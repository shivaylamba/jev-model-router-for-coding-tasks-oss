"""Strict and lenient scores for the Abdul suite.

Strict is the hidden test: answer.json must equal Abdul's gold answer under his
equal() rule. Lenient also accepts a run that wrote no correct answer.json but
gave the correct JSON in its final message. It was added after seeing that
Kimi K3 often printed the answer instead of writing the file, and applies to
both conditions alike.

Usage: python3 bench/abdul_lenient.py [--run-id abdul]
Writes reports/<run-id>/lenient.json and prints a summary.
"""
import argparse
import gzip
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_test(task_id: str):
    path = ROOT / "abdul" / "evaluator" / task_id / "acceptance_tests" / "test_answer.py"
    spec = importlib.util.spec_from_file_location(f"t_{task_id.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.equal, module.EXPECTED


def final_text(execution: Path) -> str:
    text = ""
    with gzip.open(execution / "claude-transcript.jsonl.gz", "rt") as fh:
        for line in fh:
            entry = json.loads(line)
            message = entry.get("message")
            if not isinstance(message, dict) or message.get("role") != "assistant":
                continue
            parts = [c.get("text", "") for c in message.get("content", []) if c.get("type") == "text"]
            if any(parts):
                text = "\n".join(parts)
    return text


def json_candidates(text: str):
    """Every JSON object in the text: fenced blocks first, then bare {...} spans."""
    blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    decoder = json.JSONDecoder()
    for start in [m.start() for m in re.finditer(r"\{", text)]:
        try:
            obj, _ = decoder.raw_decode(text[start:])
            blocks.append(json.dumps(obj))
        except ValueError:
            continue
    for block in blocks:
        try:
            yield json.loads(block)
        except ValueError:
            continue


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="abdul")
    args = parser.parse_args()
    run = ROOT / "runs" / args.run_id
    rows = []
    for execution in sorted((run / "executions").iterdir()):
        meta = json.loads((execution / "meta.json").read_text())
        strict = json.loads((execution / "grade.json").read_text()).get("passed") is True
        equal, expected = load_test(meta["task_id"])
        in_message = any(equal(obj, expected) for obj in json_candidates(final_text(execution)))
        rows.append({
            "execution": execution.name,
            "task_id": meta["task_id"],
            "condition": meta["condition"],
            "strict": strict,
            "lenient": strict or in_message,
        })
    summary = {}
    for condition in sorted({r["condition"] for r in rows}):
        mine = [r for r in rows if r["condition"] == condition]
        summary[condition] = {
            "tasks": len(mine),
            "strict_passed": sum(r["strict"] for r in mine),
            "lenient_passed": sum(r["lenient"] for r in mine),
        }
    out = ROOT / "reports" / args.run_id / "lenient.json"
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2) + "\n")
    for condition, s in summary.items():
        print(f"{condition}: strict {s['strict_passed']}/{s['tasks']}, lenient {s['lenient_passed']}/{s['tasks']}")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
