"""Command line: python3 -m reports.cli [--format NAME] [--output FILE] REPORT.json"""

import argparse
import sys

from .exporters import format_names, get_exporter
from .model import load_report


def build_parser():
    parser = argparse.ArgumentParser(prog="reports")
    parser.add_argument("report", nargs="?", help="report JSON file")
    parser.add_argument("--format", default="text", choices=format_names())
    parser.add_argument("--output", help="write to this file instead of stdout")
    parser.add_argument("--list-formats", action="store_true", help="print the available formats and exit")
    return parser


def main(argv=None, stdout=None):
    stdout = stdout or sys.stdout
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return exit_.code
    if args.list_formats:
        for name in format_names():
            stdout.write(name + "\n")
        return 0
    if not args.report:
        parser.print_usage(sys.stderr)
        return 2
    output = get_exporter(args.format).export(load_report(args.report))
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as handle:
            handle.write(output)
    else:
        stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
