"""Read-only project auditors used by the dev-kit CLI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Iterable

VERSION_PATTERN = re.compile(r"v\d+\.\d+\.\d+(?:[A-Za-z0-9._-]+)?")
STANDARD_RUNTIME_FILES = ("index.html", "sw.js", "app.js")
BASELINE_FILES = ("VERSION.md", *STANDARD_RUNTIME_FILES)


@dataclass(frozen=True)
class AuditProfile:
    """Named read-only audit profile for a project type."""

    name: str
    description: str
    baseline_files: tuple[str, ...]
    runtime_files: tuple[str, ...] = STANDARD_RUNTIME_FILES
    smoke_patterns: tuple[str, ...] = ()


AUDIT_PROFILES: dict[str, AuditProfile] = {
    "default": AuditProfile(
        name="default",
        description="General static project audit.",
        baseline_files=BASELINE_FILES,
    ),
    "browser-game-static": AuditProfile(
        name="browser-game-static",
        description="Static browser-game audit for HTML/CSS/JS projects with release labels and smoke scripts.",
        baseline_files=(
            "VERSION.md",
            "README.md",
            "CHANGELOG.md",
            "index.html",
            "app.js",
            "sw.js",
        ),
        smoke_patterns=("smoke*.mjs",),
    ),
}

PROFILE_ALIASES = {
    "dungeondex": "browser-game-static",
}


@dataclass(frozen=True)
class CheckResult:
    """A single read-only audit result."""

    name: str
    status: str
    detail: str

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_version_labels(text: str) -> list[str]:
    """Return unique version-looking labels in first-seen order."""

    labels: list[str] = []
    for match in VERSION_PATTERN.findall(text):
        if match not in labels:
            labels.append(match)
    return labels


def available_profile_names() -> tuple[str, ...]:
    """Return supported audit profile names, including aliases."""

    return tuple(sorted((*AUDIT_PROFILES.keys(), *PROFILE_ALIASES.keys())))


def resolve_audit_profile(profile_name: str = "default") -> AuditProfile:
    """Resolve a profile name or alias into an audit profile."""

    canonical_name = PROFILE_ALIASES.get(profile_name, profile_name)
    try:
        return AUDIT_PROFILES[canonical_name]
    except KeyError as exc:
        supported = ", ".join(available_profile_names())
        raise ValueError(f"Unknown audit profile '{profile_name}'. Supported profiles: {supported}.") from exc


def canonical_version(root: Path) -> str | None:
    """Read the first version-looking label from VERSION.md, if present."""

    version_file = root / "VERSION.md"
    if not version_file.exists():
        return None
    labels = extract_version_labels(_read_text(version_file))
    return labels[0] if labels else None


def check_project_path(root: Path) -> CheckResult:
    if root.exists() and root.is_dir():
        return CheckResult("project path", "PASS", f"Found project directory: {root}")
    return CheckResult("project path", "FAIL", f"Project directory does not exist: {root}")


def check_profile(profile: AuditProfile) -> CheckResult:
    return CheckResult(
        "audit profile",
        "PASS",
        f"Using '{profile.name}' profile: {profile.description}",
    )


def check_baseline_files(root: Path, expected_files: Iterable[str] = BASELINE_FILES) -> list[CheckResult]:
    results: list[CheckResult] = []
    for relative_path in expected_files:
        target = root / relative_path
        if target.exists():
            results.append(CheckResult(f"file:{relative_path}", "PASS", "Found baseline file."))
        else:
            results.append(CheckResult(f"file:{relative_path}", "WARN", "Missing baseline file."))
    return results


def check_smoke_files(root: Path, patterns: Iterable[str]) -> list[CheckResult]:
    pattern_list = tuple(patterns)
    if not pattern_list:
        return []

    matches: list[Path] = []
    for pattern in pattern_list:
        matches.extend(path for path in root.glob(pattern) if path.is_file())

    unique_matches = sorted({path.relative_to(root).as_posix() for path in matches})
    if unique_matches:
        found = ", ".join(unique_matches[:5])
        extra_count = len(unique_matches) - 5
        if extra_count > 0:
            found = f"{found}, +{extra_count} more"
        return [CheckResult("profile:smoke scripts", "PASS", f"Found smoke script(s): {found}.")]

    pattern_text = ", ".join(pattern_list)
    return [CheckResult("profile:smoke scripts", "WARN", f"No smoke scripts matched: {pattern_text}.")]


def check_version_sync(root: Path, runtime_files: Iterable[str] = STANDARD_RUNTIME_FILES) -> list[CheckResult]:
    version = canonical_version(root)
    if version is None:
        return [CheckResult("version:canonical", "FAIL", "VERSION.md is missing or has no v#.#.# label.")]

    results = [CheckResult("version:canonical", "PASS", f"Canonical version is {version}.")]

    for relative_path in runtime_files:
        target = root / relative_path
        if not target.exists():
            results.append(CheckResult(f"version:{relative_path}", "WARN", "File missing; skipped version-label check."))
            continue

        labels = extract_version_labels(_read_text(target))
        if not labels:
            results.append(CheckResult(f"version:{relative_path}", "WARN", "No version labels found."))
        elif labels == [version]:
            results.append(CheckResult(f"version:{relative_path}", "PASS", f"Only references {version}."))
        elif version in labels:
            extras = ", ".join(label for label in labels if label != version)
            results.append(CheckResult(f"version:{relative_path}", "FAIL", f"Contains {version}, but also conflicting labels: {extras}."))
        else:
            found = ", ".join(labels)
            results.append(CheckResult(f"version:{relative_path}", "FAIL", f"Expected {version}; found {found}."))

    return results


def audit_project(root: str | Path, profile: str = "default") -> list[CheckResult]:
    """Run a read-only project audit suite."""

    project_root = Path(root).expanduser().resolve()
    path_result = check_project_path(project_root)
    if path_result.failed:
        return [path_result]

    audit_profile = resolve_audit_profile(profile)

    return [
        path_result,
        check_profile(audit_profile),
        *check_baseline_files(project_root, audit_profile.baseline_files),
        *check_smoke_files(project_root, audit_profile.smoke_patterns),
        *check_version_sync(project_root, audit_profile.runtime_files),
    ]


def summarize(results: Iterable[CheckResult]) -> dict[str, int]:
    summary = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for result in results:
        summary[result.status] = summary.get(result.status, 0) + 1
    return summary


def _result_group(result: CheckResult) -> str:
    if result.name == "project path":
        return "Project"
    if result.name == "audit profile":
        return "Audit profile"
    if result.name.startswith("file:"):
        return "Baseline files"
    if result.name.startswith("version:"):
        return "Version labels"
    if result.name.startswith("profile:"):
        return "Profile checks"
    return "Other checks"


def summarize_by_group(results: Iterable[CheckResult]) -> dict[str, dict[str, int]]:
    """Return PASS/WARN/FAIL counts grouped by audit area."""

    grouped: dict[str, dict[str, int]] = {}
    for result in results:
        group = _result_group(result)
        grouped.setdefault(group, {"PASS": 0, "WARN": 0, "FAIL": 0})
        grouped[group][result.status] = grouped[group].get(result.status, 0) + 1
    return grouped


def _overall_status(counts: dict[str, int]) -> str:
    if counts.get("FAIL", 0):
        return "FAIL"
    if counts.get("WARN", 0):
        return "WARN"
    return "PASS"


def _format_generated_at(generated_at: datetime | str | None) -> str:
    if generated_at is None:
        generated_at = datetime.now(timezone.utc)
    if isinstance(generated_at, datetime):
        return generated_at.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return generated_at


def _section_results(results: Iterable[CheckResult], prefix: str) -> list[CheckResult]:
    return [result for result in results if result.name.startswith(prefix)]


def _next_actions(results: list[CheckResult]) -> list[str]:
    actions: list[str] = []
    failures = [result for result in results if result.status == "FAIL"]
    warnings = [result for result in results if result.status == "WARN"]

    if not failures and not warnings:
        return ["No action required. The audit completed without warnings or failures."]

    if any(result.name.startswith("version:") for result in failures):
        actions.append("Align mismatched version labels before release.")

    if any(result.name.startswith("file:") for result in warnings):
        actions.append("Review missing baseline files and decide whether they should be added or documented as intentionally absent.")

    if any(result.name == "profile:smoke scripts" for result in warnings):
        actions.append("Add or restore at least one root-level smoke script if this project should have a smoke-test safety net.")

    if failures and not actions:
        actions.append("Fix failing checks before treating this project as release-ready.")

    if warnings and not actions:
        actions.append("Review warning checks before release; warnings may be acceptable if they are intentional.")

    return actions


def render_markdown(
    root: str | Path,
    results: Iterable[CheckResult],
    generated_at: datetime | str | None = None,
) -> str:
    result_list = list(results)
    counts = summarize(result_list)
    grouped_counts = summarize_by_group(result_list)
    project_root = Path(root).expanduser().resolve()
    status = _overall_status(counts)

    lines = [
        "# dev-kit Audit Report",
        "",
        f"- Project: `{project_root}`",
        f"- Generated: `{_format_generated_at(generated_at)}`",
        f"- Overall status: **{status}**",
        "",
        "## Summary",
        "",
        f"- PASS: {counts.get('PASS', 0)}",
        f"- WARN: {counts.get('WARN', 0)}",
        f"- FAIL: {counts.get('FAIL', 0)}",
        "",
        "## Audit Groups",
        "",
    ]

    for group, group_counts in grouped_counts.items():
        lines.append(
            f"- **{group}**: PASS {group_counts.get('PASS', 0)} | "
            f"WARN {group_counts.get('WARN', 0)} | FAIL {group_counts.get('FAIL', 0)}"
        )

    version_results = _section_results(result_list, "version:")
    if version_results:
        lines.extend(["", "## Version-label Checks", ""])
        for result in version_results:
            lines.append(f"- **{result.status}** `{result.name}` - {result.detail}")

    baseline_results = _section_results(result_list, "file:")
    if baseline_results:
        lines.extend(["", "## Baseline File Checks", ""])
        for result in baseline_results:
            lines.append(f"- **{result.status}** `{result.name}` - {result.detail}")

    lines.extend(["", "## Warnings and Next Actions", ""])
    for action in _next_actions(result_list):
        lines.append(f"- {action}")

    lines.extend(["", "## All Checks", ""])
    for result in result_list:
        lines.append(f"- **{result.status}** `{result.name}` - {result.detail}")

    lines.append("")
    return "\n".join(lines)
