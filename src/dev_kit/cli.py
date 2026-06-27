"""Command-line interface for dev-kit."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .auditors import audit_project, available_profile_names, check_version_sync, render_markdown, resolve_audit_profile, summarize


def _print_results(results) -> None:
    counts = summarize(results)
    print(f"PASS {counts.get('PASS', 0)} | WARN {counts.get('WARN', 0)} | FAIL {counts.get('FAIL', 0)}")
    print("-" * 48)
    for result in results:
        print(f"[{result.status}] {result.name}: {result.detail}")


def _exit_code(results) -> int:
    return 1 if any(result.failed for result in results) else 0


def _profile_help() -> str:
    return f"Audit profile to use. Supported: {', '.join(available_profile_names())}."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dev-kit",
        description="Read-only project audit tooling for local repos.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit_parser = subparsers.add_parser("audit", help="Run the default project audit suite.")
    audit_parser.add_argument("--path", default=".", help="Project path to audit. Defaults to current directory.")
    audit_parser.add_argument("--profile", default="default", help=_profile_help())

    version_parser = subparsers.add_parser("version", help="Check VERSION.md against common runtime labels.")
    version_parser.add_argument("--path", default=".", help="Project path to audit. Defaults to current directory.")
    version_parser.add_argument("--profile", default="default", help=_profile_help())

    report_parser = subparsers.add_parser("report", help="Write a Markdown audit report.")
    report_parser.add_argument("--path", default=".", help="Project path to audit. Defaults to current directory.")
    report_parser.add_argument("--output", required=True, help="Markdown output path.")
    report_parser.add_argument("--profile", default="default", help=_profile_help())

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "audit":
            results = audit_project(args.path, profile=args.profile)
            _print_results(results)
            return _exit_code(results)

        if args.command == "version":
            profile = resolve_audit_profile(args.profile)
            results = check_version_sync(Path(args.path).expanduser().resolve(), profile.runtime_files)
            _print_results(results)
            return _exit_code(results)

        if args.command == "report":
            results = audit_project(args.path, profile=args.profile)
            output_path = Path(args.output).expanduser().resolve()
            output_path.write_text(render_markdown(args.path, results), encoding="utf-8")
            print(f"Wrote report: {output_path}")
            return _exit_code(results)
    except ValueError as exc:
        parser.error(str(exc))

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
