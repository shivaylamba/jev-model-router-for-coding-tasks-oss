# Evidence pack: fixed Kimi K3 vs Jev-assisted Auto, through Claude Code and nconnect

**Research question.** Across these 50 tasks, how much money and time did Jev-assisted Auto save, and what happened to correctness?

**Status.** One paired pass (50 tasks × 2 conditions = 100 task executions), run on 14–15 October 2026. This is preliminary evidence from a single pass, not a settled result.

All figures come from `runs/main/` through `bench/analyze.py`. The full generated tables are in [`report.md`](report.md) and the raw per-execution rows in [`results.jsonl`](results.jsonl) and [`results.csv`](results.csv).

## The answer

**Money: Auto saved nothing overall.**
- Total estimated execution cost was $36.79 for fixed Kimi K3 and $37.09 for Auto: −0.8% savings, a cost-reduction factor of 0.99×.
- The 95% bootstrap interval runs from 37% more expensive to 29% cheaper.
- Auto was cheaper on 28 of 50 tasks and more expensive on 22.

**Time: Auto was much slower.**
- 135.6 min against 27.8 min of total wall time (0.20× "speedup").
- On the 40 tasks both conditions passed, Auto took about 2.9× as long per task (geometric mean 0.35×, interval 0.27× to 0.44×).
- Auto was faster on only 3 of those 40.

**Correctness: Auto passed more tasks, but this pass can't show the gap is real.**
- 48 of 50 (96%) against 42 of 50 (84%): +12 percentage points, bootstrap interval +0 to +24.
- Auto alone passed 8 tasks and fixed Kimi K3 alone passed 2, with 40 passed by both and none failed by both. Exact McNemar test: p = 0.11.

The savings Auto did produce were offset by spending more on the tasks Jev judged hard:

| Jev's first decision | Tasks | Passed: both / only fixed / only Auto | Cost fixed → Auto | Time (both passed) |
|---|---|---|---|---|
| moderate → GLM 5.3 first | 42 (20 easy, 18 medium, 4 hard) | 37 / 1 / 4 | $27.76 → $21.89 (**21% cheaper**) | Auto ~3.2× slower |
| hard → Kimi K3 (the fixed condition's own model) | 8 (6 hard, 2 medium) | 3 / 1 / 4 | $9.03 → $15.19 (**68% more**) | about the same |
| routine → GLM 5.3 Flash first | **0** | n/a | n/a | n/a |

Two things follow from this table:

- **The "hard" tasks:** Auto used the same model as the baseline, so model selection can't explain their better pass rate. What differed there was Auto's first-turn reasoning effort (`medium` or `high`, against `none` in the fixed condition), the number of calls, and run-to-run variation.
- **The cheapest tier:** Jev never chose "routine" for any task, so no task started on GLM 5.3 Flash, the model 20× cheaper than Kimi K3.

## Scorecard

| | A: fixed Kimi K3 | B: Auto + Jev |
|---|---|---|
| Tasks passed | 42 / 50 (84%, CI 71–92%) | 48 / 50 (96%, CI 87–99%) |
| Total execution cost, estimated (all attempts) | $36.79 | $37.09 |
| …of which Jev | n/a | $0.0026 (115 calls) |
| …of which background calls | $0.00 (none made) | $0.00 (none made) |
| …spent on failed tasks | $9.51 | $1.42 |
| Lower bound if cached input were free | $5.64 | $8.35 |
| Average cost per attempted task | $0.74 | $0.74 |
| Cost per successful task | $0.88 | $0.77 |
| Successful tasks per dollar | 1.14 | 1.29 |
| Successful tasks per hour (one task at a time) | 90.7 | 21.2 |
| Median / p95 completion time | 25 s / 84 s | 62 s / 598 s |
| Median time to first output | 1.9 s | 2.6 s |
| Input tokens (share served from cache) | 10.9 M (95%) | 15.7 M (91%) |
| Output tokens (of which reported reasoning) | 0.27 M (0) | 1.14 M (0.84 M) |
| Model calls / tool calls per task | 13.4 / 15.3 | 15.8 / 18.1 |
| Failed tool calls | 146 | 135 |
| Sessions stopped by a limit | 0 | 1 (wall limit; it still passed) |

**Cost per success.** Auto's is lower only because it failed fewer tasks: fixed Kimi K3 spent $9.51 on its 8 failures.

**Cache sensitivity.** About 95% of Kimi K3's input tokens were cache hits. Nebius publishes no cached-input price, so the primary basis charges them at the full rate, as nconnect itself does.
- If Nebius discounts cache hits, every figure here shrinks, and the comparison flips against Auto: $5.64 against $8.35 in the free-cache extreme, about 48% more for Auto.
- The reason is that Auto's sessions ran longer, on models with a lower cache share.
- The **Nebius console's bill for this run** settles which side of that range is real. See the reconciliation section below.

## Why Auto behaved this way (mechanisms, with evidence)

1. **Jev rated every precise task prompt "moderate" or "hard", never "routine".**
   - nconnect asks Jev a three-way question, with "routine" defined as "small, well specified, low risk; one obvious change, a lookup, a rename" (`auto-decider.ts`).
   - These prompts are written like issues that state every interface and edge case, and Jev scored even the easy ones "moderate". `py-chunk-evenly` got p(moderate) = 0.92.
   - So the 20× cheaper fast tier was never the starting point. Its 73 requests (9% of Auto's) all came from mechanism 3.
2. **GLM 5.3, the balanced tier, reasons at length, and nconnect cannot cap it.**
   - GLM 5.3 is not on nconnect's list of models that accept `reasoning_effort` (`models/src/index.ts`).
   - It produced 0.84 M reasoning tokens, against zero from Kimi K3 at `reasoning_effort: none`.
   - Its 416 calls took 92 min of model time against 25 min for all 668 fixed-condition calls. The provider was not the cause: GLM 5.3's median time to first byte was 1.0 s.
   - This is the main reason Auto was slower.
3. **Claude Code's "Output token limit hit" message re-routes the task.**
   - When a long GLM 5.3 reply hits the output cap, Claude Code adds a user message: "Output token limit hit. Resume directly…".
   - nconnect reads it as a newly typed prompt, asks Jev about that sentence, gets "routine", and moves the rest of the task to GLM 5.3 Flash.
   - This happened in 10 tasks. It saved money on some (`ts-semver-range`: $0.44 against $1.61) and probably cost one task (`py-cron-next`, below).
4. **Three failed tool calls mark a task as stuck and move it to Kimi K3.**
   - Twelve Auto tasks escalated this way and then paid for both models.
   - In 6 of the 12, at least two of the three failures that triggered it were **permission denials** caused by the benchmark's locked-down tool policy: a Bash command outside the allow-list, or a compound command. These are not real failures.
   - The policy was identical in both conditions, but only Auto reacts to failed tool calls, so this inflated Auto's escalations and cost.
   - Users who approve commands interactively would see fewer.
5. **On Jev's "hard" tasks, Auto ran the same model as the baseline with more effort and more calls.** Those 8 tasks cost 68% more under Auto. Their 4-to-1 pass advantage did not come from model selection.

## Representative traces

Each trace was chosen by the rule shown, not picked by hand. Every execution's raw files are in `runs/main/executions/<NNN>-r1-<task>-<A|B>/`:

- `claude-stream.jsonl.gz`
- `recorder.jsonl`
- `nconnect-debug.log.gz`
- `workspace.diff`
- `grade-output.txt`

**1. Routing saved money with a correct result.** Rule: the median-saving task among the 24 where both conditions passed and Auto cost less. `ts-format-money` (easy):
- Jev answered moderate (p = 0.89) in 468 ms, and all 10 calls went to GLM 5.3.
- Both passed 7/7 tests: Auto $0.185 in 24 s, fixed $0.332 in 17 s, so 44% cheaper.
- The largest saving was `py-chunk-evenly`: $0.10 against $0.52 (80%), both passing. Executions 091/092 and 052/051.

**2. Routing to a cheaper model saved money on harder work.** Rule: the largest absolute saving. `ts-signup-validate` (medium):
- Fixed Kimi K3 took 45 calls and $3.89, with 11 failed tool calls.
- Auto took 14 GLM 5.3 calls and $0.84 (−78%), but 291 s against 115 s.
- Both passed 15/15. Executions 014/013.

**3. Hard work where Auto chose the strong model.** Rule: Jev said "hard" and only Auto passed, the most expensive such case. `py-async-rate-limiter` (hard):
- Jev answered hard (p = 0.61), and all 63 calls went to Kimi K3. It ran $7.07 and 20 min, hit the wall limit, and its final workspace passed 16/16.
- Fixed Kimi K3 spent $2.74 in 74 s, but its implementation hung the hidden tests.
- Both used the same model, so this is not a model-selection win. Executions 028/027.

**4. Routing hurt quality.** Rule: every task fixed passed and Auto failed (2 tasks).
- `py-cron-next` (hard):
  - Jev answered moderate (p = 0.75), so the task started on GLM 5.3, which spent 84k reasoning tokens over 7 calls.
  - Three "Output token limit hit" resumes followed. Jev called those sentences routine, and the last 13 calls ran on GLM 5.3 Flash.
  - It failed 19/20 after 11 min. Fixed Kimi K3 passed 20/20 in 29 s for $0.44. Executions 073/074.
- `ts-schema-validator` (hard): both ran on Kimi K3, with Auto failing 21/22 and fixed passing 22/22. This is run-to-run variation on the same model. Executions 043/044.

**5. The fixed model was the better choice.** Rule: the easy task with the largest cost ratio where both passed. `js-pick-omit`:
- Fixed passed in 4 calls, 9 s and $0.13.
- Auto ran 9 calls on GLM 5.3, hit 6 failed tool calls (3 of them permission denials), escalated to Kimi K3 for 8 more calls, and passed at $0.59 in 53 s.
- Executions 068/067. 16 of the 40 both-pass tasks cost more under Auto (see `report.md`, Scenarios).

## What the data supports, and what it doesn't

Supported, for this benchmark and this configuration:
- Jev-assisted Auto, with nconnect 0.23.0's default tiers, did **not** reduce total cost on agentic Claude Code tasks compared with running everything on Kimi K3: −0.8%, interval −37% to +29%.
- It **was slower**, by about 3× per task on tasks both passed.
- Its pass rate was **not lower**, and was 12 points higher in this pass (not statistically significant).
- Where Jev sent work to the balanced tier (42 tasks), Auto cost 21% less with no quality loss in this sample, at about 3× the completion time.
- Jev's own cost and latency are negligible here: $0.0026 for 115 calls, median 334 ms, no failures or late answers.

Not supported:
- "Routing cuts coding-agent costs by X×." This run saved 0.8% overall.
- "Routing improves quality." The difference is not significant, and half of Auto's extra passes came on the same model as the baseline.
- Any claim about Nebius billing that hasn't been reconciled (see below).
- Comparisons with the 1LittleCoder study. That work routed single-shot extraction and lookup prompts between DeepSeek V4 Flash and Kimi K2.6 against GPT-5.1, measured per prompt. This is multi-turn agentic coding, where one task makes 13–16 model calls. The workloads and baselines differ, and so do the economics: input re-sent on every call dominates cost here.

## Limitations

- **Single pass.** One run per condition per task. A task-level rerun can change its outcome; same-model pairs disagreed on 5 of 9 tasks. Run `bench/run.py prepare --repetitions 3` for firmer numbers.
- **Synthetic tasks.**
  - 50 self-contained tasks written for this benchmark, independently audited for fairness, in Python, TypeScript and JavaScript.
  - Each is one to a few files. Real repositories are larger.
  - The prompts are precise specifications, which is likely why Jev rarely judged them routine.
- **Permission policy.**
  - Headless Claude Code with a fixed allow-list turned about half of all failed tool calls into permission denials, in both conditions.
  - Because Auto escalates on failed tool calls, this hurt Auto's cost more than the baseline's.
- **Effort is part of the policy.** The comparison is of complete execution policies; it doesn't isolate model choice.
  - Fixed Kimi K3 ran at `reasoning_effort: none` (nconnect's default).
  - Auto raised effort on the first turn of strong tasks.
  - GLM 5.3 reasoned freely.
- **Pricing estimates.**
  - Costs are provider-reported tokens times Nebius's published prices (catalog captured 14 October 2026).
  - Cached input is at the full rate. That is an upper bound, and the conclusion flips if caching is discounted.
  - Jev is priced at $0.042/M input tokens (TypeSafe docs, same date).
- **Provider and host incidents.** Both were handled under rules written before the remaining data was collected (Amendments 1 and 2 in `docs/PROTOCOL.md`).
  - A GLM 5.3 outage and the laptop's sleep invalidated 10 executions. They were rerun, with the originals kept in `runs/main/attempts/` and listed in `report.md`.
  - Sensitivity, using the excluded attempts instead of their reruns: quality difference +8.0 pp, cost savings +4.3%. The time figure in that sensitivity is distorted by the sleep itself and shouldn't be used.
- **nconnect behaviours that shaped the result.** These are mechanisms 3 and 4 above, measured as found and not changed mid-run.
- **One harness, one machine, one region.** Claude Code 2.1.299 on macOS, through nconnect 0.23.0 to Nebius eu-west2.

## Billing reconciliation (not yet done)

Nebius exposes spend only in the console's Usage tab, filterable by project, with no usage API, so I could not reconcile the totals here.

- **Key:** the run used the higher-tier Token Factory key supplied on 14 October.
- **Window:** 2026-10-14 16:47:53 UTC (smoke test) to 2026-10-15 01:21:54 UTC.
- **Expected spend on the full-rate basis:**

| Part | Spend |
|---|---|
| Benchmark executions | $73.88 |
| Smoke tests and excluded attempts | $6.03 |
| Health probes | under $0.10 |
| **Total** | **about $79.91** |

Comparing that total with the console for this key and window will also settle the cache question:

| Console shows | Meaning |
|---|---|
| about $80 | cache hits are billed at the full input price |
| roughly $12–15 (the cache-free lower bound) | cache hits are close to free |
| in between | a partial cache discount |

Any other use of the same key in that window would need subtracting.

## Reproduce

```bash
cd nconnect-jev-benchmark
python3 bench/validate_dataset.py                    # 50/50 tasks: starter fails, reference passes
python3 bench/run.py smoke --conditions A,B           # about $0.35
python3 bench/run.py prepare --run-id rerun --repetitions 1
python3 bench/run.py run --run-id rerun --budget-usd 120 --max-hours 14
python3 bench/run.py requeue-infra --run-id rerun && python3 bench/run.py run --run-id rerun   # re-run outage or sleep hits
vendor/analysis-venv/bin/python bench/analyze.py --run-id rerun
vendor/analysis-venv/bin/python bench/report.py --run-id rerun
```

Credentials go in the gitignored `.env.local` (`NEBIUS_API_KEY=…`, `TYPESAFE_API_KEY=…`).

## Suggested nconnect fixes (from this run)

1. **Don't treat Claude Code's "Output token limit hit" resume message as a new prompt.** Keep the task's original decision.
2. **Don't count permission denials as failed tool calls** for the stuck rule.
3. **Consider a reasoning cap for GLM 5.3**, or a different balanced-tier default. Its uncapped reasoning made Auto about 3× slower.
4. **Revisit the "routine" criterion given to Jev.** Well-specified small changes were judged "moderate", so the fast tier is never the starting point for precisely written tasks.
5. **Read Nebius's `prompt_cache_hit_tokens` field** so nconnect's cost line can show cached input separately.

## Reference study

The brief mentions a reference study by "Dylan". The only reference supplied was the 1LittleCoder article and its repository [amrrs/jev-router-experiment](https://github.com/amrrs/jev-router-experiment), commit `56b4c3b`. If Dylan's study is a different piece, its link is missing.

This experiment borrows that study's method: a locked evaluation set, side-by-side quality, cost and latency, paired outcomes, scenarios, and explicit limitations. None of its results are used as evidence here.
