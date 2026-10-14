# nconnect routing benchmark: fixed Kimi K3 vs Jev-assisted Auto

The same 50 coding tasks run through Claude Code and nconnect under two
conditions:

- **A, router off:** every foreground request goes to Kimi K3.
- **B, router on:** nconnect's Auto picks a model per task, with TypeSafe's Jev judging how hard each task is.

Each task is graded by hidden tests. The runner records cost, time, tokens and
routing for every execution.

The research question, the verified setup and the scoring rules are in
[`docs/PROTOCOL.md`](docs/PROTOCOL.md). They were frozen before any result was
collected.

## Layout

| Path | What it is |
|---|---|
| `dataset/tasks/<id>/` | The 50 tasks: `task.json` (prompt, category, difficulty) and `workspace/` (the starting repository). |
| `evaluator/<id>/` | Hidden acceptance tests and reference solutions. Agents never see this folder. |
| `smoke/` | Three excluded smoke tasks used to validate the pipeline. |
| `config/experiment.json` | Conditions, limits, caps, seed and scoring, in machine-readable form. |
| `config/pricing/` | Dated snapshots of Nebius and TypeSafe pricing sources. |
| `bench/` | Validator, runner, request recorder, normalizer and analysis. |
| `runs/<id>/` | Raw, redacted evidence per execution, plus `manifest.json`, `plan.json`, `results.jsonl` and `events.jsonl`. |
| `reports/<id>/` | Tables, per-task rows, charts and the summary computed from `runs/<id>/`. |

## Setup (macOS, as run)

These are needed:

- Bun, which runs nconnect.
- Node 24 and Python 3.11 (standard library only).
- nconnect 0.23.0, installed at `~/.nconnect/bin/nconnect.js`.
- Claude Code 2.1.299, installed at `~/.local/share/claude/versions/2.1.299`.

`python3 bench/run.py prepare` copies nconnect and Claude Code into `vendor/` and
checks their hashes. Node and Python are linked in `vendor/bin`.

To set up the chart tooling (pinned in `requirements-analysis.lock`):

```bash
python3 -m venv vendor/analysis-venv
vendor/analysis-venv/bin/pip install -r requirements-analysis.lock
```

The tasks need no packages and no network.

## Credentials

The runner reads `NEBIUS_API_KEY` and `TYPESAFE_API_KEY` from the environment.
Failing that, it reads the Nebius key from `~/.nconnect/config.json` and either
key from a gitignored `.env.local` in this folder. It never prints them or writes
them to disk, and it redacts them from saved logs.

To add the TypeSafe key without it appearing in your shell history or anywhere else:

```bash
read -rs "TS?TypeSafe API key: " && printf 'TYPESAFE_API_KEY=%s\n' "$TS" > .env.local && chmod 600 .env.local && unset TS
```

For a clean billing reconciliation, use a Nebius key from a project used for
nothing else. Token Factory's console then shows this benchmark's spend alone,
filtered by project.

## Run

```bash
python3 bench/validate_dataset.py                        # every task: starter fails, reference passes
python3 bench/run.py smoke --conditions A,B              # excluded smoke tasks, about $0.50
python3 bench/run.py prepare --run-id main               # freeze manifest and seeded plan (50 tasks × A,B)
python3 bench/run.py run --run-id main --budget-usd 45 --max-hours 10
python3 bench/run.py status --run-id main
vendor/analysis-venv/bin/python bench/analyze.py --run-id main
```

- **Resuming:** `run` resumes after an interruption or a cap. It skips finished executions and keeps any interrupted attempt under `runs/<id>/attempts/`.
- **Repetitions:** for more paired passes, prepare a new run with `--repetitions N`.
