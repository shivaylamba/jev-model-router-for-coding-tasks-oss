"""Turn one execution's raw logs into a normalized record.

Everything here reads files the runner saved while the task ran; nothing is
reconstructed from memory. Re-running it over a run directory reproduces every
record, which is how the tables and charts stay auditable.

Sources, per execution directory:
  claude-stream.jsonl.gz   Claude Code's stream-json output, each line wrapped
                           with the time the runner received it ({"t": ms, "line": ...})
  recorder.jsonl           one line per upstream request (Nebius and TypeSafe)
  nconnect-debug.log.gz    nconnect's debug log: Auto routes, decider answers,
                           its own per-request cost estimates
  nconnect-stderr.log      the launcher's output, including its session cost line
  grade.json               the hidden-test result
  meta.json                what the runner did and when
"""

from __future__ import annotations

import gzip
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

TIER_ORDER = {"fast": 0, "balanced": 1, "strong": 2}
FOREGROUND_KINDS = {"agent", "toolless"}
BACKGROUND_KINDS = {"background_title", "background_classifier"}
JEV_KINDS = {"jev", "jev_warmup"}
CHARS_PER_TOKEN_ESTIMATE = 4


def _lines(path: Path):
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line:
                yield line


def _json_lines(path: Path):
    for line in _lines(path):
        try:
            yield json.loads(line)
        except ValueError:
            continue


def _price(prices: dict, model: str | None) -> tuple[float, float] | None:
    entry = prices.get(model or "")
    if not entry:
        return None
    return entry["input_per_million_usd"], entry["output_per_million_usd"]


def claude_stream_metrics(path: Path, started_ms: int) -> dict:
    """What Claude Code saw: model calls, tool calls and failures, time to first output."""
    message_ids, tool_uses, tool_names = [], {}, Counter()
    tool_errors = 0
    first_text_ms = first_event_ms = first_assistant_ms = first_output_ms = None
    result = init = None
    for wrapped in _json_lines(path):
        t = wrapped.get("t")
        try:
            event = json.loads(wrapped.get("line", ""))
        except ValueError:
            continue
        if first_event_ms is None and t is not None:
            first_event_ms = t
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            init = event
        elif kind == "stream_event":
            inner = event.get("event", {})
            delta = inner.get("delta", {}) if isinstance(inner, dict) else {}
            # First model output of any kind (text, tool call or reasoning): the
            # moment a user watching the session sees the agent respond.
            if first_output_ms is None and isinstance(inner, dict) and inner.get("type") == "content_block_start":
                first_output_ms = t
            if first_text_ms is None and delta.get("type") == "text_delta" and delta.get("text", "").strip():
                first_text_ms = t
        elif kind == "assistant":
            message = event.get("message", {})
            if message.get("id") and message["id"] not in message_ids:
                message_ids.append(message["id"])
            for block in message.get("content", []) or []:
                if block.get("type") == "tool_use" and block.get("id") not in tool_uses:
                    tool_uses[block.get("id")] = block.get("name")
                    tool_names[block.get("name")] += 1
                if first_assistant_ms is None and block.get("type") == "text" and block.get("text", "").strip():
                    first_assistant_ms = t
        elif kind == "user":
            for block in event.get("message", {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("is_error"):
                    tool_errors += 1
        elif kind == "result":
            result = event

    def since(ms):
        return None if ms is None else round((ms - started_ms) / 1000, 3)

    return {
        "claude_code_version": (init or {}).get("claude_code_version"),
        "claude_session_model": (init or {}).get("model"),
        "claude_tools_available": len((init or {}).get("tools", []) or []),
        "assistant_messages": len(message_ids),
        "tool_calls": len(tool_uses),
        "tool_calls_by_name": dict(tool_names),
        "tool_errors": tool_errors,
        "ttft_visible_s": since(first_text_ms),
        "first_output_s": since(first_output_ms),
        "first_assistant_text_s": since(first_assistant_ms),
        "first_stream_event_s": since(first_event_ms),
        "result_subtype": (result or {}).get("subtype"),
        "result_is_error": (result or {}).get("is_error"),
        "num_turns": (result or {}).get("num_turns"),
        "claude_duration_ms": (result or {}).get("duration_ms"),
        "claude_api_duration_ms": (result or {}).get("duration_api_ms"),
        "claude_reported_usage": (result or {}).get("usage"),
        # Claude Code prices tokens with Anthropic's rates; meaningless for Nebius models.
        "claude_reported_cost_usd_not_applicable": (result or {}).get("total_cost_usd"),
        "has_result_event": result is not None,
    }


def recorder_metrics(path: Path, prices: dict, jev_price: float) -> dict:
    """Upstream requests as the provider saw them: models, tokens, cost, timing, failures."""
    requests = list(_json_lines(path))
    by_model = defaultdict(lambda: {"requests": 0, "prompt_tokens": 0, "completion_tokens": 0, "cached_tokens": 0,
                                    "reasoning_tokens": 0, "cost_usd": 0.0, "cost_usd_cache_free": 0.0,
                                    "requests_without_usage": 0, "estimated_cost_usd": 0.0})
    by_kind = Counter()
    cost = {"foreground": 0.0, "background": 0.0, "jev": 0.0, "unmetered_estimate": 0.0}
    cost_cache_free = {"foreground": 0.0, "background": 0.0}
    tokens = Counter()
    seen_bodies = set()
    retries = errors = aborted = missing_usage = 0
    statuses = Counter()
    unknown_price_models = set()
    agent_models = []
    jev = []
    header_ms = []
    for req in requests:
        kind = req.get("kind", "unknown")
        by_kind[kind] += 1
        statuses[str(req.get("status", "none"))] += 1
        if req.get("request_sha256") in seen_bodies and kind not in JEV_KINDS:
            retries += 1
        seen_bodies.add(req.get("request_sha256"))
        if req.get("error") == "client_aborted":
            aborted += 1
        elif req.get("error") or (req.get("status") or 0) >= 400:
            errors += 1
        if req.get("ms_headers") is not None and kind in FOREGROUND_KINDS:
            header_ms.append(req["ms_headers"])
        usage = req.get("usage") or {}
        if kind in JEV_KINDS:
            prompt = usage.get("prompt_tokens")
            estimated = prompt is None
            if estimated:
                prompt = (req.get("state_chars") or 0) // CHARS_PER_TOKEN_ESTIMATE
            jev_cost = prompt * jev_price / 1e6
            cost["jev"] += jev_cost
            tokens["jev_input_tokens"] += prompt
            jev.append({"kind": kind, "ms": req.get("ms_total"), "status": req.get("status"),
                        "error": req.get("error"), "response_model": req.get("response_model"),
                        "choice": req.get("jev_choice"), "probabilities": req.get("jev_probabilities"),
                        "input_tokens": prompt, "usage_estimated": estimated, "cost_usd": jev_cost})
            continue
        if req.get("method") != "POST" or not req.get("path", "").endswith("/chat/completions"):
            continue  # catalog fetches and the like: not billable inference
        model = req.get("response_model") or req.get("model")
        slot = by_model[model]
        slot["requests"] += 1
        group = "background" if kind in BACKGROUND_KINDS else "foreground"
        if kind in FOREGROUND_KINDS:
            agent_models.append(req.get("model"))
        rate = _price(prices, model)
        if usage.get("prompt_tokens") is None or usage.get("completion_tokens") is None:
            # No usage reported (aborted or failed stream). Never counted as free:
            # estimate from the bytes that went each way, and keep it separate.
            missing_usage += 1
            slot["requests_without_usage"] += 1
            if rate and (req.get("status") == 200 or req.get("response_bytes")):
                est = ((req.get("request_bytes") or 0) / CHARS_PER_TOKEN_ESTIMATE * rate[0]
                       + (req.get("response_bytes") or 0) / CHARS_PER_TOKEN_ESTIMATE * rate[1]) / 1e6
                slot["estimated_cost_usd"] += est
                cost["unmetered_estimate"] += est
            continue
        prompt, completion = usage["prompt_tokens"], usage["completion_tokens"]
        cached = usage.get("cached_tokens") or 0
        reasoning = usage.get("reasoning_tokens") or 0
        slot["prompt_tokens"] += prompt
        slot["completion_tokens"] += completion
        slot["cached_tokens"] += cached
        slot["reasoning_tokens"] += reasoning
        tokens[f"{group}_prompt_tokens"] += prompt
        tokens[f"{group}_completion_tokens"] += completion
        tokens[f"{group}_cached_tokens"] += cached
        tokens[f"{group}_reasoning_tokens"] += reasoning
        if rate is None:
            unknown_price_models.add(model)
            continue
        # Primary basis: cached input billed at the full input rate (Nebius
        # publishes no cached-input price). The cache-free figure is a lower bound.
        upper = (prompt * rate[0] + completion * rate[1]) / 1e6
        lower = ((prompt - cached) * rate[0] + completion * rate[1]) / 1e6
        slot["cost_usd"] += upper
        slot["cost_usd_cache_free"] += lower
        cost[group] += upper
        cost_cache_free[group] += lower
    return {
        "upstream_requests": len(requests),
        "upstream_requests_by_kind": dict(by_kind),
        "upstream_status_counts": dict(statuses),
        "upstream_retries": retries,
        "upstream_errors": errors,
        "upstream_aborted": aborted,
        "upstream_requests_without_usage": missing_usage,
        "unknown_price_models": sorted(m for m in unknown_price_models if m),
        "by_model": {k: {kk: (round(vv, 6) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                     for k, v in by_model.items()},
        "tokens": dict(tokens),
        "cost_foreground_usd": round(cost["foreground"], 6),
        "cost_background_usd": round(cost["background"], 6),
        "cost_jev_usd": round(cost["jev"], 6),
        "cost_unmetered_estimate_usd": round(cost["unmetered_estimate"], 6),
        "cost_foreground_cache_free_usd": round(cost_cache_free["foreground"], 6),
        "cost_background_cache_free_usd": round(cost_cache_free["background"], 6),
        "agent_request_models": agent_models,
        "jev_calls": jev,
        "upstream_header_ms_median": statistics.median(header_ms) if header_ms else None,
    }


DEBUG_LINE = re.compile(r"^\[nconnect proxy\] ([a-z][a-z ]+?): (\{.*\})$")


def nconnect_debug_metrics(path: Path) -> dict:
    """Auto's own account: routes, decider answers, nconnect's per-request cost estimates."""
    routes, deciders = [], []
    estimated_cost = 0.0
    stream_requests = []
    for line in _lines(path):
        match = DEBUG_LINE.match(line)
        if not match:
            continue
        label, payload = match.groups()
        try:
            data = json.loads(payload)
        except ValueError:
            continue
        if label == "auto route":
            routes.append(data)
        elif label == "auto decider":
            deciders.append(data)
        elif label == "request cost":
            estimated_cost += data.get("requestCostUsd") or 0
        elif label == "nebius stream request":
            stream_requests.append({"model": data.get("model"), "reasoning_effort": data.get("reasoningEffort")})
    agent_routes = [r for r in routes if r.get("reason") != "harness_call"]
    tiers = [r.get("tier") for r in agent_routes]
    escalations = sum(1 for a, b in zip(tiers, tiers[1:]) if TIER_ORDER.get(b, 0) > TIER_ORDER.get(a, 0))
    downshifts = sum(1 for a, b in zip(tiers, tiers[1:]) if TIER_ORDER.get(b, 0) < TIER_ORDER.get(a, 0))
    task_deciders = [d for d in deciders]
    return {
        "auto_routes": routes,
        "auto_tier_counts": dict(Counter(tiers)),
        "auto_reason_counts": dict(Counter(r.get("reason") for r in routes)),
        "auto_first_tier": tiers[0] if tiers else None,
        "auto_tiers_used": sorted(set(tiers), key=lambda t: TIER_ORDER.get(t, 9)),
        "auto_escalations": escalations,
        "auto_downshifts": downshifts,
        "auto_stuck_routes": sum(1 for r in routes if r.get("reason") == "stuck"),
        "decider_events": task_deciders,
        "decider_no_answer": sum(1 for d in task_deciders if d.get("answer") == "none"),
        "decider_late": sum(1 for d in task_deciders if d.get("late")),
        "nconnect_estimated_cost_usd": round(estimated_cost, 6),
        "reasoning_effort_counts": dict(Counter(str(r["reasoning_effort"]) for r in stream_requests)),
        "nebius_stream_requests_logged": len(stream_requests),
    }


COST_LINE = re.compile(r"\[nconnect cost\] session total: \$([0-9.]+) \(([\d,]+) in(?: incl ([\d,]+) cached)?, ([\d,]+) out\)")


def nconnect_stderr_metrics(path: Path) -> dict:
    text = path.read_text(errors="replace") if path.exists() else ""
    total = COST_LINE.search(text)
    by_model = re.search(r"\[nconnect cost\] by model: (.+)", text)
    session = re.search(r"/session/([A-Za-z0-9_-]+)", text)
    return {
        "nconnect_session_cost_usd": float(total.group(1)) if total else None,
        "nconnect_session_input_tokens": int(total.group(2).replace(",", "")) if total else None,
        "nconnect_session_cached_tokens": int((total.group(3) or "0").replace(",", "")) if total else None,
        "nconnect_session_output_tokens": int(total.group(4).replace(",", "")) if total else None,
        "nconnect_by_model_line": by_model.group(1) if by_model else None,
        "nconnect_session_id": session.group(1) if session else None,
    }


def normalize(exec_dir: Path, manifest: dict) -> dict:
    meta = json.loads((exec_dir / "meta.json").read_text())
    grade = json.loads((exec_dir / "grade.json").read_text()) if (exec_dir / "grade.json").exists() else {}
    prices = manifest["prices"]["nebius"]
    jev_price = manifest["prices"]["jev"]["input_per_million_usd"]
    stream = claude_stream_metrics(exec_dir / "claude-stream.jsonl.gz", meta["started_ms"])
    upstream = recorder_metrics(exec_dir / "recorder.jsonl", prices, jev_price)
    debug = nconnect_debug_metrics(exec_dir / "nconnect-debug.log.gz")
    stderr = nconnect_stderr_metrics(exec_dir / "nconnect-stderr.log")

    condition = meta["condition"]
    expected = manifest["conditions"][condition]
    anomalies = list(meta.get("anomalies", []))
    if condition == "A":
        wrong = sorted({m for m in upstream["agent_request_models"] if m != expected["nconnect_model"]})
        if wrong:
            anomalies.append(f"foreground requests went to {wrong}, not {expected['nconnect_model']}")
        if debug["auto_routes"]:
            anomalies.append("Auto routes logged in the fixed condition")
    else:
        pool = set(manifest["auto"]["pool_models"])
        wrong = sorted({m for m in upstream["agent_request_models"] if m not in pool})
        if wrong:
            anomalies.append(f"foreground requests went to models outside Auto's pools: {wrong}")
        if not debug["auto_routes"]:
            anomalies.append("no Auto routes logged in the Auto condition")
        task_decisions = [j for j in upstream["jev_calls"] if j["kind"] == "jev"]
        if expected.get("env", {}).get("NCONNECT_AUTO_DECIDER") == "jev" and not task_decisions:
            anomalies.append("no Jev decision for the task prompt")
    if meta.get("fallback_diagnostics"):
        anomalies.append(f"{meta['fallback_diagnostics']} model-fallback diagnostics recorded")

    total = (upstream["cost_foreground_usd"] + upstream["cost_background_usd"] + upstream["cost_jev_usd"]
             + upstream["cost_unmetered_estimate_usd"])
    jev_task = [j for j in upstream["jev_calls"] if j["kind"] == "jev"]
    return {
        "run_id": meta["run_id"],
        "seq": meta["seq"],
        "repetition": meta["repetition"],
        "task_id": meta["task_id"],
        "category": meta["category"],
        "difficulty": meta["difficulty"],
        "language": meta["language"],
        "condition": condition,
        "condition_label": expected["label"],
        "pair_position": meta["pair_position"],
        "started_at": meta["started_at"],
        "ended_at": meta["ended_at"],
        "duration_s": meta["duration_s"],
        "termination": meta["termination"],
        "exit_code": meta["exit_code"],
        "passed": bool(grade.get("passed")),
        "tests_total": grade.get("tests_total"),
        "tests_failed": grade.get("tests_failed"),
        "grade_timed_out": grade.get("timed_out"),
        **stream,
        **{k: v for k, v in upstream.items() if k != "agent_request_models"},
        "foreground_models": sorted(set(upstream["agent_request_models"]) - {None}),
        **debug,
        **stderr,
        "jev_decision_ms": jev_task[0]["ms"] if jev_task else None,
        "jev_decision_choice": jev_task[0]["choice"] if jev_task else None,
        "jev_model_version": jev_task[0]["response_model"] if jev_task else None,
        "cost_total_usd": round(total, 6),
        "cost_basis": "estimated: provider-reported tokens x prices snapshotted in the manifest; "
                      "cached input at the full input rate (no published cached price)",
        "contamination_flags": meta.get("contamination_flags", []),
        "anomalies": anomalies,
        "versions": meta.get("versions", {}),
    }
