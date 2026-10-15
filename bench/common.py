"""Shared paths, task loading and grading for the benchmark.

Grading never runs inside the agent's workspace: the workspace is copied, the
hidden acceptance tests are added to the copy, and the copy is tested.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUITES = {
    "dataset": (ROOT / "dataset" / "tasks", ROOT / "evaluator"),
    "smoke": (ROOT / "smoke" / "tasks", ROOT / "smoke" / "evaluator"),
    # Tuning set for Auto v2: nconnect's own 12 routing tasks plus the smoke tasks. Never the 50.
    "dev": (ROOT / "dev" / "tasks", ROOT / "dev" / "evaluator"),
    # Abdul's 30 core tasks (amrrs/jev-router-experiment at 56b4c3b): one-shot JSON answers, a separate benchmark.
    "abdul": (ROOT / "abdul" / "tasks", ROOT / "abdul" / "evaluator"),
}
CATEGORIES = {"utility", "formatting", "parsing", "validation", "bugfix", "api-change", "feature", "refactor", "state"}
DIFFICULTIES = ("easy", "medium", "hard")
LANGUAGES = {"python", "typescript", "javascript"}
MIN_ASSERTIONS = {"easy": 5, "medium": 10, "hard": 15}
PROMPT_MAX_CHARS = 2500

# Difficulty and effort language, and phrases nconnect's Auto treats as a request
# for the strong model ("think hard", "ultrathink"). None may appear in a prompt.
BANNED_PROMPT_WORDS = re.compile(
    r"\b(trivial|simple|simply|easy|easily|quick|quickly|straightforward|hard|harder|difficult|"
    r"complex|complicated|tricky|challenging|careful|carefully|think|ultrathink|tier|model)\b|step[- ]by[- ]step",
    re.IGNORECASE,
)

GRADE_TIMEOUT_S = 120


@dataclass
class Task:
    suite: str
    id: str
    meta: dict
    task_dir: Path
    eval_dir: Path

    @property
    def workspace(self) -> Path:
        return self.task_dir / "workspace"

    @property
    def acceptance_dir(self) -> Path:
        return self.eval_dir / "acceptance_tests"

    @property
    def reference_dir(self) -> Path:
        return self.eval_dir / "reference"

    @property
    def language(self) -> str:
        return self.meta["language"]

    @property
    def prompt(self) -> str:
        return self.meta["prompt"]


def load_task(task_id: str, suite: str = "dataset") -> Task:
    tasks_dir, eval_root = SUITES[suite]
    task_dir = tasks_dir / task_id
    meta = json.loads((task_dir / "task.json").read_text())
    return Task(suite, task_id, meta, task_dir, eval_root / task_id)


def list_tasks(suite: str = "dataset") -> list[Task]:
    tasks_dir, _ = SUITES[suite]
    if not tasks_dir.is_dir():
        return []
    return [load_task(p.name, suite) for p in sorted(tasks_dir.iterdir()) if (p / "task.json").is_file()]


def copy_tree(src: Path, dest: Path) -> None:
    shutil.copytree(src, dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))


def materialize(task: Task, dest: Path, with_reference: bool = False) -> Path:
    """The starting workspace at `dest`, optionally with the reference solution applied."""
    dest.mkdir(parents=True, exist_ok=True)
    copy_tree(task.workspace, dest)
    if with_reference:
        copy_tree(task.reference_dir, dest)
        deletions = task.eval_dir / "reference.delete"
        if deletions.is_file():
            for line in deletions.read_text().splitlines():
                if line.strip():
                    (dest / line.strip()).unlink(missing_ok=True)
    return dest


def tool_env(home: Path) -> dict:
    """A minimal, fixed environment for running tests."""
    return {
        "PATH": os.environ.get("BENCH_TOOL_PATH", f"{ROOT / 'vendor' / 'bin'}:/usr/bin:/bin"),
        "HOME": str(home),
        "LANG": "en_US.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "NODE_NO_WARNINGS": "1",
        "TZ": "UTC",
    }


def acceptance_files(task: Task) -> list[str]:
    files = []
    for path in sorted(task.acceptance_dir.rglob("*")):
        if path.is_file():
            files.append(path.relative_to(task.acceptance_dir).as_posix())
    return files


def test_command(task: Task) -> list[str]:
    if task.language == "python":
        return ["python3", "-m", "unittest", "discover", "-s", "acceptance_tests", "-t", ".", "-v"]
    tests = [f"acceptance_tests/{name}" for name in acceptance_files(task)
             if re.search(r"\.test\.(mjs|js|ts|mts)$", name)]
    return ["node", "--test", "--test-reporter=tap", *tests]


@dataclass
class GradeResult:
    passed: bool
    tests_total: int | None
    tests_failed: int | None
    duration_s: float
    timed_out: bool
    exit_code: int | None
    output: str = field(repr=False)

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "tests_total": self.tests_total,
            "tests_failed": self.tests_failed,
            "duration_s": round(self.duration_s, 3),
            "timed_out": self.timed_out,
            "exit_code": self.exit_code,
        }


def _parse_counts(language: str, output: str) -> tuple[int | None, int | None]:
    if language == "python":
        ran = re.findall(r"^Ran (\d+) tests? in", output, re.MULTILINE)
        total = int(ran[-1]) if ran else None
        failed = 0
        summary = re.findall(r"^FAILED \(([^)]*)\)", output, re.MULTILINE)
        if summary:
            for part in summary[-1].split(","):
                key, _, value = part.strip().partition("=")
                if key in ("failures", "errors") and value.isdigit():
                    failed += int(value)
        return total, (failed if total is not None else None)
    tests = re.findall(r"^# tests (\d+)", output, re.MULTILINE)
    fails = re.findall(r"^# fail (\d+)", output, re.MULTILINE)
    cancelled = re.findall(r"^# cancelled (\d+)", output, re.MULTILINE)
    total = int(tests[-1]) if tests else None
    failed = (int(fails[-1]) if fails else 0) + (int(cancelled[-1]) if cancelled else 0)
    return total, (failed if total is not None else None)


def grade(task: Task, workspace: Path, keep_dir: Path | None = None) -> GradeResult:
    """Copy `workspace`, add the hidden tests, run them. `keep_dir` keeps the graded copy."""
    scratch = Path(tempfile.mkdtemp(prefix="grade-"))
    try:
        target = scratch / "ws"
        copy_tree(workspace, target)
        shutil.rmtree(target / "acceptance_tests", ignore_errors=True)
        copy_tree(task.acceptance_dir, target / "acceptance_tests")
        home = scratch / "home"
        home.mkdir()
        started = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run(test_command(task), cwd=target, env=tool_env(home), capture_output=True,
                                  text=True, timeout=GRADE_TIMEOUT_S)
            output = proc.stdout + "\n" + proc.stderr
            code = proc.returncode
        except subprocess.TimeoutExpired as err:
            timed_out = True
            output = (err.stdout or b"").decode(errors="replace") if isinstance(err.stdout, bytes) else (err.stdout or "")
            code = None
        duration = time.monotonic() - started
        total, failed = _parse_counts(task.language, output)
        passed = (code == 0 and not timed_out and total is not None and total > 0 and failed == 0)
        if keep_dir is not None:
            copy_tree(target, keep_dir)
        return GradeResult(passed, total, failed, duration, timed_out, code, output)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_digest(paths: list[Path], base: Path) -> dict[str, str]:
    """sha256 of every file under `paths`, keyed by path relative to `base`."""
    digest = {}
    for root in paths:
        if root.is_file():
            digest[root.relative_to(base).as_posix()] = sha256_file(root)
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.name != ".DS_Store":
                digest[path.relative_to(base).as_posix()] = sha256_file(path)
    return digest
