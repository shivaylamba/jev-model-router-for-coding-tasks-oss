#!/usr/bin/env python3
"""Analyse a run: side-by-side tables, paired statistics, per-task rows, charts.

    vendor/analysis-venv/bin/python bench/analyze.py --run-id main

Every number comes from runs/<id>/executions/*/ (re-normalized from the raw logs
unless --use-results is given), so each table and chart traces back to raw files.
Outputs go to reports/<id>/.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_task  # noqa: E402
from normalize import normalize  # noqa: E402

DIFFICULTIES = ["easy", "medium", "hard"]
BOOTSTRAP = 10_000
RNG_SEED = 20261014
FIXED, AUTO = "A", "B"
MODEL_SHORT = {
    "moonshotai/Kimi-K3": "Kimi K3",
    "zai-org/GLM-5.3-Flash": "GLM 5.3 Flash",
    "zai-org/GLM-5.3": "GLM 5.3",
    "moonshotai/Kimi-K2.6": "Kimi K2.6",
    "deepseek-ai/DeepSeek-V4.1-Flash": "DeepSeek V4.1 Flash",
}


# ---------------------------------------------------------------- loading

def load_records(run_dir: Path, use_results: bool) -> tuple[dict, list[dict]]:
    manifest = json.loads((run_dir / "manifest.json").read_text())
    if use_results:
        records = [json.loads(l) for l in (run_dir / "results.jsonl").read_text().splitlines() if l.strip()]
    else:
        records = [normalize(d, manifest) for d in sorted((run_dir / "executions").iterdir())
                   if (d / "DONE").exists()]
    return manifest, records


# ---------------------------------------------------------------- statistics

def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value on discordant pairs b (fixed only) and c (Auto only)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def bootstrap(pairs: list, stat, n: int = BOOTSTRAP) -> tuple[float, float] | None:
    """95% percentile interval of stat() over pairs resampled with replacement (tasks are the unit)."""
    if len(pairs) < 2:
        return None
    rng = random.Random(RNG_SEED)
    values = []
    for _ in range(n):
        sample = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        value = stat(sample)
        if value is not None and not math.isnan(value):
            values.append(value)
    if not values:
        return None
    values.sort()
    return values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]


def safe_div(a: float, b: float) -> float | None:
    return None if not b else a / b


# ---------------------------------------------------------------- aggregation

def condition_summary(rows: list[dict]) -> dict:
    n = len(rows)
    passed = sum(r["passed"] for r in rows)
    cost = sum(r["cost_total_usd"] for r in rows)
    durations = [r["duration_s"] for r in rows]
    tokens_in = sum(r["tokens"].get("foreground_prompt_tokens", 0) + r["tokens"].get("background_prompt_tokens", 0)
                    for r in rows)
    tokens_out = sum(r["tokens"].get("foreground_completion_tokens", 0)
                     + r["tokens"].get("background_completion_tokens", 0) for r in rows)
    cached = sum(r["tokens"].get("foreground_cached_tokens", 0) + r["tokens"].get("background_cached_tokens", 0)
                 for r in rows)
    reasoning = sum(r["tokens"].get("foreground_reasoning_tokens", 0) for r in rows)
    lo, hi = wilson(passed, n)
    hours = sum(durations) / 3600
    ttfo = [r["first_output_s"] for r in rows if r.get("first_output_s") is not None]
    return {
        "attempted": n,
        "passed": passed,
        "success_rate": safe_div(passed, n),
        "success_rate_ci95": [lo, hi],
        "cost_total_usd": cost,
        "cost_foreground_usd": sum(r["cost_foreground_usd"] for r in rows),
        "cost_background_usd": sum(r["cost_background_usd"] for r in rows),
        "cost_jev_usd": sum(r["cost_jev_usd"] for r in rows),
        "cost_unmetered_estimate_usd": sum(r["cost_unmetered_estimate_usd"] for r in rows),
        "cost_total_cache_free_lower_bound_usd": sum(r["cost_foreground_cache_free_usd"] + r["cost_background_cache_free_usd"]
                                                    + r["cost_jev_usd"] + r["cost_unmetered_estimate_usd"] for r in rows),
        "cost_failed_tasks_usd": sum(r["cost_total_usd"] for r in rows if not r["passed"]),
        "cost_per_attempt_usd": safe_div(cost, n),
        "cost_per_success_usd": safe_div(cost, passed),
        "successes_per_dollar": safe_div(passed, cost),
        "successes_per_hour_sequential": safe_div(passed, hours),
        "duration_total_s": sum(durations),
        "duration_median_s": statistics.median(durations) if durations else None,
        "duration_p95_s": percentile(durations, 0.95),
        "first_output_median_s": statistics.median(ttfo) if ttfo else None,
        "first_output_p95_s": percentile(ttfo, 0.95),
        "input_tokens": tokens_in,
        "cached_input_tokens": cached,
        "cached_share_of_input": safe_div(cached, tokens_in),
        "output_tokens": tokens_out,
        "reasoning_tokens_reported": reasoning,
        "tokens_per_task": safe_div(tokens_in + tokens_out, n),
        "tokens_per_success": safe_div(tokens_in + tokens_out, passed),
        "upstream_requests": sum(r["upstream_requests"] for r in rows),
        "model_requests_per_task": safe_div(sum(r["assistant_messages"] for r in rows), n),
        "tool_calls_per_task": safe_div(sum(r["tool_calls"] for r in rows), n),
        "tool_errors": sum(r["tool_errors"] for r in rows),
        "upstream_retries": sum(r["upstream_retries"] for r in rows),
        "upstream_errors": sum(r["upstream_errors"] for r in rows),
        "requests_without_usage": sum(r["upstream_requests_without_usage"] for r in rows),
        "terminations": dict(Counter(r["termination"] for r in rows)),
        "escalations": sum(r.get("auto_escalations", 0) for r in rows),
        "stuck_routes": sum(r.get("auto_stuck_routes", 0) for r in rows),
        "anomalies": sum(len(r["anomalies"]) for r in rows),
        "contamination_flags": sum(len(r["contamination_flags"]) for r in rows),
    }


def model_shares(rows: list[dict]) -> dict:
    by = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost_usd": 0.0})
    for r in rows:
        for model, slot in r["by_model"].items():
            by[model]["requests"] += slot["requests"]
            by[model]["tokens"] += slot["prompt_tokens"] + slot["completion_tokens"]
            by[model]["cost_usd"] += slot["cost_usd"] + slot.get("estimated_cost_usd", 0)
    totals = {k: sum(v[k] for v in by.values()) for k in ("requests", "tokens", "cost_usd")}
    return {model: {**v, **{f"{k}_share": safe_div(v[k], totals[k]) for k in totals}} for model, v in by.items()}


def pairs_of(records: list[dict]) -> list[tuple[dict, dict]]:
    index = defaultdict(dict)
    for r in records:
        index[(r["repetition"], r["task_id"])][r["condition"]] = r
    return [(v[FIXED], v[AUTO]) for k, v in sorted(index.items()) if FIXED in v and AUTO in v]


def paired_summary(pairs: list[tuple[dict, dict]]) -> dict:
    if not pairs:
        return {}
    both = sum(a["passed"] and b["passed"] for a, b in pairs)
    fixed_only = sum(a["passed"] and not b["passed"] for a, b in pairs)
    auto_only = sum(b["passed"] and not a["passed"] for a, b in pairs)
    neither = sum(not a["passed"] and not b["passed"] for a, b in pairs)
    n = len(pairs)

    def savings(sample):
        fixed = sum(a["cost_total_usd"] for a, _ in sample)
        auto = sum(b["cost_total_usd"] for _, b in sample)
        return None if not fixed else 100 * (fixed - auto) / fixed

    def quality(sample):
        return 100 * (sum(b["passed"] for _, b in sample) - sum(a["passed"] for a, _ in sample)) / len(sample)

    fixed_cost = sum(a["cost_total_usd"] for a, _ in pairs)
    auto_cost = sum(b["cost_total_usd"] for _, b in pairs)
    fixed_time = sum(a["duration_s"] for a, _ in pairs)
    auto_time = sum(b["duration_s"] for _, b in pairs)
    both_pass = [(a, b) for a, b in pairs if a["passed"] and b["passed"]]
    log_ratios = [math.log(a["duration_s"] / b["duration_s"]) for a, b in both_pass
                  if a["duration_s"] > 0 and b["duration_s"] > 0]

    def geo(sample):
        vals = [math.log(a["duration_s"] / b["duration_s"]) for a, b in sample if a["duration_s"] > 0 and b["duration_s"] > 0]
        return math.exp(statistics.mean(vals)) if vals else None

    return {
        "pairs": n,
        "both_pass": both, "fixed_only_pass": fixed_only, "auto_only_pass": auto_only, "both_fail": neither,
        "mcnemar_exact_p": mcnemar_exact(fixed_only, auto_only),
        "quality_difference_pp": quality(pairs),
        "quality_difference_pp_ci95": bootstrap(pairs, quality),
        "fixed_cost_usd": fixed_cost, "auto_cost_usd": auto_cost,
        "dollar_savings_usd": fixed_cost - auto_cost,
        "cost_savings_pct": savings(pairs),
        "cost_savings_pct_ci95": bootstrap(pairs, savings),
        "cost_reduction_factor": safe_div(fixed_cost, auto_cost),
        "auto_cheaper_tasks": sum(b["cost_total_usd"] < a["cost_total_usd"] for a, b in pairs),
        "fixed_total_duration_s": fixed_time, "auto_total_duration_s": auto_time,
        "speedup_total_time": safe_div(fixed_time, auto_time),
        "speedup_median_time": safe_div(statistics.median([a["duration_s"] for a, _ in pairs]),
                                        statistics.median([b["duration_s"] for _, b in pairs])),
        "both_pass_pairs": len(both_pass),
        "speedup_geomean_both_pass": math.exp(statistics.mean(log_ratios)) if log_ratios else None,
        "speedup_geomean_both_pass_ci95": bootstrap(both_pass, geo),
        "auto_faster_tasks_both_pass": sum(b["duration_s"] < a["duration_s"] for a, b in both_pass),
    }


def auto_routing(rows: list[dict]) -> dict:
    first = defaultdict(Counter)
    jev_ms = [r["jev_decision_ms"] for r in rows if r.get("jev_decision_ms") is not None]
    decider = [d for r in rows for d in r.get("decider_events", [])]
    for r in rows:
        first[r["difficulty"]][r.get("auto_first_tier") or "none"] += 1
    return {
        "first_tier_by_difficulty": {d: dict(first[d]) for d in DIFFICULTIES if d in first},
        "jev_choice_by_difficulty": {d: dict(Counter(r.get("jev_decision_choice") or "none" for r in rows
                                                     if r["difficulty"] == d)) for d in DIFFICULTIES},
        "tier_request_counts": dict(sum((Counter(r.get("auto_tier_counts") or {}) for r in rows), Counter())),
        "reason_counts": dict(sum((Counter(r.get("auto_reason_counts") or {}) for r in rows), Counter())),
        "tasks_with_escalation": sum(1 for r in rows if r.get("auto_escalations")),
        "tasks_with_downshift": sum(1 for r in rows if r.get("auto_downshifts")),
        "tasks_with_repeat_jev_decisions": sum(1 for r in rows if (r.get("jev_task_decisions") or 0) > 1),
        "tasks_with_output_limit_resumes": sum(1 for r in rows if r.get("output_limit_resumes")),
        "tasks_reaching_strong": sum(1 for r in rows if "strong" in (r.get("auto_tiers_used") or [])),
        "jev_calls": sum(len(r["jev_calls"]) for r in rows),
        "jev_cost_usd": sum(r["cost_jev_usd"] for r in rows),
        "jev_decision_ms_median": statistics.median(jev_ms) if jev_ms else None,
        "jev_decision_ms_p95": percentile(jev_ms, 0.95),
        "decider_no_answer": sum(1 for d in decider if d.get("answer") == "none"),
        "decider_late": sum(1 for d in decider if d.get("late")),
        "decider_events": len(decider),
        "jev_model_versions": dict(Counter(r.get("jev_model_version") or "none" for r in rows)),
        "effort_counts": dict(sum((Counter(r.get("reasoning_effort_counts") or {}) for r in rows), Counter())),
    }


# ---------------------------------------------------------------- formatting

def money(v):
    return "n/a" if v is None else (f"${v:,.4f}" if abs(v) < 1 else f"${v:,.2f}")


def pct(v, digits=1):
    return "n/a" if v is None else f"{100 * v:.{digits}f}%"


def secs(v):
    return "n/a" if v is None else (f"{v:.0f} s" if v >= 10 else f"{v:.1f} s")


def ci(pair, fmt):
    return "" if not pair else f" (95% CI {fmt(pair[0])} to {fmt(pair[1])})"


def models_label(r: dict) -> str:
    models = sorted(r["by_model"], key=lambda m: -r["by_model"][m]["requests"])
    return " + ".join(f"{MODEL_SHORT.get(m, m)}×{r['by_model'][m]['requests']}" for m in models) or "none"


def tiers_label(r: dict) -> str:
    counts = r.get("auto_tier_counts") or {}
    return " → ".join(t for t in ("fast", "balanced", "strong") if t in counts) if counts else "-"


def notable(a: dict, b: dict) -> str:
    notes = []
    if a["passed"] != b["passed"]:
        notes.append("only fixed passed" if a["passed"] else "only Auto passed")
    if b.get("auto_escalations"):
        notes.append(f"Auto escalated {b['auto_escalations']}×")
    if b.get("auto_stuck_routes"):
        notes.append("stuck → strong")
    if b.get("decider_no_answer"):
        notes.append("Jev gave no answer (keyword rules used)")
    if b.get("decider_late"):
        notes.append("Jev answer arrived late")
    for r, name in ((a, "fixed"), (b, "Auto")):
        if r["termination"] != "completed":
            notes.append(f"{name} hit {r['termination']}")
        if r["anomalies"]:
            notes.append(f"{name} anomaly: {'; '.join(r['anomalies'])}")
    if b["cost_total_usd"] > a["cost_total_usd"]:
        notes.append("Auto cost more")
    if a["passed"] and b["passed"] and b["assistant_messages"] > 1.5 * a["assistant_messages"]:
        notes.append(f"Auto took {b['assistant_messages']} model calls vs {a['assistant_messages']}")
    return "; ".join(notes)


def per_task_rows(pairs) -> list[dict]:
    rows = []
    for a, b in pairs:
        save = None if not a["cost_total_usd"] else 100 * (a["cost_total_usd"] - b["cost_total_usd"]) / a["cost_total_usd"]
        rows.append({
            "task_id": a["task_id"], "repetition": a["repetition"], "difficulty": a["difficulty"],
            "category": a["category"], "language": a["language"],
            "fixed_models": models_label(a), "auto_models": models_label(b), "auto_tiers": tiers_label(b),
            "auto_first_tier": b.get("auto_first_tier"), "jev_choice": b.get("jev_decision_choice"),
            "fixed_pass": a["passed"], "auto_pass": b["passed"],
            "fixed_cost_usd": round(a["cost_total_usd"], 6), "auto_cost_usd": round(b["cost_total_usd"], 6),
            "savings_pct": None if save is None else round(save, 1),
            "fixed_time_s": a["duration_s"], "auto_time_s": b["duration_s"],
            "fixed_model_calls": a["assistant_messages"], "auto_model_calls": b["assistant_messages"],
            "notable": notable(a, b),
            "fixed_execution": f"{a['seq']:03d}", "auto_execution": f"{b['seq']:03d}",
        })
    return rows


# ---------------------------------------------------------------- charts

def charts(out: Path, summary: dict, records: list[dict], pairs) -> list[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return ["charts skipped: matplotlib unavailable (use vendor/analysis-venv/bin/python)"]
    out.mkdir(parents=True, exist_ok=True)
    colors = {FIXED: "#2a78d6", AUTO: "#eb6834"}
    labels = {FIXED: "Fixed Kimi K3", AUTO: "Auto + Jev"}
    model_colors = {"Kimi K3": "#2a78d6", "GLM 5.3 Flash": "#1baf7a", "GLM 5.3": "#eda100", "Kimi K2.6": "#e87ba4",
                    "DeepSeek V4.1 Flash": "#6250d6"}
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#8a8984", "axes.labelcolor": "#0b0b0b", "xtick.color": "#52514e",
                         "ytick.color": "#52514e", "axes.grid": True, "grid.color": "#e7e6e2", "grid.linewidth": 0.8,
                         "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "legend.frameon": False,
                         "axes.axisbelow": True})
    by = summary["by_difficulty"]
    x = range(len(DIFFICULTIES))
    width = 0.38
    made = []

    def save(fig, name):
        for ext in ("png", "svg"):
            fig.savefig(out / f"{name}.{ext}", dpi=180, bbox_inches="tight")
        plt.close(fig)
        made.append(name)

    # 1. Cost by difficulty, including failed attempts.
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, cond in enumerate((FIXED, AUTO)):
        vals = [by.get(d, {}).get(cond, {}).get("cost_total_usd", 0) for d in DIFFICULTIES]
        bars = ax.bar([p + (i - 0.5) * width for p in x], vals, width - 0.02, color=colors[cond], label=labels[cond])
        for bar, v in zip(bars, vals):
            ax.annotate(f"${v:.2f}", (bar.get_x() + bar.get_width() / 2, v), ha="center", va="bottom", fontsize=8,
                        color="#52514e", xytext=(0, 2), textcoords="offset points")
    ax.set_xticks(list(x), [f"{d}\n({by.get(d, {}).get(FIXED, {}).get('attempted', 0)} tasks)" for d in DIFFICULTIES])
    ax.set_ylabel("Estimated cost, USD (all attempts)")
    ax.set_title("Total cost by task difficulty", loc="left", fontsize=11)
    ax.legend()
    ax.grid(axis="x", visible=False)
    save(fig, "cost-by-difficulty")

    # 2. Success rate by difficulty with Wilson intervals.
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, cond in enumerate((FIXED, AUTO)):
        rates, errs_lo, errs_hi, notes = [], [], [], []
        for d in DIFFICULTIES:
            s = by.get(d, {}).get(cond, {})
            rate = s.get("success_rate") or 0
            lo, hi = s.get("success_rate_ci95", [rate, rate])
            rates.append(100 * rate)
            errs_lo.append(100 * (rate - lo))
            errs_hi.append(100 * (hi - rate))
            notes.append(f"{s.get('passed', 0)}/{s.get('attempted', 0)}")
        pos = [p + (i - 0.5) * width for p in x]
        ax.bar(pos, rates, width - 0.02, color=colors[cond], label=labels[cond])
        ax.errorbar(pos, rates, yerr=[errs_lo, errs_hi], fmt="none", ecolor="#52514e", elinewidth=1, capsize=3)
    counts = []
    for d in DIFFICULTIES:
        parts = [f"{by.get(d, {}).get(c, {}).get('passed', 0)}/{by.get(d, {}).get(c, {}).get('attempted', 0)}"
                 for c in (FIXED, AUTO)]
        counts.append(f"{d}\nfixed {parts[0]} · Auto {parts[1]}")
    ax.set_xticks(list(x), counts)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Tasks passed (%)")
    ax.set_title("Success rate by difficulty (95% Wilson intervals)", loc="left", fontsize=11)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncols=2)
    ax.grid(axis="x", visible=False)
    save(fig, "success-by-difficulty")

    # 3. Completion latency: every task as a dot, by difficulty and condition.
    fig, ax = plt.subplots(figsize=(7, 4))
    rng = random.Random(1)
    for i, cond in enumerate((FIXED, AUTO)):
        for j, d in enumerate(DIFFICULTIES):
            vals = [r["duration_s"] for r in records if r["condition"] == cond and r["difficulty"] == d]
            passed = [r["passed"] for r in records if r["condition"] == cond and r["difficulty"] == d]
            centre = j + (i - 0.5) * width
            xs = [centre + rng.uniform(-0.12, 0.12) for _ in vals]
            ax.scatter([x_ for x_, ok in zip(xs, passed) if ok], [v for v, ok in zip(vals, passed) if ok], s=22,
                       color=colors[cond], edgecolor="#fcfcfb", linewidth=1, zorder=3,
                       label=labels[cond] if j == 0 else None)
            ax.scatter([x_ for x_, ok in zip(xs, passed) if not ok], [v for v, ok in zip(vals, passed) if not ok],
                       s=26, facecolor="none", edgecolor=colors[cond], linewidth=1.4, zorder=3,
                       label=f"{labels[cond]} (failed)" if j == 0 else None)
            if vals:
                med = statistics.median(vals)
                ax.hlines(med, centre - 0.16, centre + 0.16, color="#0b0b0b", linewidth=2, zorder=4)
    ax.set_xticks(list(x), DIFFICULTIES)
    ax.set_yscale("log")
    from matplotlib.ticker import FuncFormatter
    plain = FuncFormatter(lambda v, _: f"{v:g}")
    ax.yaxis.set_major_formatter(plain)
    ax.yaxis.set_minor_formatter(plain)
    ax.tick_params(axis="y", which="minor", labelsize=8)
    ax.set_ylabel("Task completion time, s (log scale)")
    ax.set_title("Completion time per task (bar = median, hollow = failed)", loc="left", fontsize=11)
    ax.legend(fontsize=8, ncols=2)
    ax.grid(axis="x", visible=False)
    save(fig, "latency-by-difficulty")

    # 4. Auto's model mix: share of requests, tokens and spend.
    shares = summary["model_shares"].get(AUTO, {})
    if shares:
        order = [m for m in MODEL_SHORT if m in shares] + [m for m in shares if m not in MODEL_SHORT]
        fig, ax = plt.subplots(figsize=(7, 3.2))
        metrics = [("requests_share", "Requests"), ("tokens_share", "Tokens"), ("cost_usd_share", "Spend")]
        for k, (key, label) in enumerate(metrics):
            left = 0.0
            for model in order:
                share = shares[model].get(key) or 0
                name = MODEL_SHORT.get(model, model)
                ax.barh(k, 100 * share, left=left, height=0.6, color=model_colors.get(name, "#8a8984"),
                        edgecolor="#fcfcfb", linewidth=2, label=name if k == 0 else None)
                if share >= 0.07:
                    ax.text(left + 50 * share, k, f"{100 * share:.0f}%", ha="center", va="center", fontsize=8,
                            color="#0b0b0b")
                left += 100 * share
        ax.set_yticks(range(len(metrics)), [m[1] for m in metrics])
        ax.set_xlim(0, 100)
        ax.set_xlabel("Share within the Auto condition (%)")
        ax.set_title("Where Auto sent the work", loc="left", fontsize=11)
        ax.legend(ncols=3, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.28))
        ax.grid(axis="y", visible=False)
        save(fig, "auto-model-distribution")

    # 5. Paired cost per task.
    if pairs:
        fig, ax = plt.subplots(figsize=(5.2, 5))
        style = {(True, True): ("#0b0b0b", "both passed"), (True, False): ("#2a78d6", "only fixed passed"),
                 (False, True): ("#eb6834", "only Auto passed"), (False, False): ("#8a8984", "both failed")}
        seen = set()
        for a, b in pairs:
            key = (a["passed"], b["passed"])
            col, lab = style[key]
            ax.scatter(a["cost_total_usd"], b["cost_total_usd"], s=24, color=col, edgecolor="#fcfcfb", linewidth=1,
                       zorder=3, label=None if key in seen else lab)
            seen.add(key)
        lo = min(min(a["cost_total_usd"], b["cost_total_usd"]) for a, b in pairs if a["cost_total_usd"] > 0) / 1.5
        hi = max(max(a["cost_total_usd"], b["cost_total_usd"]) for a, b in pairs) * 1.5
        ax.plot([lo, hi], [lo, hi], color="#8a8984", linewidth=1, linestyle="--", zorder=1)
        ax.text(hi / 1.6, hi / 1.25, "same cost", color="#52514e", fontsize=8, ha="right")
        ax.set_xscale("log")
        ax.set_yscale("log")
        from matplotlib.ticker import FuncFormatter
        dollars = FuncFormatter(lambda v, _: f"${v:g}")
        ax.xaxis.set_major_formatter(dollars)
        ax.yaxis.set_major_formatter(dollars)
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_xlabel("Fixed Kimi K3 cost per task, USD")
        ax.set_ylabel("Auto + Jev cost per task, USD")
        ax.set_title("Cost per task, paired (below the line = Auto cheaper)", loc="left", fontsize=11)
        ax.legend(fontsize=8)
        save(fig, "paired-cost")
    return made


# ---------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--use-results", action="store_true", help="read results.jsonl instead of re-normalizing")
    parser.add_argument("--auto-condition", default="B", help="the routed condition to compare with A (B_rules for pipeline checks)")
    args = parser.parse_args()
    global AUTO
    AUTO = args.auto_condition
    run_dir = ROOT / "runs" / args.run_id
    out = ROOT / "reports" / args.run_id
    out.mkdir(parents=True, exist_ok=True)
    manifest, records = load_records(run_dir, args.use_results)
    conditions = sorted({r["condition"] for r in records})
    pairs = pairs_of(records)

    summary = {
        "run_id": args.run_id,
        "executions": len(records),
        "conditions": {c: manifest["conditions"][c]["label"] for c in conditions},
        "overall": {c: condition_summary([r for r in records if r["condition"] == c]) for c in conditions},
        "by_difficulty": {d: {c: condition_summary([r for r in records if r["condition"] == c and r["difficulty"] == d])
                              for c in conditions} for d in DIFFICULTIES if any(r["difficulty"] == d for r in records)},
        "by_category": {cat: {c: condition_summary([r for r in records if r["condition"] == c and r["category"] == cat])
                              for c in conditions} for cat in sorted({r["category"] for r in records})},
        "paired": paired_summary(pairs),
        "paired_by_difficulty": {d: paired_summary([(a, b) for a, b in pairs if a["difficulty"] == d])
                                 for d in DIFFICULTIES},
        "model_shares": {c: model_shares([r for r in records if r["condition"] == c]) for c in conditions},
        "auto_routing": auto_routing([r for r in records if r["condition"] == AUTO]) if AUTO in conditions else {},
        "spend_by_difficulty": {c: {d: sum(r["cost_total_usd"] for r in records if r["condition"] == c and r["difficulty"] == d)
                                    for d in DIFFICULTIES} for c in conditions},
        "formulas": {
            "cost_savings_pct": "100 × (fixed cost − Auto cost) / fixed cost, summed over paired tasks",
            "cost_reduction_factor": "fixed cost / Auto cost",
            "quality_difference_pp": "Auto success rate − fixed success rate, in percentage points, over paired tasks",
            "speedup_total_time": "sum of fixed durations / sum of Auto durations, all paired tasks",
            "speedup_geomean_both_pass": "geometric mean over tasks both conditions passed of fixed duration / Auto duration",
            "confidence_intervals": f"95% percentile bootstrap over tasks ({BOOTSTRAP} resamples, seed {RNG_SEED}); "
                                    "success-rate intervals are Wilson",
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    with (out / "results.jsonl").open("w") as handle:
        for r in records:
            handle.write(json.dumps(r) + "\n")
    flat_keys = ["seq", "repetition", "task_id", "category", "difficulty", "language", "condition", "pair_position",
                 "started_at", "ended_at", "duration_s", "first_output_s", "ttft_visible_s", "termination", "passed",
                 "tests_total", "tests_failed", "assistant_messages", "tool_calls", "tool_errors", "upstream_requests",
                 "upstream_retries", "upstream_errors", "upstream_requests_without_usage", "cost_foreground_usd",
                 "cost_background_usd", "cost_jev_usd", "cost_unmetered_estimate_usd", "cost_total_usd",
                 "cost_foreground_cache_free_usd", "nconnect_session_cost_usd", "auto_first_tier", "auto_escalations",
                 "auto_stuck_routes", "jev_decision_choice", "jev_decision_ms", "jev_model_version", "decider_no_answer",
                 "decider_late"]
    with (out / "results.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(flat_keys + ["foreground_models", "auto_tier_counts", "tokens", "anomalies"])
        for r in records:
            writer.writerow([r.get(k) for k in flat_keys] + [";".join(r["foreground_models"]),
                                                             json.dumps(r.get("auto_tier_counts") or {}),
                                                             json.dumps(r["tokens"]), "; ".join(r["anomalies"])])
    task_rows = per_task_rows(pairs)
    if task_rows:
        with (out / "per-task.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(task_rows[0].keys()))
            writer.writeheader()
            writer.writerows(task_rows)
    made = charts(out / "charts", summary, records, pairs)
    print(json.dumps({"executions": len(records), "pairs": len(pairs), "charts": made,
                      "overall": {c: {k: summary["overall"][c][k] for k in ("passed", "attempted", "cost_total_usd")}
                                  for c in conditions},
                      "paired": {k: summary["paired"].get(k) for k in ("cost_savings_pct", "quality_difference_pp",
                                                                        "speedup_total_time")}}, indent=1, default=str))


if __name__ == "__main__":
    main()
