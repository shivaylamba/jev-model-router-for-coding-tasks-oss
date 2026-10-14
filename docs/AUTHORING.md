# Task authoring rules

These rules were fixed before any benchmark result was collected. Every task in
`dataset/` and `smoke/` follows them, and `bench/validate_dataset.py` checks the
parts that can be checked mechanically.

## Layout

```
dataset/tasks/<id>/task.json          metadata and the prompt
dataset/tasks/<id>/workspace/         the starting repository the agent receives
evaluator/<id>/acceptance_tests/      hidden tests, copied in only at grading time
evaluator/<id>/reference/             reference solution: every file it adds or changes
evaluator/<id>/reference.delete       optional: workspace paths the reference removes
```

Smoke tasks use the same layout under `smoke/tasks/` and `smoke/evaluator/`.
They are never part of the benchmark.

The agent only ever sees a copy of `workspace/`. Nothing under `evaluator/` is
reachable from its working directory.

## task.json

```json
{
  "id": "py-chunk-evenly",
  "title": "Split a list into near-equal chunks",
  "category": "utility",
  "difficulty": "easy",
  "language": "python",
  "prompt": "…the exact text sent to Claude Code…",
  "acceptance": "What the hidden tests check, for reviewers.",
  "difficulty_rationale": "Why this label.",
  "estimated_human_minutes": 10
}
```

- `category` is one of `utility`, `formatting`, `parsing`, `validation`, `bugfix`,
  `api-change`, `feature`, `refactor`, `state`.
- `difficulty` is one of `easy`, `medium`, `hard`, assigned by the evaluator:
  - **easy**: one function or file, a clear specification, few edge cases. About
    5 to 15 minutes for a competent developer.
  - **medium**: several functions or two to four files, several edge cases, or a
    bug whose cause takes some reading. About 15 to 45 minutes.
  - **hard**: interacting constraints, state, concurrency or caching, usually
    across several files, with edge cases a quick solution gets wrong. About one
    to three hours.
- `language` is `python`, `typescript` or `javascript`.

## The workspace

- Self-contained and offline. Python uses the standard library only (Python
  3.11). JavaScript and TypeScript use Node 24 built-ins only; a `package.json`
  may exist but has no dependencies.
- A short `README.md` says what the project is and how to run its tests
  (`python3 -m unittest discover -s tests` or `node --test`).
- TypeScript runs directly through Node 24's type stripping. The README says so,
  and that only erasable syntax works (no `enum`, `namespace` or constructor
  parameter properties) and that relative imports include the `.ts` extension.
- It may include visible tests of existing behaviour, as a real repository
  would. They must pass with the reference solution.
- Bug-fix tasks contain the real bug. Refactor tasks contain the code to
  refactor. Nothing hints at the solution beyond what a real codebase would.
- Never include a directory named `acceptance_tests`.

## The prompt

- Written the way a developer asks a colleague or files an issue: natural, and
  precise about every interface and behaviour the hidden tests check (names,
  signatures, return shapes, error types, edge cases).
- No difficulty or effort language and no router hints. The validator rejects
  these words: trivial, simple, simply, easy, easily, quick, quickly,
  straightforward, hard, harder, difficult, complex, complicated, tricky,
  challenging, careful, carefully, think, ultrathink, "step by step", tier,
  model.
- No mention of hidden or acceptance tests.
- Under 2,500 characters.

## Hidden acceptance tests

- Python: `acceptance_tests/__init__.py` (empty) and `acceptance_tests/test_*.py`
  using `unittest`. They import workspace modules as top-level modules; grading
  runs `python3 -m unittest discover -s acceptance_tests -t . -v` from the
  workspace root.
- JavaScript/TypeScript: `acceptance_tests/*.test.mjs` or `*.test.ts` using
  `node:test` and `node:assert/strict`, importing from `../src/...` or wherever
  the workspace keeps its code. Grading runs `node --test --test-reporter=tap`
  on those files from the workspace root.
- Deterministic, offline, and fast: the whole file runs in well under ten
  seconds. Time-dependent code is tested through an injected clock, never by
  sleeping.
- Assert only behaviour the prompt, README, docstrings, types or existing code
  conventions specify. Do not assert exact error message text unless the prompt
  specifies it.
- Cover the edge cases the prompt names. Easy tasks have at least 5 assertions,
  medium at least 10, hard at least 15.
- The starting workspace must fail at least one test, and the reference must
  pass them all.

## Validation

`python3 bench/validate_dataset.py --task <id>` checks the metadata, lints the
prompt, grades the untouched workspace (must fail), grades the reference twice
(must pass both times), and runs any visible tests against the reference.
