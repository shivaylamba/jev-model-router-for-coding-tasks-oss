# Follow-up: Auto v2 (written and committed before any v2 execution on the 50 tasks)

## Why there is a v2

The main run (`runs/main`, `reports/main`) compared fixed Kimi K3 (A) with Auto + Jev on nconnect 0.23.0 (B). Auto passed more tasks (48 against 42) but cost about the same ($37.09 against $36.79) and was about 2.9× slower. The analysis traced this to nconnect, not to Jev's latency:

1. Jev never answered "routine", so the cheap tier almost never ran.
2. GLM 5.3, the balanced tier, reasoned uncapped (about 2,000 reasoning tokens per call), because nconnect sent it no `reasoning_effort`.
3. Claude Code's "Output token limit hit" nudge was read as a new prompt: Jev was asked again and tasks changed model halfway.
4. Permission refusals from the benchmark's own lockdown counted toward the stuck rule and escalated tasks to Kimi K3.

v2 fixes these in nconnect and changes the model lineup to the one in Abdul's Jev router experiment (DeepSeek V4 Flash with Kimi K2.6), with Kimi K3 kept as the top tier.

**This is a redesigned policy, chosen after seeing the v1 results.** v1 stays reported in full alongside it.

## What changed in nconnect (branch `feat/auto-v2`, commit `12ad392`)

Each change was measured directly before it was made (Nebius, 2026-10-15):

| Change | Evidence |
|---|---|
| GLM 5.3 gets `reasoning_effort`, floored at `low` | It ignores `none` (1,682 reasoning tokens), and `low` stops it (6) |
| Kimi K2.6 gets `chat_template_kwargs.thinking: false` at effort `none` | It ignores `reasoning_effort` at every level; the template switch turns reasoning off |
| DeepSeek V4 Flash 0731 gets `reasoning_effort`, floored at `low` | At `none` it looped for 17k and 28k output tokens in single Claude Code replies (dev run 1) |
| Claude Code's output-limit and empty-reply nudges are stripped from the prompt | They were read as new prompts; Claude Code merges them into the prompt message |
| Permission refusals no longer count toward the stuck rule | Six of v1's twelve escalations were mostly refusals |
| Decider criteria reworded: "routine" covers new code that a spec spells out | v1: Jev answered "moderate" on 42 of 50 tasks and "routine" on none |

Tests were added for each change in `packages/tests`.

## Tuning set (never the 50)

All tuning used `dev/`, which holds 15 tasks:
- nconnect's own 12 auto-routing benchmark tasks (`packages/tests/benchmarks/auto-routing/tasks` at 66bf93f);
- the 3 smoke tasks.

- Criteria wording was checked by asking Jev directly about the 15 dev prompts (old against new wording).
- `runs/dev-v2` (v2.0, stopped early) found DeepSeek's degeneration at `none`.
- `runs/dev-v2b` (v2.1) ran both A and C on all 15 dev tasks:

| Difficulty | A (passed, cost) | C (passed, cost) |
|---|---|---|
| Easy (7) | 7/7, $1.06 | 7/7, $0.10 |
| Medium (4) | 4/4, $0.93 | 4/4, $0.27 |
| Hard (4) | 4/4, $2.35 | 3/4, $7.49 |

On hard tasks, C ran Kimi K3, the same model as A. The only difference in the requests was Auto's first-turn effort raise (`medium` against `none`). The cost gap came mostly from the agent taking a longer path (one execution: 64 calls against 22).

**Decision from the dev set:** turn Auto's effort raise off (`NCONNECT_AUTO_EFFORT=off`, an existing setting). Hard tasks then run exactly like fixed Kimi K3, and Auto changes only which model runs a task.

v2.2 (the build used below) differs from the dev-tested v2.1 in one way: it strips the nudges anywhere in the prompt message, where v2.1 required them to stand alone. It reduces repeat decider calls and cannot change a first decision.

## Condition C, frozen

- `config/experiment.json` → `v2_conditions.C`.
- nconnect bundle `vendor/nconnect-0.23.0-autov2.2.js`, sha256 `1e392f7e…2390`, source commit `12ad392`.
- Environment:
  - `NCONNECT_AUTO_DECIDER=jev`
  - `NCONNECT_AUTO_DECIDER_MODEL=jev-1.13.0`
  - `NCONNECT_AUTO_FAST_MODEL=deepseek-ai/DeepSeek-V4-Flash-0731`
  - `NCONNECT_AUTO_BALANCED_MODEL=moonshotai/Kimi-K2.6`
  - `NCONNECT_AUTO_STRONG_MODEL=moonshotai/Kimi-K3`
  - `NCONNECT_AUTO_EFFORT=off`
- Everything else as in the main run: Claude Code 2.1.299, the same limits, permissions, recorder, grading and hidden tests. The dataset digest is unchanged.
- Prices: the main run's pinned catalog, copied unchanged (`--catalog-from main`), so A and C price tokens identically. The cost basis is the same as the main run's: cached input is billed at the full input rate, with a cache-free lower bound reported alongside.
- Health probes cover the models C and A can use. Amendments 1 and 2 (infrastructure and host-sleep exclusions) apply unchanged.

## Comparison and what gets reported

- **Primary:** C against A over the same 50 tasks, one execution each. A comes from `runs/main`, unchanged: same nconnect 0.23.0 bundle, Claude Code binary, catalog and settings. A and C ran on different days, so provider-side drift is possible; this is stated as a limitation.
- **Metrics:** the same ones and the same analysis code as the main run:
  - total cost and cost savings with a bootstrap interval;
  - pass rate and paired outcomes (McNemar);
  - cost per success;
  - time.
- v1 (B) is reported next to v2 (C). No task is dropped. Every execution, including any exclusion, is listed.
- Known limitation: one run per task, so hard tasks are noisy. Both conditions run Kimi K3 on them, which makes them a coin-flip on cost in either direction.

## Amendment 3: provider slowdown (2026-10-15, after 13 of 50 v2 executions)

**What happened.** During execution 12 (js-parse-ini), Nebius's Kimi K3 was badly degraded:
- calls returning about 1,200 tokens took 20–50 s, and one took 250 s;
- four calls got no response within nconnect's 45 s timeout.

The execution hit the 20-minute wall limit and failed. Fixed Kimi K3 had passed the same task in 38 s the day before. A direct probe afterwards took 7–11 s for a 140-token reply, against about 1–2 s normally. The health probe passed throughout, because it only checked that Kimi K3 answered within 30 s.

**The rule added**, written to be blind to condition:

1. **Health probe.** The probe now asks for a short reply of up to 150 tokens. A model that takes more than 6 s is unhealthy, and the runner waits, as under Amendment 1.
2. **Infrastructure failure.** A failed execution in which 3 or more model requests got no provider response is an infrastructure failure, handled exactly as in Amendment 1:
   - kept as evidence;
   - moved to `excluded.jsonl`;
   - re-run.

**Scope check.** Applied to every execution in `runs/main` (both A and B), the new failure rule matches nothing: none of their 10 failures had a single unanswered request. In `runs/v2` it matches only execution 12. The sensitivity analysis counts each excluded execution as a failed task at the cost it incurred, as before.
