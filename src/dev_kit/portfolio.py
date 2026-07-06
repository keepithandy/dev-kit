"""Read-only portfolio audit helpers for sibling repository folders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .auditors import audit_project, summarize

PROJECT_MARKERS = (
    ".git",
    "README.md",
    "pyproject.toml",
    "package.json",
    "index.html",
)


@dataclass(frozen=True)
class PortfolioRepoSummary:
    """Compact audit summary for one child project folder."""

    name: str
    path: Path
    profile: str
    status: str
    pass_count: int
    warn_count: int
    fail_count: int
    next_action: str


def looks_like_project(path: Path) -> bool:
    """Return True when a child folder looks like a project/repository."""
    if not path.is_dir() or path.name.startswith("."):
        return False
    return any((path / marker).exists() for marker in PROJECT_MARKERS)


def choose_profile(path: Path) -> str:
    """Pick a conservative audit profile for a local project folder."""
    if (path / "index.html").exists() and any(path.glob("smoke*.mjs")):
        return "browser-game-static"
    return "default"


def _status_from_counts(counts: dict[str, int]) -> str:
    if counts.get("FAIL", 0):
        return "FAIL"
    if counts.get("WARN", 0):
        return "WARN"
    return "PASS"


def _next_action_from_results(results) -> str:
    failures = [result for result in results if result.status == "FAIL"]
    warnings = [result for result in results if result.status == "WARN"]

    if failures:
        return failures[0].detail
    if warnings:
        return warnings[0].detail
    return "No action required."


def audit_portfolio(parent: str | Path) -> list[PortfolioRepoSummary]:
    """Audit immediate child project folders under a parent directory.

    This function is read-only. It does not create, update, delete, or move files.
    """
    parent_path = Path(parent).expanduser().resolve()
    summaries: list[PortfolioRepoSummary] = []

    for child in sorted(parent_path.iterdir(), key=lambda item: item.name.lower()):
        if not looks_like_project(child):
            continue

        profile = choose_profile(child)
        results = audit_project(child, profile=profile)
        counts = summarize(results)
        summaries.append(
            PortfolioRepoSummary(
                name=child.name,
                path=child,
                profile=profile,
                status=_status_from_counts(counts),
                pass_count=counts.get("PASS", 0),
                warn_count=counts.get("WARN", 0),
                fail_count=counts.get("FAIL", 0),
                next_action=_next_action_from_results(results),
            )
        )

    return summaries


def render_portfolio_markdown(parent: str | Path, summaries: list[PortfolioRepoSummary]) -> str:
    """Render a Markdown portfolio audit report."""
    parent_path = Path(parent).expanduser().resolve()
    lines = [
        "# dev-kit Portfolio Audit Report",
        "",
        f"- Parent folder: `{parent_path}`",
        f"- Projects found: {len(summaries)}",
        "",
        "| Repo | Profile | Status | PASS | WARN | FAIL | Next action |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]

    for summary in summaries:
        next_action = summary.next_action.replace("|", "\\|")
        lines.append(
            f"| `{summary.name}` | `{summary.profile}` | **{summary.status}** | "
            f"{summary.pass_count} | {summary.warn_count} | {summary.fail_count} | {next_action} |"
        )

    lines.append("")
    return "\n".join(lines)
