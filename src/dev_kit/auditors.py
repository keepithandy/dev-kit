"""Read-only project auditors used by the dev-kit CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

VERSION_PATTERN = re.compile(r"v\d+\.\d+\.\d+(?:[A-Za-z0-9._-]+)?")
STANDARD_RUNTIME_FILES = ("index.html", "sw.js", "app.js")
BASELINE_FILES = ("VERSION.md", *STANDARD_RUNTIME_FILES)


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


def check_baseline_files(root: Path, expected_files: Iterable[str] = BASELINE_FILES) -> list[CheckResult]:
    results: list[CheckResult] = []
    for relative_path in expected_files:
        target = root / relative_path
        if target.exists():
            results.append(CheckResult(f"file:{relative_path}", "PASS", "Found baseline file."))
        else:
            results.append(CheckResult(f"file:{relative_path}", "WARN", "Missing baseline file."))
    return results


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


def audit_project(root: str | Path) -> list[CheckResult]:
    """Run the default read-only project audit suite."""

    project_root = Path(root).expanduser().resolve()
    path_result = check_project_path(project_root)
    if path_result.failed:
        return [path_result]

    return [
        path_result,
        *check_baseline_files(project_root),
        *check_version_sync(project_root),
    ]


def summarize(results: Iterable[CheckResult]) -> dict[str, int]:
    summary = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for result in results:
        summary[result.status] = summary.get(result.status, 0) + 1
    return summary


def render_markdown(root: str | Path, results: Iterable[CheckResult]) -> str:
    result_list = list(results)
    counts = summarize(result_list)
    project_root = Path(root).expanduser().resolve()

    lines = [
        "# dev-kit Audit Report",
        "",
        f"Project: `{project_root}`",
        "",
        "## Summary",
        "",
        f"- PASS: {counts.get('PASS', 0)}",
        f"- WARN: {counts.get('WARN', 0)}",
        f"- FAIL: {counts.get('FAIL', 0)}",
        "",
        "## Checks",
        "",
    ]

    for result in result_list:
        lines.append(f"- **{result.status}** `{result.name}` - {result.detail}")

    lines.append("")
    return "\n".join(lines)
