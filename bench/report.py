#!/usr/bin/env python3
"""Write reports/<id>/report.md from summary.json, per-task.csv and the raw records.

    vendor/analysis-venv/bin/python bench/report.py --run-id main

Every table is generated; nothing is typed in by hand. Scenario lists include
every task that meets each rule (no hand-picked examples), with the rule stated.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT  # noqa: E402

FIXED, AUTO = "A", "B"
AUTO_LABELS = {"B": "Auto + Jev", "C": "Auto v2 + Jev"}


def money(v):
    if v is None:
        return "n/a"
    return f"${v:,.4f}" if abs(v) < 1 else f"${v:,.2f}"


def pct(v, digits=1):
    return "n/a" if v is None else f"{100 * v:.{digits}f}%"


def num(v, digits=0):
    return "n/a" if v is None else f"{v:,.{digits}f}"


def secs(v):
    if v is None:
        return "n/a"
    return f"{v / 60:.1f} min" if v >= 120 else (f"{v:.0f} s" if v >= 10 else f"{v:.1f} s")


def ratio(v):
    return "n/a" if v is None else f"{v:.2f}×"


def ci(pair, fmt):
    return "" if not pair else f" [{fmt(pair[0])}, {fmt(pair[1])}]"


def limits(s: dict) -> str:
    stopped = {k: v for k, v in (s.get("terminations") or {}).items() if k != "completed"}
    return ", ".join(f"{k}: {v}" for k, v in stopped.items()) or "none"


def outages(summary: dict) -> str:
    failures = summary.get("infrastructure_failures") or []
    if not failures:
        return "No execution met the infrastructure-failure rule."
    out = ["Executions excluded as provider outages (Amendment 1) or host sleep (Amendment 2), and re-run. Evidence is kept:", "",
           "| Task | Condition | Execution | Cost | Duration | Reason | Evidence |", "|---|---|---|---|---|---|---|"]
    for f in failures:
        out.append(f"| {f['task_id']} | {f['condition']} | {f['seq']:03d} | {money(f['cost_usd'])} | {secs(f['duration_s'])} | "
                   f"{f['reason']} | `{f['kept_at']}` |")
    s = summary.get("paired_counting_outages_as_failures") or {}
    if s:
        out += ["", f"Sensitivity, using each excluded attempt as the result instead of its re-run: quality difference "
                f"{s['quality_difference_pp']:+.1f} pp, cost savings {s['cost_savings_pct']:.1f}%, speedup by total time "
                f"{ratio(s['speedup_total_time'])}."]
    return "\n".join(out)


def scorecard(summary: dict) -> str:
    a, b = summary["overall"].get(FIXED, {}), summary["overall"].get(AUTO, {})
    rows = [
        ("Tasks passed", f"{a.get('passed')}/{a.get('attempted')}", f"{b.get('passed')}/{b.get('attempted')}"),
        ("Success rate (95% CI)", pct(a.get("success_rate")) + ci(a.get("success_rate_ci95"), pct),
         pct(b.get("success_rate")) + ci(b.get("success_rate_ci95"), pct)),
        ("Total execution cost, estimated (incl. failed tasks)", money(a.get("cost_total_usd")), money(b.get("cost_total_usd"))),
        ("  of which foreground inference", money(a.get("cost_foreground_usd")), money(b.get("cost_foreground_usd"))),
        ("  of which background calls", money(a.get("cost_background_usd")), money(b.get("cost_background_usd"))),
        ("  of which Jev routing", money(a.get("cost_jev_usd")), money(b.get("cost_jev_usd"))),
        ("  of which unmetered (estimated from bytes)", money(a.get("cost_unmetered_estimate_usd")), money(b.get("cost_unmetered_estimate_usd"))),
        ("  spent on failed tasks", money(a.get("cost_failed_tasks_usd")), money(b.get("cost_failed_tasks_usd"))),
        ("Lower bound if cached input were free", money(a.get("cost_total_cache_free_lower_bound_usd")), money(b.get("cost_total_cache_free_lower_bound_usd"))),
        ("Average cost per attempted task", money(a.get("cost_per_attempt_usd")), money(b.get("cost_per_attempt_usd"))),
        ("Cost per successful task", money(a.get("cost_per_success_usd")), money(b.get("cost_per_success_usd"))),
        ("Successful tasks per dollar", num(a.get("successes_per_dollar"), 1), num(b.get("successes_per_dollar"), 1)),
        ("Successful tasks per hour (one at a time)", num(a.get("successes_per_hour_sequential"), 1), num(b.get("successes_per_hour_sequential"), 1)),
        ("Median completion time", secs(a.get("duration_median_s")), secs(b.get("duration_median_s"))),
        ("p95 completion time", secs(a.get("duration_p95_s")), secs(b.get("duration_p95_s"))),
        ("Median time to first output", secs(a.get("first_output_median_s")), secs(b.get("first_output_median_s"))),
        ("Total wall time", secs(a.get("duration_total_s")), secs(b.get("duration_total_s"))),
        ("Input tokens (cached share)", f"{num(a.get('input_tokens'))} ({pct(a.get('cached_share_of_input'), 0)})",
         f"{num(b.get('input_tokens'))} ({pct(b.get('cached_share_of_input'), 0)})"),
        ("Output tokens (reasoning reported)", f"{num(a.get('output_tokens'))} ({num(a.get('reasoning_tokens_reported'))})",
         f"{num(b.get('output_tokens'))} ({num(b.get('reasoning_tokens_reported'))})"),
        ("Tokens per task / per success", f"{num(a.get('tokens_per_task'))} / {num(a.get('tokens_per_success'))}",
         f"{num(b.get('tokens_per_task'))} / {num(b.get('tokens_per_success'))}"),
        ("Model requests per task", num(a.get("model_requests_per_task"), 1), num(b.get("model_requests_per_task"), 1)),
        ("Tool calls per task", num(a.get("tool_calls_per_task"), 1), num(b.get("tool_calls_per_task"), 1)),
        ("Failed tool calls", num(a.get("tool_errors")), num(b.get("tool_errors"))),
        ("Upstream retries / errors / without usage", f"{a.get('upstream_retries')} / {a.get('upstream_errors')} / {a.get('requests_without_usage')}",
         f"{b.get('upstream_retries')} / {b.get('upstream_errors')} / {b.get('requests_without_usage')}"),
        ("Sessions stopped by a limit", limits(a), limits(b)),
        ("Auto escalations (tasks with stuck → strong)", "n/a", f"{b.get('escalations')} ({b.get('stuck_routes')} stuck routes)"),
        ("Anomalies / contamination flags", f"{a.get('anomalies')} / {a.get('contamination_flags')}", f"{b.get('anomalies')} / {b.get('contamination_flags')}"),
    ]
    out = [f"| Metric | A: fixed Kimi K3 | {AUTO}: {AUTO_LABELS.get(AUTO, 'Auto + Jev')} |", "|---|---|---|"]
    out += [f"| {m} | {x} | {y} |" for m, x, y in rows]
    return "\n".join(out)


def headline(summary: dict) -> str:
    p = summary.get("paired") or {}
    if not p:
        return "_No paired tasks yet._"
    lines = [
        f"- Paired tasks: **{p['pairs']}**.",
        f"- Quality: Auto minus fixed = **{p['quality_difference_pp']:+.1f} percentage points**"
        + ci(p.get("quality_difference_pp_ci95"), lambda v: f"{v:+.1f}") + " (bootstrap 95% CI). "
        f"Exact McNemar p = {p['mcnemar_exact_p']:.3f} on {p['fixed_only_pass'] + p['auto_only_pass']} discordant pairs.",
        f"- Cost: fixed {money(p['fixed_cost_usd'])}, Auto {money(p['auto_cost_usd'])}. "
        f"Savings **{p['cost_savings_pct']:.1f}%**" + ci(p.get("cost_savings_pct_ci95"), lambda v: f"{v:.1f}%")
        + f", i.e. a cost-reduction factor of **{ratio(p['cost_reduction_factor'])}** ({money(p['dollar_savings_usd'])} saved). "
        f"Auto was cheaper on {p['auto_cheaper_tasks']} of {p['pairs']} tasks.",
        f"- Time: total fixed {secs(p['fixed_total_duration_s'])}, Auto {secs(p['auto_total_duration_s'])}; "
        f"speedup by total time **{ratio(p['speedup_total_time'])}**, by median {ratio(p['speedup_median_time'])}, "
        f"geometric mean over the {p['both_pass_pairs']} tasks both passed {ratio(p['speedup_geomean_both_pass'])}"
        + ci(p.get("speedup_geomean_both_pass_ci95"), lambda v: f"{v:.2f}×")
        + f". Auto was faster on {p['auto_faster_tasks_both_pass']} of those {p['both_pass_pairs']}.",
        "- Speedup above 1× means Auto finished faster; below 1× means slower.",
    ]
    return "\n".join(lines)


def breakdown(summary: dict, key: str, title: str) -> str:
    groups = summary[key]
    out = [f"| {title} | Tasks | Passed A / B | Cost A / B | Savings | Cost per success A / B | Median time A / B |",
           "|---|---|---|---|---|---|---|"]
    for name, by in groups.items():
        a, b = by.get(FIXED, {}), by.get(AUTO, {})
        save = None if not a.get("cost_total_usd") else 100 * (a["cost_total_usd"] - b.get("cost_total_usd", 0)) / a["cost_total_usd"]
        out.append(f"| {name} | {a.get('attempted', 0)} | {a.get('passed', 0)} / {b.get('passed', 0)} | "
                   f"{money(a.get('cost_total_usd'))} / {money(b.get('cost_total_usd'))} | "
                   f"{'n/a' if save is None else f'{save:.0f}%'} | {money(a.get('cost_per_success_usd'))} / {money(b.get('cost_per_success_usd'))} | "
                   f"{secs(a.get('duration_median_s'))} / {secs(b.get('duration_median_s'))} |")
    return "\n".join(out)


def paired_table(summary: dict) -> str:
    rows = [("all", summary.get("paired") or {})] + [(d, s) for d, s in summary.get("paired_by_difficulty", {}).items() if s]
    out = ["| Tasks | Both pass | Only fixed passes | Only Auto passes | Both fail | McNemar p |", "|---|---|---|---|---|---|"]
    for name, p in rows:
        if p:
            out.append(f"| {name} | {p['both_pass']} | {p['fixed_only_pass']} | {p['auto_only_pass']} | {p['both_fail']} | {p['mcnemar_exact_p']:.3f} |")
    return "\n".join(out)


def routing_section(summary: dict) -> str:
    r = summary.get("auto_routing") or {}
    if not r:
        return "_No Auto executions._"
    out = ["First tier Auto chose for each task, by the evaluator's difficulty label (a diagnostic, not a quality measure):", "",
           "| Difficulty | fast | balanced | strong | none |", "|---|---|---|---|---|"]
    for d, counts in r["first_tier_by_difficulty"].items():
        out.append(f"| {d} | {counts.get('fast', 0)} | {counts.get('balanced', 0)} | {counts.get('strong', 0)} | {counts.get('none', 0)} |")
    out += ["", "Jev's own choice on the task prompt:", "", "| Difficulty | routine | moderate | hard | none |", "|---|---|---|---|---|"]
    for d, counts in r["jev_choice_by_difficulty"].items():
        if counts:
            out.append(f"| {d} | {counts.get('routine', 0)} | {counts.get('moderate', 0)} | {counts.get('hard', 0)} | {counts.get('none', 0)} |")
    out += ["",
            f"- Model requests by tier: {json.dumps(r['tier_request_counts'])}; by reason: {json.dumps(r['reason_counts'])}.",
            f"- Tasks that escalated: {r['tasks_with_escalation']}; tasks that reached the strong tier at some point: {r['tasks_reaching_strong']}.",
            f"- Tasks that moved down a tier mid-task: {r.get('tasks_with_downshift')}; tasks where Jev was asked more than once: "
            f"{r.get('tasks_with_repeat_jev_decisions')}; tasks where Claude Code resumed after hitting the output-token limit: "
            f"{r.get('tasks_with_output_limit_resumes')}. (nconnect treats Claude Code's \"Output token limit hit\" message as a new "
            "prompt, asks Jev about it, and re-routes the rest of the task.)",
            f"- Jev calls: {r['jev_calls']} (task decisions plus one warm-up per session), cost {money(r['jev_cost_usd'])}; "
            f"decision latency median {num(r['jev_decision_ms_median'])} ms, p95 {num(r['jev_decision_ms_p95'])} ms.",
            f"- Jev gave no answer (keyword rules used instead): {r['decider_no_answer']} of {r['decider_events']} decider events; "
            f"answers that arrived after the 2.5 s wait: {r['decider_late']}.",
            f"- Jev versions that answered: {json.dumps(r['jev_model_versions'])}.",
            f"- Reasoning effort sent upstream (all requests): {json.dumps(r['effort_counts'])}."]
    return "\n".join(out)


def model_mix(summary: dict) -> str:
    out = ["| Condition | Model | Requests (share) | Tokens (share) | Spend (share) |", "|---|---|---|---|---|"]
    for cond, shares in summary["model_shares"].items():
        for model, s in sorted(shares.items(), key=lambda kv: -kv[1]["cost_usd"]):
            out.append(f"| {cond} | {model} | {s['requests']:,} ({pct(s['requests_share'], 0)}) | "
                       f"{s['tokens']:,} ({pct(s['tokens_share'], 0)}) | {money(s['cost_usd'])} ({pct(s['cost_usd_share'], 0)}) |")
    return "\n".join(out)


def per_task_md(rows: list[dict]) -> str:
    out = ["| Task | Difficulty | Fixed model(s) | Auto model(s) / tiers | Fixed | Auto | Fixed cost | Auto cost | Savings | Fixed time | Auto time | Notable |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['task_id']} | {r['difficulty']} | {r['fixed_models']} | {r['auto_models']} ({r['auto_tiers']}) | "
                   f"{'pass' if r['fixed_pass'] == 'True' else 'FAIL'} | {'pass' if r['auto_pass'] == 'True' else 'FAIL'} | "
                   f"{money(float(r['fixed_cost_usd']))} | {money(float(r['auto_cost_usd']))} | "
                   f"{r['savings_pct'] + '%' if r['savings_pct'] else 'n/a'} | {secs(float(r['fixed_time_s']))} | "
                   f"{secs(float(r['auto_time_s']))} | {r['notable']} |")
    return "\n".join(out)


def scenarios(rows: list[dict]) -> str:
    def f(r, k):
        return float(r[k])
    passed = lambda r, k: r[k] == "True"  # noqa: E731
    rules = [
        ("Routine work where routing saved money with a correct result",
         "Auto's first tier was fast, both conditions passed, Auto cost less. Sorted by savings.",
         sorted([r for r in rows if r["auto_first_tier"] == "fast" and passed(r, "fixed_pass") and passed(r, "auto_pass")
                 and f(r, "auto_cost_usd") < f(r, "fixed_cost_usd")], key=lambda r: -float(r["savings_pct"] or 0))),
        ("Routing saved money with a correct result (any tier)",
         "Both conditions passed and Auto cost less. Sorted by savings.",
         sorted([r for r in rows if passed(r, "fixed_pass") and passed(r, "auto_pass")
                 and f(r, "auto_cost_usd") < f(r, "fixed_cost_usd")], key=lambda r: -float(r["savings_pct"] or 0))),
        ("Work where Auto chose or escalated to the strong model",
         "Auto's first tier was strong, or it escalated during the task.",
         [r for r in rows if r["auto_first_tier"] == "strong" or "escalated" in r["notable"]]),
        ("Routing hurt quality", "Fixed passed and Auto failed.",
         [r for r in rows if passed(r, "fixed_pass") and not passed(r, "auto_pass")]),
        ("Routing helped quality", "Auto passed and fixed failed.",
         [r for r in rows if passed(r, "auto_pass") and not passed(r, "fixed_pass")]),
        ("Routing increased completion time", "Both passed and Auto took at least 1.5× as long.",
         [r for r in rows if passed(r, "fixed_pass") and passed(r, "auto_pass") and f(r, "auto_time_s") >= 1.5 * f(r, "fixed_time_s")]),
        ("The fixed model was the better choice on cost too", "Both passed and Auto cost more than fixed Kimi K3.",
         [r for r in rows if passed(r, "fixed_pass") and passed(r, "auto_pass") and f(r, "auto_cost_usd") > f(r, "fixed_cost_usd")]),
        ("Cheaper per token, not cheaper per task",
         "Auto made at least 1.5× as many model calls as fixed (longer sessions on cheaper models).",
         [r for r in rows if int(r["auto_model_calls"]) >= 1.5 * max(1, int(r["fixed_model_calls"]))]),
    ]
    out = []
    for title, rule, matches in rules:
        out += [f"### {title}", "", f"Rule: {rule} Matches: {len(matches)}.", ""]
        if matches:
            out += ["| Task | Difficulty | Auto tiers | Fixed / Auto | Cost fixed / Auto | Time fixed / Auto | Calls fixed / Auto | Executions |",
                    "|---|---|---|---|---|---|---|---|"]
            for r in matches:
                out.append(f"| {r['task_id']} | {r['difficulty']} | {r['auto_tiers']} | "
                           f"{'pass' if passed(r, 'fixed_pass') else 'FAIL'} / {'pass' if passed(r, 'auto_pass') else 'FAIL'} | "
                           f"{money(f(r, 'fixed_cost_usd'))} / {money(f(r, 'auto_cost_usd'))} | "
                           f"{secs(f(r, 'fixed_time_s'))} / {secs(f(r, 'auto_time_s'))} | "
                           f"{r['fixed_model_calls']} / {r['auto_model_calls']} | {r['fixed_execution']}, {r['auto_execution']} |")
        out.append("")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--auto-condition", default="B")
    parser.add_argument("--out", default="", help="report directory under reports/ (default: the run id)")
    parser.add_argument("--fixed-from", default="", help="the run condition A came from, for the header")
    args = parser.parse_args()
    global AUTO
    AUTO = args.auto_condition
    rep = ROOT / "reports" / (args.out or args.run_id)
    run_dir = ROOT / "runs" / args.run_id
    summary = json.loads((rep / "summary.json").read_text())
    manifest = json.loads((run_dir / "manifest.json").read_text())
    rows = list(csv.DictReader((rep / "per-task.csv").open())) if (rep / "per-task.csv").exists() else []
    events = [json.loads(l) for l in (run_dir / "events.jsonl").read_text().splitlines() if l.strip()]
    v = manifest["versions"]
    text = f"""# Results: {args.run_id}

Generated from `runs/{args.run_id}/` by `bench/analyze.py` and `bench/report.py`. Every number below can be traced to
`results.jsonl` and the raw files of the execution named in the per-task table.

- Condition A taken from: `runs/{args.fixed_from or args.run_id}/`; condition {AUTO} from `runs/{args.run_id}/`.
- Executions: {summary['executions']} (task executions; each makes many model API requests, counted separately below).
- {v['nconnect_version']} (bundle `{v['nconnect_bundle_sha256'][:12]}…`, source `{v['nconnect_source_commit'][:7]}`), {v['claude_code']}, Node {v['node']}, {v['python']}.
{"".join(f"- Condition {c} runs its own nconnect build: `{b['path']}` (sha256 `{b['sha256'][:12]}…`, source `{b['source_commit'][:7]}`).{chr(10)}" for c, b in (v.get('condition_bundles') or {}).items())}- Prices: Nebius catalog captured {manifest['prices']['captured_at']}; Jev {manifest['prices']['jev']['model']} at ${manifest['prices']['jev']['input_per_million_usd']}/M input tokens.
- Costs are **estimates** from provider-reported tokens and those prices, not reconciled against Nebius billing. Cached input
  is charged at the full input rate (Nebius publishes no cached price); the cache-free lower bound is shown alongside.
- Run events: {"; ".join(e['event'] for e in events)}.

## Headline (paired tasks)

{headline(summary)}

## Excluded executions (Amendments 1 and 2)

{outages(summary)}

## Scorecard

{scorecard(summary)}

## Paired outcomes

{paired_table(summary)}

## By difficulty

{breakdown(summary, "by_difficulty", "Difficulty")}

## By category

{breakdown(summary, "by_category", "Category")}

## Where the work and the money went

{model_mix(summary)}

## Auto's routing

{routing_section(summary)}

## Scenarios

Each list includes every task that meets its rule.

{scenarios(rows)}

## Per task

{per_task_md(rows)}

## Charts

![Cost by difficulty](charts/cost-by-difficulty.png)
![Success by difficulty](charts/success-by-difficulty.png)
![Completion time](charts/latency-by-difficulty.png)
![Auto model distribution](charts/auto-model-distribution.png)
![Paired cost](charts/paired-cost.png)
"""
    (rep / "report.md").write_text(text)
    print(f"wrote {rep / 'report.md'}")


if __name__ == "__main__":
    main()
