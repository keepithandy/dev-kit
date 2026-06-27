"""Command-line interface for dev-kit."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from .auditors import audit_project, available_profile_names, check_version_sync, render_markdown, resolve_audit_profile, summarize

EXIT_SUCCESS = 0
EXIT_AUDIT_FAILURE = 1
EXIT_USAGE_ERROR = 2
EXIT_RUNTIME_ERROR = 3


class DevKitCliError(Exception):
    """Friendly CLI error with a stable exit code."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def _print_results(results) -> None:
    counts = summarize(results)
    print(f"PASS {counts.get('PASS', 0)} | WARN {counts.get('WARN', 0)} | FAIL {counts.get('FAIL', 0)}")
    print("-" * 48)
    for result in results:
        print(f"[{result.status}] {result.name}: {result.detail}")


def _print_error(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def _exit_code(results) -> int:
    return EXIT_AUDIT_FAILURE if any(result.failed for result in results) else EXIT_SUCCESS


def _profile_help() -> str:
    return f"Audit profile to use. Supported: {', '.join(available_profile_names())}."


def _resolve_path(path_value: str) -> Path:
    try:
        return Path(path_value).expanduser().resolve()
    except OSError as exc:
        raise DevKitCliError(f"Could not resolve path '{path_value}': {exc}", EXIT_USAGE_ERROR) from exc


def _validate_project_path(path_value: str) -> Path:
    project_path = _resolve_path(path_value)

    try:
        if not project_path.exists():
            raise DevKitCliError(f"Project path does not exist: {project_path}", EXIT_USAGE_ERROR)
        if not project_path.is_dir():
            raise DevKitCliError(f"Project path is not a directory: {project_path}", EXIT_USAGE_ERROR)
        if not os.access(project_path, os.R_OK):
            raise DevKitCliError(f"Project path is not readable: {project_path}", EXIT_USAGE_ERROR)
    except OSError as exc:
        raise DevKitCliError(f"Could not inspect project path '{project_path}': {exc}", EXIT_USAGE_ERROR) from exc

    return project_path


def _validate_output_path(path_value: str) -> Path:
    output_path = _resolve_path(path_value)
    parent = output_path.parent

    try:
        if not parent.exists():
            raise DevKitCliError(f"Output directory does not exist: {parent}", EXIT_USAGE_ERROR)
        if not parent.is_dir():
            raise DevKitCliError(f"Output parent is not a directory: {parent}", EXIT_USAGE_ERROR)
        if not os.access(parent, os.W_OK):
            raise DevKitCliError(f"Output directory is not writable: {parent}", EXIT_RUNTIME_ERROR)
    except OSError as exc:
        raise DevKitCliError(f"Could not inspect output path '{output_path}': {exc}", EXIT_RUNTIME_ERROR) from exc

    return output_path


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
            project_path = _validate_project_path(args.path)
            results = audit_project(project_path, profile=args.profile)
            _print_results(results)
            return _exit_code(results)

        if args.command == "version":
            project_path = _validate_project_path(args.path)
            profile = resolve_audit_profile(args.profile)
            results = check_version_sync(project_path, profile.runtime_files)
            _print_results(results)
            return _exit_code(results)

        if args.command == "report":
            project_path = _validate_project_path(args.path)
            output_path = _validate_output_path(args.output)
            results = audit_project(project_path, profile=args.profile)
            output_path.write_text(render_markdown(project_path, results), encoding="utf-8")
            print(f"Wrote report: {output_path}")
            return _exit_code(results)
    except DevKitCliError as exc:
        _print_error(str(exc))
        return exc.exit_code
    except ValueError as exc:
        _print_error(str(exc))
        return EXIT_USAGE_ERROR
    except OSError as exc:
        _print_error(f"File-system error: {exc}")
        return EXIT_RUNTIME_ERROR
    except Exception as exc:  # pragma: no cover - final guardrail for CLI users.
        _print_error(f"Unexpected runtime error: {exc}")
        return EXIT_RUNTIME_ERROR

    _print_error(f"Unknown command: {args.command}")
    return EXIT_USAGE_ERROR


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
