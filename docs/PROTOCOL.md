# Protocol

Written and frozen before any benchmark result was collected. The machine-readable
version is `config/experiment.json`; each run's `manifest.json` records the
exact values used, with hashes of the dataset, evaluator, protocol and binaries.

**Research question.** Across these 50 tasks, how much money and time did
Jev-assisted Auto save, and what happened to correctness?

This compares two complete execution policies. It does not isolate model
selection from reasoning effort: Auto also changes the reasoning effort it
requests (see "Effort" below).

## 1. What was verified, and how

All checks were made on 14 October 2026 against the installed software and the
nconnect source at the matching commit.

| Item | Finding | How it was checked |
|---|---|---|
| nconnect | v0.23.0. The installed bundle `~/.nconnect/bin/nconnect.js` (sha256 `db122e27…`) is byte-identical to `https://nconnect.sh/nconnect.js`, which Vercel builds from `main` at `66bf93f` (PR #32 merge). The runner uses a pinned copy in `vendor/`. | `shasum` of both files; `git rev-parse origin/main`. |
| Claude Code | 2.1.299 (the `claude` on PATH). A copy is pinned in `vendor/`. Headless flags used: `-p`, `--output-format stream-json`, `--verbose`, `--include-partial-messages`, `--permission-mode acceptEdits`, `--allowedTools`, `--disallowedTools`, `--strict-mcp-config`. There is no turn-limit flag in this version, so the runner enforces the request limit itself. | `claude --help`. |
| Runtimes | Node 24.18.1 (TypeScript runs through built-in type stripping), Python 3.11.5, Bun 1.4.2. Node and Python are pinned through `vendor/bin`. | `--version`. |
| Model IDs and prices | Kimi K3 `moonshotai/Kimi-K3` $3.00 in / $15.00 out per million tokens; GLM 5.3 Flash `zai-org/GLM-5.3-Flash` $0.15 / $0.50; GLM 5.3 `zai-org/GLM-5.3` $1.40 / $4.40; Kimi K2.6 `moonshotai/Kimi-K2.6` $0.95 / $4.00. Nebius publishes no cached-input price (`input_cache_read: null`). | `GET /v1/models?verbose=true` and the public `models_info` endpoint, both snapshotted in `config/pricing/`. |
| Jev | `jev-latest` resolves to `jev-1.13.0`; $0.042 per million input tokens, output free. The run pins `jev-1.13.0` through `NCONNECT_AUTO_DECIDER_MODEL` so the alias cannot move mid-experiment. | TypeSafe docs page, snapshotted in `config/pricing/`. |
| Command for B | `NCONNECT_AUTO_DECIDER=jev nconnect --model auto claude` is correct for 0.23.0: `--model` belongs to nconnect and must come before `claude`. | Source (`bin/nconnect.ts`, `harnesses/claude.ts`) and the smoke test. |
| Where routing settings are read | By the launcher, from its environment, and carried with the session to the daemon. The decider's answers are cached inside the daemon process, keyed by prompt. So every task gets a fresh daemon and an empty nconnect home, and nothing carries over between tasks. | `daemon/launch.ts`, `auto-decider.ts`. |
| How Jev picks a tier | Jev is asked once per typed prompt to choose routine, moderate or hard (three criteria). Its probabilities become one difficulty score, `(0.5·p(moderate) + p(hard)) / total`. At the default medium cost preference, a score of at least 0.7 goes to the strong tier, at least 0.3 to balanced, and anything lower to fast. The tool-calling turns of the task reuse the answer. | `auto-decider.ts`, `auto-routing.ts`. |
| How escalation works | Three or more failed tool calls in a task (Claude Code's `is_error` tool results) route it to the strong tier, reason `stuck`. Plan mode, an effort level above Claude Code's default, or a "think hard" phrase also force strong. No task prompt contains such a phrase (the validator rejects them). Per-turn downshifting is off. | `auto-routing.ts`. |
| Decider failure | Jev is given 2.5 s per turn. A slower answer is used from the next turn (logged `late`). No answer within 20 s, or an error, falls back to nconnect's keyword rules for that task (logged `answer: none`). | `auto-decider.ts`. |
| Observability | With `NCONNECT_DEBUG=1`, nconnect logs every Auto route (tier, reason, model), every decider answer (score, latency, late, error), and its own per-request cost estimate. | `claude/proxy.ts`, `auto-decider.ts`. |
| Background calls | nconnect sends Claude Code's session-title and permission-classifier calls to `NCONNECT_BACKGROUND_MODEL` (default GLM 5.3 Flash) in both conditions. In headless `-p` mode Claude Code 2.1.299 made neither call in the smoke test. Any that occur are costed separately. | `claude/request-routing.ts`; smoke test. |
| Cross-model fallback | On by default (a dead endpoint is retried on Kimi K2.6). Disabled in both conditions with `NCONNECT_FALLBACK_MODEL=off`; any fallback diagnostic is logged as an anomaly. | `nebius-client.ts`. |
| Effort | In A, nconnect sends `reasoning_effort: none` to Kimi K3 on every request. Claude Code's own effort setting is not passed through. In B: GLM 5.3 Flash (fast) always gets `low`, its floor. GLM 5.3 (balanced) is not on nconnect's list of models that accept the parameter, so it gets none and reasons by its own default. Kimi K3 (strong) gets `medium` on the task's first turn, or `high` when Jev's score is at least 0.9, and `none` after that. | `claude/translate-request.ts`, `models/src/index.ts`; smoke-test logs. |
| Billing records | Token Factory shows spend only in the console's Usage tab, filterable by project; there is no usage API. Costs here are estimates from provider-reported tokens. | Nebius docs, snapshotted in `config/pricing/`. |

## 2. Conditions

| | A: router off | B: router on |
|---|---|---|
| Launch | `nconnect --model moonshotai/Kimi-K3 claude -p <prompt> …` | `nconnect --model auto claude -p <prompt> …` |
| Routing | none | `NCONNECT_AUTO_DECIDER=jev`, `NCONNECT_AUTO_DECIDER_MODEL=jev-1.13.0` |
| Auto settings | n/a | defaults: pools fast GLM 5.3 Flash then DeepSeek V4.1 Flash, balanced GLM 5.3 then Kimi K2.6, strong Kimi K3; cost tier medium; per-turn off; effort on |
| Common | `NCONNECT_FALLBACK_MODEL=off`, `NCONNECT_DISABLE_AUTOUPDATE=1`, `NCONNECT_DEBUG=1`, `DISABLE_AUTOUPDATER=1` | same |
| Claude Code | same binary, flags, tools and permissions; subagents, WebFetch and WebSearch disabled | same |

Both conditions run Claude Code against Nebius Token Factory. Claude Code is the
harness, not a third baseline.

Subagents are disabled in both conditions because Claude Code runs them on its
Haiku-tier model, which would break "Kimi K3 for every foreground request" in A.

## 3. Isolation

Every task execution gets all of the following:

- A new temporary directory holding a copy of the task's starting workspace, committed to a fresh git repository.
- A new `HOME`, a new `CLAUDE_CONFIG_DIR` (no memory, no CLAUDE.md, no skills, no MCP servers) and a new nconnect home seeded with the frozen catalog.
- A new nconnect daemon, so the decider cache is empty.
- A new recorder.
- An environment built from nothing, so no `NCONNECT_*`, `CLAUDE_*` or `ANTHROPIC_*` setting leaks in from the operator's shell.

The hidden tests and reference solutions live in the benchmark project. Agents
never get that path. Every tool call is scanned afterwards for references to it,
and a reference is flagged.

## 4. Measurement

- **Claude Code's stream** (`claude-stream.jsonl.gz`): each line stamped on arrival. Gives model calls as Claude Code saw them, tool calls by name, failed tool calls, time to first output and to first text, and Claude Code's own duration figures.
- **Recorder** (`recorder.jsonl`): a passthrough between the nconnect daemon and Nebius and TypeSafe, reached through settings nconnect already supports (`NEBIUS_BASE_URL`, `NCONNECT_AUTO_DECIDER_URL`). One line per upstream request, with:
  - start time, time to headers and to first byte, total time;
  - requested and answering model, the kind of call, reasoning effort;
  - provider-reported usage (prompt, completion, cached and reasoning tokens);
  - status, errors and aborts;
  - for Jev, its choice and probabilities.

  It never records headers, prompts or completions.

  This is the only added instrumentation, and it applies identically to both conditions. The smoke test reconciled its cost against nconnect's own session total to the cent.
- **nconnect debug log**: Auto routes, decider answers and nconnect's own cost estimate per request.
- **nconnect's session line** on exit: its cost and token totals, kept for cross-checking.
- **Workspace**: the final diff and a tarball, and the hidden-test output.

Reasoning tokens are a subset of completion tokens and are never added to them.
Cached tokens are a subset of prompt tokens.

## 5. Scoring (fixed before results)

- **Success**: every hidden acceptance test passes on the final workspace. Nothing else counts.
- **Cost (estimated)**: provider-reported tokens times the manifest's prices.
  - Cached input is billed at the full input rate, because no cached price is published. A cache-free lower bound is reported alongside.
  - Requests without reported usage are estimated from bytes and kept separate.
  - Jev is charged per input token.
  - Failed tasks count in every total.
  - Nothing is reconciled against billing unless stated.
- **Time**: wall time from launching nconnect to its exit. Time to first output is the first content block in Claude Code's stream. A fast failure is never a speed win; paired speed comparisons use only tasks both conditions passed.
- **Quality difference**: Auto success rate minus fixed success rate, in percentage points.
- **Savings**: `100 × (fixed − Auto) / fixed`.
- **Reduction factor**: `fixed / Auto`.
- **Speedup**: three measures are reported.
  - Total fixed time over total Auto time.
  - The ratio of medians.
  - The geometric mean of per-task ratios on tasks both conditions passed.
- **Uncertainty**:
  - Wilson intervals for success rates.
  - Exact McNemar for paired pass/fail.
  - 95% bootstrap intervals over tasks (10,000 resamples, seed 20261014) for savings and the quality difference.
- Router agreement with the evaluator's difficulty labels is a diagnostic only.

## 6. Limits and caps

- Per task: 1,200 s of wall time and 80 model requests, the same for every task and both conditions. A per-task cost cap of $8 exists only to stop a runaway session.
- Per run: a spending cap (default $45) and a runtime cap (default 10 h), both settable on the command line. The runner stops at a cap and keeps everything recorded so far.
- One execution at a time.

## 7. Order and repetitions

- **Task order:** shuffled with seed 20261014.
- **Condition order:** within each task the two conditions run back to back, and which goes first is balanced 25/25 and seeded.
- **Resuming:** a resumed run skips finished executions and keeps any interrupted attempt under `attempts/` instead of overwriting it.
- **Repetitions:** more come from `prepare --repetitions N`. One pass is preliminary evidence.

## 8. Smoke test

Three excluded tasks (`smoke/`) validated execution, grading, telemetry and cost
accounting before the benchmark. A pipeline-only condition (`B_rules`, Auto with
keyword rules) tested Auto's telemetry while the Jev key was unavailable; it is
never part of the benchmark.

## Amendments

### Amendment 1: provider outages (2026-10-14, 17:25 UTC, after 8 of 100 executions)

**What happened.** During execution 8 (`ts-todo-query`, condition B), Nebius stopped responding for `zai-org/GLM-5.3`, the balanced-tier model:

- 22 of 23 requests got no response headers within nconnect's 45 s limit.
- The session ran into the 20-minute wall limit.
- A direct probe a minute later also got no answer within 60 s, while Kimi K3 and GLM 5.3 Flash answered in about 1 s.
- Cross-model fallback is off by design, so the task never reached a model.

That measures the outage, not the routing policy.

**The rule added**, applied identically to both conditions and blind to which condition the execution belonged to:

1. Before every execution, the runner sends one tiny request to each of Kimi K3, GLM 5.3 and GLM 5.3 Flash. If any fails to answer within 30 s, it waits 5 minutes and tries again. The probes are not charged to any task, and every wait is logged in `events.jsonl`.
2. An execution is an **infrastructure failure** when it failed and the provider answered none of its last three model requests. Such an execution is:
   - kept as evidence in `attempts/<name>.infra-N`;
   - moved from `results.jsonl` to `excluded.jsonl`, with the reason;
   - re-run once the endpoints are healthy, up to twice.
3. The report lists every infrastructure failure. A sensitivity analysis counts each excluded execution as a failed task at the cost it incurred.

Nothing about the tasks, prompts, scoring, tier mappings or the conditions themselves changed. At the time, results stood at A 2 of 4 passed and B 3 of 3 passed.

### Amendment 2: host sleep (2026-10-15, after 95 of 100 executions)

**What happened.** Between 20:08 and 21:48 UTC the Mac running the benchmark entered macOS maintenance sleep repeatedly, including one 61-minute sleep. Seven executions overlapped a sleep:

- Their durations include time the machine was asleep.
- Execution 95 hit the wall limit only because its clock jumped.

**The rule added**, applied identically to both conditions:

1. An execution that overlaps a sleep interval in the macOS power log (`pmset -g log`) is a host failure.
2. It is handled exactly like an Amendment 1 infrastructure failure: kept in `attempts/`, moved to `excluded.jsonl`, and re-run.
3. The intervals used are saved in `runs/main/host-sleep-intervals.json`.

From this point the runner is kept awake with `caffeinate -i -s` for its lifetime.
