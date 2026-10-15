#!/usr/bin/env python3
"""Check tasks against docs/AUTHORING.md: metadata, prompt, starter fails, reference passes."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (BANNED_PROMPT_WORDS, CATEGORIES, DIFFICULTIES, LANGUAGES, MIN_ASSERTIONS,  # noqa: E402
                    PROMPT_MAX_CHARS, acceptance_files, grade, list_tasks, load_task, materialize, tool_env)

REQUIRED = ("id", "title", "category", "difficulty", "language", "prompt", "acceptance",
            "difficulty_rationale", "estimated_human_minutes")


def count_assertions(task) -> int:
    pattern = r"self\.assert\w+\(" if task.language == "python" else r"\bassert(?:\.\w+)?\("
    return sum(len(re.findall(pattern, (task.acceptance_dir / name).read_text()))
               for name in acceptance_files(task))


def visible_tests(task, workspace: Path) -> tuple[bool, str] | None:
    """Run the workspace's own tests, if it has any."""
    with tempfile.TemporaryDirectory() as home:
        if task.language == "python":
            if not (workspace / "tests").is_dir():
                return None
            cmd = ["python3", "-m", "unittest", "discover", "-s", "tests", "-t", "."]
        else:
            files = sorted(str(p.relative_to(workspace)) for p in workspace.rglob("*")
                           if re.search(r"\.test\.(mjs|js|ts|mts)$", p.name) and "node_modules" not in p.parts)
            if not files:
                return None
            cmd = ["node", "--test", *files]
        proc = subprocess.run(cmd, cwd=workspace, env=tool_env(Path(home)), capture_output=True, text=True, timeout=120)
        return proc.returncode == 0, (proc.stdout + proc.stderr)[-1500:]


def check(task) -> list[str]:
    problems = []
    meta = task.meta
    for key in REQUIRED:
        if key not in meta:
            problems.append(f"task.json is missing {key}")
    if meta.get("id") != task.id:
        problems.append(f"id {meta.get('id')!r} does not match folder {task.id!r}")
    if meta.get("category") not in CATEGORIES:
        problems.append(f"unknown category {meta.get('category')!r}")
    if meta.get("difficulty") not in DIFFICULTIES:
        problems.append(f"unknown difficulty {meta.get('difficulty')!r}")
    if meta.get("language") not in LANGUAGES:
        problems.append(f"unknown language {meta.get('language')!r}")
    prompt = meta.get("prompt", "")
    banned = sorted({m.group(0).lower() for m in BANNED_PROMPT_WORDS.finditer(prompt)})
    if banned:
        problems.append(f"prompt uses banned words: {', '.join(banned)}")
    if re.search(r"acceptance|hidden test", prompt, re.IGNORECASE):
        problems.append("prompt mentions acceptance or hidden tests")
    if len(prompt) > PROMPT_MAX_CHARS:
        problems.append(f"prompt is {len(prompt)} characters (max {PROMPT_MAX_CHARS})")
    if not task.workspace.is_dir() or not (task.workspace / "README.md").is_file():
        problems.append("workspace/README.md is missing")
    if any(p.name == "acceptance_tests" for p in task.workspace.rglob("*")):
        problems.append("workspace contains an acceptance_tests directory")
    if not task.acceptance_dir.is_dir() or not acceptance_files(task):
        problems.append("evaluator acceptance_tests are missing")
        return problems
    if task.language == "python" and not (task.acceptance_dir / "__init__.py").is_file():
        problems.append("acceptance_tests/__init__.py is missing")
    if not task.reference_dir.is_dir():
        problems.append("evaluator reference is missing")
        return problems
    minimum = MIN_ASSERTIONS.get(meta.get("difficulty"), 0)
    found = count_assertions(task)
    if found < minimum:
        problems.append(f"only {found} assertions (needs {minimum})")

    with tempfile.TemporaryDirectory() as tmp:
        start = materialize(task, Path(tmp) / "start")
        result = grade(task, start)
        if result.passed:
            problems.append("the starting workspace already passes the acceptance tests")
        elif result.tests_total in (None, 0):
            problems.append("the acceptance tests did not run on the starting workspace:\n"
                            + result.output[-800:])
        ref = materialize(task, Path(tmp) / "ref", with_reference=True)
        for attempt in (1, 2):
            result = grade(task, ref)
            if not result.passed:
                problems.append(f"reference fails (attempt {attempt}): {result.tests_failed} of "
                                f"{result.tests_total} failed\n{result.output[-1500:]}")
                break
            if result.duration_s > 30:
                problems.append(f"acceptance tests took {result.duration_s:.1f}s (max 30)")
        visible = visible_tests(task, ref)
        if visible is not None and not visible[0]:
            problems.append(f"the workspace's own tests fail with the reference:\n{visible[1]}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", default="dataset", choices=["dataset", "smoke", "dev", "abdul"])
    parser.add_argument("--task", action="append", help="task id (repeatable); default all")
    args = parser.parse_args()
    tasks = [load_task(t, args.suite) for t in args.task] if args.task else list_tasks(args.suite)
    bad = 0
    for task in tasks:
        problems = check(task)
        status = "OK" if not problems else "INVALID"
        meta = task.meta
        print(f"{status:8} {task.id:34} {meta.get('difficulty', '?'):6} {meta.get('category', '?'):10} "
              f"{meta.get('language', '?'):10} assertions={count_assertions(task) if task.acceptance_dir.is_dir() else 0}",
              flush=True)
        for problem in problems:
            print("         - " + problem.replace("\n", "\n           "))
        bad += bool(problems)
    print(f"\n{len(tasks) - bad} of {len(tasks)} tasks valid")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
