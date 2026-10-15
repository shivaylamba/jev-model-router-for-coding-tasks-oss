#!/usr/bin/env python3
"""Run the experiment: each task in a fresh Claude Code session through nconnect, once per condition.

  python3 bench/run.py prepare --run-id main            # pin binaries and catalog, write manifest and plan
  python3 bench/run.py run --run-id main                # execute (resumes where it stopped)
  python3 bench/run.py status --run-id main
  python3 bench/run.py smoke --conditions A,B           # excluded smoke tasks, same machinery

Credentials are read from the environment (NEBIUS_API_KEY, TYPESAFE_API_KEY) or,
failing that, from ~/.nconnect/config.json (Nebius) and the gitignored
.env.local file in the project root. They are never printed or written to disk.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, grade, list_tasks, load_task, materialize, sha256_file, tree_digest  # noqa: E402
from normalize import normalize  # noqa: E402

CONFIG = json.loads((ROOT / "config" / "experiment.json").read_text())
VENDOR = ROOT / "vendor"
RUNS = ROOT / "runs"
NCONNECT_BUNDLE = VENDOR / "nconnect-0.23.0.js"
NCONNECT_SOURCE = Path.home() / ".nconnect" / "bin" / "nconnect.js"
NCONNECT_EXPECTED_SHA = "db122e2754730104b6dd6854ad39161018a219c09baeb53090bd1684331ef9b0"
NCONNECT_SOURCE_COMMIT = "66bf93fd609b30f1ce40e44d748bcb1b025355a7"
CLAUDE_VERSION = "2.1.299"
CLAUDE_BINARY = VENDOR / f"claude-{CLAUDE_VERSION}"
CLAUDE_SOURCE = Path.home() / ".local" / "share" / "claude" / "versions" / CLAUDE_VERSION
BUN = Path.home() / ".bun" / "bin" / "bun"
GIT = Path("/opt/homebrew/bin/git")
FROZEN_UNTIL_MS = 4_102_444_800_000  # 2100-01-01: keeps nconnect from refreshing the pinned catalog
PORT = CONFIG["nconnect_port"]
NEBIUS_ORIGIN_BASE = "https://api.tokenfactory.nebius.com/v1"

# Auto's default pools in nconnect 0.23.0 (packages/cli/src/lib/auto-model.ts, DEFAULT_POOLS),
# verified against observed routes during the smoke test.
AUTO_POOLS = {
    "fast": ["zai-org/GLM-5.3-Flash", "deepseek-ai/DeepSeek-V4.1-Flash"],
    "balanced": ["zai-org/GLM-5.3", "moonshotai/Kimi-K2.6"],
    "strong": ["moonshotai/Kimi-K3"],
}
BACKGROUND_MODEL = "zai-org/GLM-5.3-Flash"
JEV_PRICE = {"model": "jev-1.13.0", "input_per_million_usd": 0.042, "output_per_million_usd": 0.0,
             "source": "https://docs.typesafe.ai/models", "snapshot": "config/pricing/typesafe-docs-models.2026-10-14.txt"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def log_event(run_dir: Path, message: str, **extra) -> None:
    line = {"at": now_iso(), "event": message, **extra}
    with (run_dir / "events.jsonl").open("a") as handle:
        handle.write(json.dumps(line) + "\n")
    print(f"[{line['at']}] {message}" + (f" {extra}" if extra else ""), flush=True)


# ---------------------------------------------------------------- secrets

def secret(name: str) -> str | None:
    """The project's .env.local wins, so a benchmark key is never silently swapped for a personal one."""
    local = ROOT / ".env.local"
    if local.exists():
        for line in local.read_text().splitlines():
            key, _, value = line.partition("=")
            if key.strip() == name and value.strip():
                return value.strip().strip('"').strip("'")
    value = os.environ.get(name, "").strip()
    if value:
        return value
    if name == "NEBIUS_API_KEY":
        config = Path.home() / ".nconnect" / "config.json"
        if config.exists():
            return (json.loads(config.read_text()).get("apiKey") or "").strip() or None
    return None


# ---------------------------------------------------------------- pinning and preparation

def ensure_vendor() -> None:
    VENDOR.mkdir(exist_ok=True)
    (VENDOR / "bin").mkdir(exist_ok=True)
    if not NCONNECT_BUNDLE.exists():
        if sha256_file(NCONNECT_SOURCE) != NCONNECT_EXPECTED_SHA:
            sys.exit("The installed nconnect bundle is not the 0.23.0 release this experiment pins.")
        shutil.copy2(NCONNECT_SOURCE, NCONNECT_BUNDLE)
    if sha256_file(NCONNECT_BUNDLE) != NCONNECT_EXPECTED_SHA:
        sys.exit("vendor/nconnect-0.23.0.js does not match the pinned sha256.")
    if not CLAUDE_BINARY.exists():
        shutil.copy2(CLAUDE_SOURCE, CLAUDE_BINARY)
    links = {"claude": CLAUDE_BINARY, "git": GIT, "bun": BUN}
    for name, target in links.items():
        link = VENDOR / "bin" / name
        if not link.exists():
            link.symlink_to(target)


def tool_path() -> str:
    return f"{VENDOR / 'bin'}:/usr/bin:/bin:/usr/sbin:/sbin"


def base_env(home: Path, tmp: Path) -> dict:
    """Built from nothing, so no NCONNECT_*, CLAUDE_* or ANTHROPIC_* setting leaks in from the shell."""
    return {
        "PATH": tool_path(),
        "HOME": str(home),
        "TMPDIR": str(tmp),
        "USER": os.environ.get("USER", "bench"),
        "LOGNAME": os.environ.get("USER", "bench"),
        "SHELL": "/bin/zsh",
        "LANG": "en_US.UTF-8",
        "TERM": "dumb",
        "TZ": "UTC",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def run_quiet(cmd: list[str], env: dict, cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                          stdin=subprocess.DEVNULL)


def kill_port(port: int) -> None:
    found = subprocess.run(["/usr/sbin/lsof", f"-tiTCP:{port}", "-sTCP:LISTEN"], capture_output=True, text=True)
    pids = [int(p) for p in found.stdout.split()]
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.time() + 5
    while pids and time.time() < deadline:
        pids = [p for p in pids if _alive(p)]
        time.sleep(0.2)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def pin_catalog(run_dir: Path, nebius_key: str) -> dict:
    """Load the live catalog once through nconnect itself, then freeze it for the whole run.

    nconnect 0.23.0 keeps its catalog cache in $HOME/.nconnect even when
    NCONNECT_HOME points elsewhere, so every execution gets a home whose
    .nconnect holds these frozen files.
    """
    pinned = run_dir / "pinned"
    pinned.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="njb-prep-") as tmp:
        tmp = Path(tmp)
        nhome = tmp / "home" / ".nconnect"
        nhome.mkdir(parents=True)
        env = {**base_env(tmp / "home", tmp), "NEBIUS_API_KEY": nebius_key, "NCONNECT_HOME": str(nhome),
               "NCONNECT_PORT": str(PORT), "NCONNECT_DISABLE_AUTOUPDATE": "1"}
        models = run_quiet([str(BUN), str(NCONNECT_BUNDLE), "models", "--json", "--all"], env)
        if models.returncode != 0:
            models = run_quiet([str(BUN), str(NCONNECT_BUNDLE), "models", "--json"], env)
        version = run_quiet([str(BUN), str(NCONNECT_BUNDLE), "--version"], env).stdout.strip()
        time.sleep(3)  # give the background models.dev refresh a moment to land
        kill_port(PORT)
        if not (nhome / "model-catalog.json").exists():
            sys.exit("nconnect did not write a model catalog; check NEBIUS_API_KEY and the network.")
        shutil.copy2(nhome / "model-catalog.json", pinned / "model-catalog.json")
        source_dev = nhome / "models-dev.json"
        if not source_dev.exists():
            source_dev = Path.home() / ".nconnect" / "models-dev.json"
        if source_dev.exists():
            shutil.copy2(source_dev, pinned / "models-dev.json")
    for name in ("model-catalog.json", "models-dev.json"):
        path = pinned / name
        if path.exists():
            data = json.loads(path.read_text())
            data["fetchedAt"] = FROZEN_UNTIL_MS
            path.write_text(json.dumps(data))
    catalog = json.loads((pinned / "model-catalog.json").read_text())
    if catalog.get("baseUrl") != NEBIUS_ORIGIN_BASE:
        sys.exit(f"Pinned catalog has baseUrl {catalog.get('baseUrl')!r}; expected {NEBIUS_ORIGIN_BASE}")
    (pinned / "nconnect-models.json").write_text(models.stdout)
    return {"nconnect_version_output": version, "catalog": catalog}


def all_conditions() -> dict:
    return {**CONFIG["conditions"], **CONFIG["pipeline_check_conditions"], **CONFIG.get("v2_conditions", {})}


def bundle_for(spec: dict) -> Path:
    """The nconnect bundle a condition runs: 0.23.0 unless the condition pins another build."""
    return ROOT / spec["nconnect_bundle"] if spec.get("nconnect_bundle") else NCONNECT_BUNDLE


def check_bundle(spec: dict) -> None:
    if spec.get("nconnect_bundle") and sha256_file(bundle_for(spec)) != spec["nconnect_bundle_sha256"]:
        sys.exit(f"{spec['nconnect_bundle']} does not match its pinned sha256.")


def copy_catalog(run_dir: Path, source_run: str) -> dict:
    """Reuse another run's frozen catalog, so both runs price tokens identically."""
    source = RUNS / source_run / "pinned"
    pinned = run_dir / "pinned"
    shutil.copytree(source, pinned)
    catalog = json.loads((pinned / "model-catalog.json").read_text())
    manifest = json.loads((RUNS / source_run / "manifest.json").read_text())
    return {"nconnect_version_output": manifest["versions"]["nconnect_version"], "catalog": catalog,
            "copied_from": source_run}


def seed_nconnect_home(run_dir: Path, nhome: Path) -> None:
    nhome.mkdir(parents=True, exist_ok=True)
    for name in ("model-catalog.json", "models-dev.json"):
        source = run_dir / "pinned" / name
        if source.exists():
            shutil.copy2(source, nhome / name)


def prices_from_catalog(catalog: dict) -> dict:
    prices = {}
    for model in catalog["models"]:
        pricing = model.get("pricing") or {}
        try:
            prices[model["id"]] = {
                "input_per_million_usd": round(float(pricing["prompt"]) * 1e6, 6),
                "output_per_million_usd": round(float(pricing["completion"]) * 1e6, 6),
                "cached_input_per_million_usd": (None if pricing.get("input_cache_read") is None
                                                 else round(float(pricing["input_cache_read"]) * 1e6, 6)),
            }
        except (KeyError, TypeError, ValueError):
            continue
    return prices


def protocol_digest() -> dict:
    return tree_digest([ROOT / "dataset", ROOT / "evaluator", ROOT / "config" / "experiment.json",
                        ROOT / "docs" / "AUTHORING.md", ROOT / "docs" / "TASK_PLAN.md",
                        ROOT / "bench"], ROOT)


def make_plan(task_ids: list[str], conditions: list[str], repetitions: int, seed: int) -> list[dict]:
    """Seeded task order; within each task pair, which condition goes first is balanced and seeded."""
    plan, seq = [], 0
    for rep in range(1, repetitions + 1):
        rng = random.Random(seed * 1000 + rep)
        order = list(task_ids)
        rng.shuffle(order)
        firsts = [conditions[i % len(conditions)] for i in range(len(order))]
        rng.shuffle(firsts)
        for task_id, first in zip(order, firsts):
            ordered = [first] + [c for c in conditions if c != first]
            for position, condition in enumerate(ordered):
                seq += 1
                plan.append({"seq": seq, "repetition": rep, "task_id": task_id, "condition": condition,
                             "pair_position": "first" if position == 0 else "second"})
    return plan


def prepare(args) -> Path:
    run_dir = RUNS / args.run_id
    if (run_dir / "manifest.json").exists():
        sys.exit(f"{run_dir} already prepared; its manifest is frozen. Use a new --run-id.")
    nebius_key = secret("NEBIUS_API_KEY")
    if not nebius_key:
        sys.exit("NEBIUS_API_KEY is missing (environment or ~/.nconnect/config.json).")
    ensure_vendor()
    run_dir.mkdir(parents=True)
    suite = args.suite
    tasks = list_tasks(suite)
    if args.tasks:
        wanted = args.tasks.split(",")
        tasks = [t for t in tasks if t.id in wanted]
    conditions = args.conditions.split(",")
    for condition in conditions:
        spec = all_conditions().get(condition)
        if spec is None:
            sys.exit(f"unknown condition {condition}")
        check_bundle(spec)
        if spec.get("smoke_only") and suite != "smoke":
            sys.exit(f"{condition} is a pipeline check and may only run on smoke tasks")
    pinned = copy_catalog(run_dir, args.catalog_from) if args.catalog_from else pin_catalog(run_dir, nebius_key)
    prices = prices_from_catalog(pinned["catalog"])
    pools = next((all_conditions()[c]["pools"] for c in conditions if all_conditions()[c].get("pools")), AUTO_POOLS)
    for model in [m for pool in pools.values() for m in pool] + [CONFIG["conditions"]["A"]["nconnect_model"]]:
        if model not in prices:
            print(f"warning: no price for {model} in the pinned catalog", file=sys.stderr)
    claude_version = run_quiet([str(CLAUDE_BINARY), "--version"], base_env(Path(tempfile.gettempdir()), Path(tempfile.gettempdir()))).stdout.strip()
    node_version = run_quiet([str(VENDOR / "bin" / "node"), "--version"], {"PATH": tool_path()}).stdout.strip()
    python_version = run_quiet([str(VENDOR / "bin" / "python3"), "--version"], {"PATH": tool_path()}).stdout.strip()
    bun_version = run_quiet([str(BUN), "--version"], {"PATH": tool_path()}).stdout.strip()
    manifest = {
        "run_id": args.run_id,
        "suite": suite,
        "created_at": now_iso(),
        "seed": CONFIG["seed"],
        "repetitions": args.repetitions,
        "conditions": {c: all_conditions()[c] for c in conditions},
        "common_env": CONFIG["common_env"],
        "left_at_default": CONFIG["left_at_default"],
        "limits": CONFIG["limits"],
        "claude_code": CONFIG["claude_code"],
        "scoring": CONFIG["scoring"],
        # Claude Code's background calls (titles, permission checks) go to the catalog default in every
        # condition, so they count as expected models too.
        "auto": {"pools": pools, "pool_models": sorted({m for p in pools.values() for m in p} | {BACKGROUND_MODEL}),
                 "cost_tier": "medium", "thresholds_medium": [0.3, 0.7], "per_turn": False,
                 "stuck_after_tool_errors": 3, "decider_wait_ms": 2500, "decider_hard_timeout_ms": 20000,
                 "background_model": BACKGROUND_MODEL},
        "versions": {
            "nconnect_bundle_sha256": sha256_file(NCONNECT_BUNDLE),
            "condition_bundles": {c: {"path": all_conditions()[c]["nconnect_bundle"],
                                      "sha256": all_conditions()[c]["nconnect_bundle_sha256"],
                                      "source_commit": all_conditions()[c]["nconnect_source_commit"]}
                                  for c in conditions if all_conditions()[c].get("nconnect_bundle")},
            "catalog_copied_from": pinned.get("copied_from"),
            "nconnect_version": pinned["nconnect_version_output"],
            "nconnect_source_commit": NCONNECT_SOURCE_COMMIT,
            "nconnect_provenance": "The installed bundle (~/.nconnect/bin/nconnect.js) is byte-identical to "
                                   "https://nconnect.sh/nconnect.js, which Vercel builds from main at "
                                   f"{NCONNECT_SOURCE_COMMIT[:7]} (PR #32 merge, v0.23.0).",
            "claude_code": claude_version,
            "claude_code_binary_sha256": sha256_file(CLAUDE_BINARY),
            "node": node_version,
            "node_binary_sha256": sha256_file(VENDOR / "node-v24.18.1"),
            "python": python_version,
            "bun": bun_version,
            "os": run_quiet(["/usr/bin/sw_vers", "-productVersion"], {"PATH": "/usr/bin"}).stdout.strip(),
        },
        "prices": {
            "nebius": prices,
            "nebius_source": "GET https://api.tokenfactory.nebius.com/v1/models?verbose=true through nconnect, "
                             "pinned in runs/<id>/pinned/model-catalog.json; cross-checked against "
                             "config/pricing/nebius-public-models_info.2026-10-14.json",
            "jev": JEV_PRICE,
            "captured_at": now_iso(),
        },
        "dataset_digest": tree_digest([ROOT / "dataset", ROOT / "evaluator"], ROOT) if suite == "dataset"
        else tree_digest([ROOT / suite], ROOT),
        "protocol_digest": protocol_digest(),
        "task_ids": [t.id for t in tasks],
    }
    plan = make_plan([t.id for t in tasks], conditions, args.repetitions, CONFIG["seed"])
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (run_dir / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    (run_dir / "executions").mkdir()
    log_event(run_dir, "prepared", tasks=len(tasks), executions=len(plan), conditions=conditions)
    return run_dir


# ---------------------------------------------------------------- one execution

class StreamWatcher:
    """Reads Claude Code's stdout, stamps each line, and keeps the counts the limits need."""

    def __init__(self, stream, out_path: Path):
        self.stream = stream
        self.out = gzip.open(out_path, "wt", encoding="utf-8")
        self.message_ids: set[str] = set()
        self.lines = 0
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        for raw in self.stream:
            line = raw.rstrip("\n")
            if not line:
                continue
            stamp = int(time.time() * 1000)
            self.out.write(json.dumps({"t": stamp, "line": line}) + "\n")
            self.lines += 1
            if '"type":"assistant"' in line or '"type": "assistant"' in line:
                try:
                    event = json.loads(line)
                    message_id = event.get("message", {}).get("id")
                    if event.get("type") == "assistant" and message_id:
                        self.message_ids.add(message_id)
                except ValueError:
                    pass
        self.out.close()

    def join(self) -> None:
        self.thread.join(timeout=30)


def running_cost(recorder_path: Path, offset: int, manifest: dict, total: float) -> tuple[int, float]:
    if not recorder_path.exists():
        return offset, total
    with recorder_path.open() as handle:
        handle.seek(offset)
        for line in handle:
            try:
                req = json.loads(line)
            except ValueError:
                continue
            usage = req.get("usage") or {}
            rate = manifest["prices"]["nebius"].get(req.get("response_model") or req.get("model") or "")
            if rate and usage.get("prompt_tokens") is not None:
                total += (usage["prompt_tokens"] * rate["input_per_million_usd"]
                          + (usage.get("completion_tokens") or 0) * rate["output_per_million_usd"]) / 1e6
        offset = handle.tell()
    return offset, total


def start_recorder(out: Path, env: dict) -> tuple[subprocess.Popen, int]:
    proc = subprocess.Popen([str(VENDOR / "bin" / "node"), str(ROOT / "bench" / "recorder.mjs"), "--out", str(out)],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                            start_new_session=True)
    line = proc.stdout.readline()
    return proc, json.loads(line)["port"]


def contamination(stream_path: Path) -> list[str]:
    """Any tool call that reached for the benchmark's own files."""
    markers = [str(ROOT), "nconnect-jev-benchmark", "acceptance_tests", "/evaluator/", "reference.delete"]
    flags = []
    with gzip.open(stream_path, "rt", encoding="utf-8", errors="replace") as handle:
        for wrapped in handle:
            if '"tool_use"' not in wrapped:
                continue
            for marker in markers:
                if marker in wrapped:
                    flags.append(f"tool call mentions {marker!r}")
    return sorted(set(flags))


def redact(paths: list[Path], secrets: list[str]) -> None:
    secrets = [s for s in secrets if s and len(s) >= 12]
    for path in paths:
        if not path.exists() or path.is_dir():
            continue
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        else:
            text = path.read_text(errors="replace")
        cleaned = text
        for value in secrets:
            cleaned = cleaned.replace(value, "[REDACTED]")
        if cleaned != text:
            if path.suffix == ".gz":
                with gzip.open(path, "wt", encoding="utf-8") as handle:
                    handle.write(cleaned)
            else:
                path.write_text(cleaned)


def gzip_file(path: Path) -> Path:
    target = path.with_suffix(path.suffix + ".gz")
    if path.exists():
        with path.open("rb") as src, gzip.open(target, "wb") as dst:
            shutil.copyfileobj(src, dst)
        path.unlink()
    return target


def fallback_diagnostics(home_dir: Path) -> int:
    path = home_dir / "request-diagnostics.jsonl"
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text().splitlines() if '"phase":"fallback"' in line)


def execute(run_dir: Path, manifest: dict, item: dict, keys: dict) -> dict:
    task = load_task(item["task_id"], manifest["suite"])
    condition = item["condition"]
    spec = manifest["conditions"][condition]
    name = f"{item['seq']:03d}-r{item['repetition']}-{task.id}-{condition}"
    exec_dir = run_dir / "executions" / name
    if exec_dir.exists():
        attempts = run_dir / "attempts"
        attempts.mkdir(exist_ok=True)
        n = len(list(attempts.glob(f"{name}.attempt-*"))) + 1
        exec_dir.rename(attempts / f"{name}.attempt-{n}")
        log_event(run_dir, "kept interrupted attempt", execution=name, attempt=n)
    exec_dir.mkdir(parents=True)
    tmp = Path(tempfile.mkdtemp(prefix="njb-"))
    workspace = tmp / "workspace"
    home = tmp / "home"
    (tmp / "tmp").mkdir()
    home.mkdir()
    # A fresh nconnect home per execution: a fresh daemon, an empty decider
    # cache, and the frozen catalog.
    home_dir = home / ".nconnect"
    seed_nconnect_home(run_dir, home_dir)
    materialize(task, workspace)
    git_env = {**base_env(home, tmp / "tmp"), "GIT_AUTHOR_NAME": "bench", "GIT_AUTHOR_EMAIL": "bench@example.invalid",
               "GIT_COMMITTER_NAME": "bench", "GIT_COMMITTER_EMAIL": "bench@example.invalid",
               "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}
    for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "Initial commit"]):
        run_quiet([str(GIT), *cmd], git_env, cwd=workspace)

    kill_port(PORT)
    recorder_env = {"PATH": tool_path(), "HOME": str(home)}
    recorder, rport = start_recorder(exec_dir / "recorder.jsonl", recorder_env)
    env = {
        **base_env(home, tmp / "tmp"),
        **manifest["common_env"],
        **spec.get("env", {}),
        "NEBIUS_API_KEY": keys["NEBIUS_API_KEY"],
        "NEBIUS_BASE_URL": f"http://127.0.0.1:{rport}/v1",
        "NCONNECT_HOME": str(home_dir),
        "NCONNECT_PORT": str(PORT),
        "NCONNECT_DEBUG_LOG": str(exec_dir / "nconnect-debug.log"),
        "CLAUDE_CONFIG_DIR": str(tmp / "claude-config"),
    }
    for name_ in spec.get("secrets", []):
        env[name_] = keys[name_]
    if spec.get("decider_through_recorder"):
        env["NCONNECT_AUTO_DECIDER_URL"] = f"http://127.0.0.1:{rport}/typesafe/v1/systemone"
    cc = manifest["claude_code"]
    command = [str(BUN), str(bundle_for(spec)), "--model", spec["nconnect_model"], "claude", "-p", task.prompt,
               *cc["flags"], "--allowedTools", ",".join(cc["allowed_tools"]),
               "--disallowedTools", ",".join(cc["disallowed_tools"])]
    limits = manifest["limits"]
    meta = {
        "run_id": manifest["run_id"], "seq": item["seq"], "repetition": item["repetition"],
        "task_id": task.id, "category": task.meta["category"], "difficulty": task.meta["difficulty"],
        "language": task.language, "condition": condition, "pair_position": item["pair_position"],
        "command": [c if c != task.prompt else "<task prompt>" for c in command],
        "env_names": sorted(env.keys()),
        "env_settings": {k: v for k, v in env.items() if k.startswith(("NCONNECT_", "DISABLE_")) or k == "NEBIUS_BASE_URL"},
        "limits": limits, "versions": manifest["versions"], "anomalies": [],
    }
    started_ms = int(time.time() * 1000)
    meta.update(started_at=now_iso(), started_ms=started_ms)
    (exec_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    termination = "completed"
    stderr_file = (exec_dir / "nconnect-stderr.log").open("w")
    proc = subprocess.Popen(command, cwd=workspace, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=stderr_file, text=True, start_new_session=True)
    watcher = StreamWatcher(proc.stdout, exec_dir / "claude-stream.jsonl.gz")
    cost_offset, cost_so_far = 0, 0.0
    try:
        while proc.poll() is None:
            time.sleep(1)
            elapsed = time.time() - started_ms / 1000
            cost_offset, cost_so_far = running_cost(exec_dir / "recorder.jsonl", cost_offset, manifest, cost_so_far)
            if elapsed > limits["wall_seconds_per_task"]:
                termination = "wall_limit"
            elif len(watcher.message_ids) > limits["max_model_requests_per_task"]:
                termination = "request_limit"
            elif cost_so_far > limits["per_execution_cost_cap_usd"]:
                termination = "cost_cap"
            if termination != "completed":
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                break
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        watcher.join()
        stderr_file.close()
        ended_ms = int(time.time() * 1000)
        time.sleep(1)  # let the daemon finish writing its last usage line
        kill_port(PORT)
        recorder.terminate()
        try:
            recorder.wait(timeout=10)
        except subprocess.TimeoutExpired:
            recorder.kill()

    meta.update(ended_at=now_iso(), ended_ms=ended_ms, duration_s=round((ended_ms - started_ms) / 1000, 3),
                exit_code=proc.returncode, termination=termination,
                fallback_diagnostics=fallback_diagnostics(home_dir))
    for name_ in ("request-diagnostics.jsonl",):
        if (home_dir / name_).exists():
            shutil.copy2(home_dir / name_, exec_dir / f"nconnect-{name_}")
    if (home_dir / "model-catalog.json").exists() and json.loads((home_dir / "model-catalog.json").read_text()).get("fetchedAt") != FROZEN_UNTIL_MS:
        meta["anomalies"].append("nconnect refreshed the pinned catalog during the task")

    # Evidence: the transcript Claude Code kept, the final workspace and its diff.
    transcripts = sorted((tmp / "claude-config" / "projects").rglob("*.jsonl")) if (tmp / "claude-config").exists() else []
    if transcripts:
        with gzip.open(exec_dir / "claude-transcript.jsonl.gz", "wt", encoding="utf-8") as out:
            for path in transcripts:
                out.write(path.read_text(errors="replace"))
    run_quiet([str(GIT), "add", "-A"], git_env, cwd=workspace)
    diff = run_quiet([str(GIT), "diff", "--cached", "HEAD", "--stat", "--patch"], git_env, cwd=workspace)
    (exec_dir / "workspace.diff").write_text(diff.stdout)
    shutil.make_archive(str(exec_dir / "workspace-final"), "gztar", root_dir=workspace)

    result = grade(task, workspace)
    (exec_dir / "grade.json").write_text(json.dumps(result.as_dict(), indent=2))
    (exec_dir / "grade-output.txt").write_text(result.output[-20000:])

    meta["contamination_flags"] = contamination(exec_dir / "claude-stream.jsonl.gz")
    (exec_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    gzip_file(exec_dir / "nconnect-debug.log")
    token_file = home_dir / "local-proxy-token"
    redact(list(exec_dir.iterdir()), [keys.get("NEBIUS_API_KEY", ""), keys.get("TYPESAFE_API_KEY", ""),
                                      token_file.read_text().strip() if token_file.exists() else ""])
    record = normalize(exec_dir, manifest)
    (exec_dir / "record.json").write_text(json.dumps(record, indent=2))
    with (run_dir / "results.jsonl").open("a") as handle:
        handle.write(json.dumps(record) + "\n")
    (exec_dir / "DONE").write_text(now_iso())
    shutil.rmtree(tmp, ignore_errors=True)
    return record


# ---------------------------------------------------------------- provider health and infrastructure failures
# Amendment 1 (docs/PROTOCOL.md): added after a GLM 5.3 outage, before results beyond execution 8.

HEALTH_MODELS = ["moonshotai/Kimi-K3", "zai-org/GLM-5.3", "zai-org/GLM-5.3-Flash"]
HEALTH_WAIT_S = 300
INFRA_TAIL = 3
INFRA_RERUNS = 2


def probe(model: str, key: str, timeout: int = 30) -> tuple[bool, str]:
    """One tiny request straight to Nebius (via curl; the key goes on stdin, never argv).
    Not part of any task's cost; logged as overhead."""
    body = json.dumps({"model": model, "max_tokens": 8, "messages": [{"role": "user", "content": "Reply with OK"}]})
    started = time.time()
    proc = subprocess.run(["curl", "-sS", "-m", str(timeout), "-o", "/dev/null", "-w", "%{http_code}", "-K", "-",
                           "-H", "content-type: application/json", f"{NEBIUS_ORIGIN_BASE}/chat/completions", "-d", body],
                          input=f'header = "Authorization: Bearer {key}"\n', capture_output=True, text=True)
    code = proc.stdout.strip()
    if code == "200":
        return True, f"200 in {time.time() - started:.1f}s"
    return False, f"HTTP {code}" if code and code != "000" else (proc.stderr.strip()[:60] or "no response")


def health_models(manifest: dict) -> list[str]:
    """The main run probed HEALTH_MODELS. A run with its own pools probes the models it can actually use."""
    if not any(spec.get("pools") for spec in manifest["conditions"].values()):
        return HEALTH_MODELS
    models = {spec["nconnect_model"] for spec in manifest["conditions"].values() if spec["nconnect_model"] != "auto"}
    return sorted(models | set(manifest["auto"]["pool_models"]))


def wait_until_healthy(run_dir: Path, key: str, deadline: float, models: list[str] = HEALTH_MODELS) -> bool:
    while True:
        results = {model: probe(model, key) for model in models}
        bad = {m: r[1] for m, r in results.items() if not r[0]}
        if not bad:
            return True
        log_event(run_dir, "provider unhealthy; waiting", models=bad, wait_s=HEALTH_WAIT_S)
        if time.time() + HEALTH_WAIT_S > deadline:
            return False
        time.sleep(HEALTH_WAIT_S)


def infra_failure(run_dir: Path, record: dict) -> str | None:
    """Failed, and the provider answered none of the last INFRA_TAIL model requests."""
    if record["passed"]:
        return None
    exec_dir = next((run_dir / "executions").glob(f"{record['seq']:03d}-*"), None)
    if exec_dir is None:
        return None
    requests = [json.loads(line) for line in (exec_dir / "recorder.jsonl").read_text().splitlines() if line.strip()]
    model_requests = [r for r in requests if r.get("kind") in ("agent", "toolless")]
    tail = model_requests[-INFRA_TAIL:]
    if len(tail) < INFRA_TAIL or any(r.get("status") == 200 and r.get("usage") for r in tail):
        return None
    failed = sum(1 for r in model_requests if not (r.get("status") == 200 and r.get("usage")))
    models = sorted({r.get("model") for r in tail})
    return (f"the last {INFRA_TAIL} model requests ({', '.join(models)}) got no provider response; "
            f"{failed} of {len(model_requests)} model requests failed")


def quarantine(run_dir: Path, record: dict, reason: str) -> None:
    """Keep the evidence, take the execution out of the primary results, so the loop re-runs it."""
    exec_dir = next((run_dir / "executions").glob(f"{record['seq']:03d}-*"))
    attempts = run_dir / "attempts"
    attempts.mkdir(exist_ok=True)
    n = len(list(attempts.glob(f"{exec_dir.name}.infra-*"))) + 1
    exec_dir.rename(attempts / f"{exec_dir.name}.infra-{n}")
    results = load_results(run_dir)
    keep = [r for r in results if r["seq"] != record["seq"]]
    (run_dir / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in keep))
    with (run_dir / "excluded.jsonl").open("a") as handle:
        handle.write(json.dumps({**record, "excluded_reason": "infrastructure failure: " + reason,
                                 "excluded_at": now_iso(), "kept_at": f"attempts/{exec_dir.name}.infra-{n}"}) + "\n")
    log_event(run_dir, "infrastructure failure: excluded and queued for re-run", execution=exec_dir.name, reason=reason)


def host_sleep_intervals() -> list[tuple[datetime, datetime]]:
    """Sleep periods from the macOS power log: a Sleep entry until the next DarkWake, or a Wake more than 10 s later."""
    out = subprocess.run(["/usr/bin/pmset", "-g", "log"], capture_output=True, text=True).stdout
    sleeps, start = [], None
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[3] not in ("Sleep", "Wake", "DarkWake"):
            continue
        try:
            at = datetime.strptime(" ".join(parts[:3]), "%Y-%m-%d %H:%M:%S %z")
        except ValueError:
            continue
        if parts[3] == "Sleep":
            start = at
        elif start and (parts[3] == "DarkWake" or (at - start).total_seconds() > 10):
            sleeps.append((start, at))
            start = None
    return sleeps


def slept_during(run_dir: Path, record: dict, sleeps) -> float:
    start = datetime.fromisoformat(record["started_at"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(record["ended_at"].replace("Z", "+00:00"))
    return sum(max(0.0, (min(b, end) - max(a, start)).total_seconds()) for a, b in sleeps if a < end and b > start)


def requeue_infra(args) -> None:
    run_dir = RUNS / args.run_id
    for record in load_results(run_dir):
        reason = infra_failure(run_dir, record)
        if reason:
            quarantine(run_dir, record, reason)
    # Amendment 2: the host machine slept during the execution.
    sleeps = host_sleep_intervals()
    (run_dir / "host-sleep-intervals.json").write_text(json.dumps([(a.isoformat(), b.isoformat()) for a, b in sleeps], indent=1))
    for record in load_results(run_dir):
        asleep = slept_during(run_dir, record, sleeps)
        if asleep > 0:
            quarantine(run_dir, record, f"the host machine was asleep for {asleep:.0f} s of its {record['duration_s']:.0f} s")


# ---------------------------------------------------------------- run loop

def load_results(run_dir: Path) -> list[dict]:
    path = run_dir / "results.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def verify_frozen(run_dir: Path, manifest: dict) -> None:
    current = (tree_digest([ROOT / "dataset", ROOT / "evaluator"], ROOT) if manifest["suite"] == "dataset"
               else tree_digest([ROOT / manifest["suite"]], ROOT))
    if current != manifest["dataset_digest"]:
        changed = sorted(k for k in set(current) | set(manifest["dataset_digest"])
                         if current.get(k) != manifest["dataset_digest"].get(k))
        sys.exit(f"The dataset changed after the manifest was frozen: {changed[:10]}")
    if sha256_file(NCONNECT_BUNDLE) != manifest["versions"]["nconnect_bundle_sha256"]:
        sys.exit("The pinned nconnect bundle changed.")
    for spec in manifest["conditions"].values():
        check_bundle(spec)
    if sha256_file(CLAUDE_BINARY) != manifest["versions"]["claude_code_binary_sha256"]:
        sys.exit("The pinned Claude Code binary changed.")


def run(args, run_dir: Path | None = None) -> None:
    run_dir = run_dir or RUNS / args.run_id
    manifest = json.loads((run_dir / "manifest.json").read_text())
    plan = json.loads((run_dir / "plan.json").read_text())
    verify_frozen(run_dir, manifest)
    keys = {"NEBIUS_API_KEY": secret("NEBIUS_API_KEY")}
    needed = {s for c in manifest["conditions"].values() for s in c.get("secrets", [])}
    for name in needed:
        keys[name] = secret(name)
    missing = [k for k, v in keys.items() if not v]
    if missing:
        sys.exit(f"Missing credentials: {', '.join(missing)}. See README.md, 'Credentials'.")
    budget = args.budget_usd if args.budget_usd is not None else CONFIG["default_caps"]["budget_usd"]
    max_hours = args.max_hours if args.max_hours is not None else CONFIG["default_caps"]["max_hours"]
    log_event(run_dir, "run started", budget_usd=budget, max_hours=max_hours)
    # Amendment 2: keep the host awake for as long as this process lives.
    subprocess.Popen(["/usr/bin/caffeinate", "-i", "-s", "-w", str(os.getpid())], stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    started = time.time()
    done = {(r["repetition"], r["task_id"], r["condition"]) for r in load_results(run_dir)}
    for item in plan:
        key = (item["repetition"], item["task_id"], item["condition"])
        if key in done:
            continue
        spent = sum(r["cost_total_usd"] for r in load_results(run_dir))
        if spent >= budget:
            log_event(run_dir, "stopped: budget reached", spent_usd=round(spent, 4), budget_usd=budget)
            return
        if (time.time() - started) / 3600 >= max_hours:
            log_event(run_dir, "stopped: runtime cap reached", hours=max_hours)
            return
        if not wait_until_healthy(run_dir, keys["NEBIUS_API_KEY"], started + max_hours * 3600,
                                      health_models(manifest)):
            log_event(run_dir, "stopped: provider still unhealthy at the runtime cap")
            return
        record = execute(run_dir, manifest, item, keys)
        reruns = 0
        while (reason := infra_failure(run_dir, record)) and reruns < INFRA_RERUNS:
            quarantine(run_dir, record, reason)
            reruns += 1
            if not wait_until_healthy(run_dir, keys["NEBIUS_API_KEY"], started + max_hours * 3600,
                                      health_models(manifest)):
                log_event(run_dir, "stopped: provider still unhealthy at the runtime cap")
                return
            record = execute(run_dir, manifest, item, keys)
        print(f"{item['seq']:3d} {item['task_id']:28} {item['condition']:7} "
              f"{'PASS' if record['passed'] else 'FAIL':4} ${record['cost_total_usd']:.4f} "
              f"{record['duration_s']:6.1f}s {record['termination']:13} "
              f"{record.get('auto_tier_counts') or ''} {('ANOMALY ' + '; '.join(record['anomalies'])) if record['anomalies'] else ''}",
              flush=True)
    log_event(run_dir, "run complete", spent_usd=round(sum(r["cost_total_usd"] for r in load_results(run_dir)), 4))


def status(args) -> None:
    run_dir = RUNS / args.run_id
    plan = json.loads((run_dir / "plan.json").read_text())
    results = load_results(run_dir)
    print(f"{len(results)} of {len(plan)} executions done")
    for condition in sorted({r["condition"] for r in results}):
        rows = [r for r in results if r["condition"] == condition]
        print(f"  {condition}: {sum(r['passed'] for r in rows)}/{len(rows)} passed, "
              f"${sum(r['cost_total_usd'] for r in rows):.4f}, {sum(r['duration_s'] for r in rows) / 60:.1f} min")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--run-id", required=True)
    p.add_argument("--suite", default="dataset", choices=["dataset", "smoke", "dev"])
    p.add_argument("--conditions", default="A,B")
    p.add_argument("--repetitions", type=int, default=1)
    p.add_argument("--tasks", default="")
    p.add_argument("--catalog-from", default="", help="reuse this run's frozen catalog and prices")
    r = sub.add_parser("run")
    r.add_argument("--run-id", required=True)
    r.add_argument("--budget-usd", type=float)
    r.add_argument("--max-hours", type=float)
    q = sub.add_parser("requeue-infra", help="exclude and queue for re-run any recorded infrastructure failure")
    q.add_argument("--run-id", required=True)
    s = sub.add_parser("status")
    s.add_argument("--run-id", required=True)
    sm = sub.add_parser("smoke", help="prepare and run the excluded smoke tasks")
    sm.add_argument("--run-id", default=f"smoke-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    sm.add_argument("--conditions", default="A,B")
    sm.add_argument("--budget-usd", type=float, default=3.0)
    sm.add_argument("--max-hours", type=float, default=1.0)
    sm.add_argument("--catalog-from", default="", help="reuse this run's frozen catalog and prices")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args)
    elif args.command == "run":
        run(args)
    elif args.command == "status":
        status(args)
    elif args.command == "requeue-infra":
        requeue_infra(args)
    elif args.command == "smoke":
        args.suite, args.repetitions, args.tasks = "smoke", 1, ""
        run_dir = prepare(args)
        run(args, run_dir)


if __name__ == "__main__":
    main()
