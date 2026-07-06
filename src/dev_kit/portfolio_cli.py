"""Standalone portfolio audit command for dev-kit."""

from __future__ import annotations

import argparse
from pathlib import Path

from .portfolio import audit_portfolio, render_portfolio_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit immediate child project folders.")
    parser.add_argument("--path", default=".", help="Parent folder containing sibling repos.")
    parser.add_argument("--output", help="Optional Markdown output path.")
    args = parser.parse_args(argv)

    parent = Path(args.path).expanduser().resolve()
    if not parent.exists() or not parent.is_dir():
        print(f"ERROR: Parent folder does not exist or is not a directory: {parent}")
        return 2

    summaries = audit_portfolio(parent)
    print(f"Projects found: {len(summaries)}")
    print("-" * 72)
    for summary in summaries:
        print(
            f"[{summary.status}] {summary.name} ({summary.profile}) "
            f"PASS {summary.pass_count} | WARN {summary.warn_count} | FAIL {summary.fail_count}"
        )
        print(f"  Next: {summary.next_action}")

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.write_text(render_portfolio_markdown(parent, summaries), encoding="utf-8")
        print(f"Wrote portfolio report: {output_path}")

    return 1 if any(summary.fail_count for summary in summaries) else 0


if __name__ == "__main__":
    raise SystemExit(main())
