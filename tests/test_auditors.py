from pathlib import Path
import contextlib
import io
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dev_kit.auditors import audit_project, check_version_sync, extract_version_labels, render_markdown, summarize
from dev_kit.cli import main as cli_main

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"


def fixture_path(name: str) -> Path:
    return FIXTURE_ROOT / name


def snapshot_fixture(root: Path) -> dict[Path, str]:
    return {
        path.relative_to(root): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class AuditorTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = cli_main(list(args))
        return exit_code, output.getvalue()

    def test_extract_version_labels_keeps_unique_order(self):
        text = "v1.2.3, v1.2.3, v1.2.4"
        self.assertEqual(extract_version_labels(text), ["v1.2.3", "v1.2.4"])

    def test_clean_fixture_audit_passes_without_failures(self):
        root = fixture_path("clean_project")
        before = snapshot_fixture(root)

        results = audit_project(root)
        counts = summarize(results)

        self.assertEqual(counts["FAIL"], 0, "clean_project audit should not produce FAIL results")
        self.assertEqual(counts["WARN"], 0, "clean_project audit should not produce WARN results")
        self.assertEqual(snapshot_fixture(root), before, "clean_project fixture files should not be modified")

    def test_missing_file_fixture_audit_warns_without_failures(self):
        root = fixture_path("missing_file_project")
        before = snapshot_fixture(root)

        results = audit_project(root)
        counts = summarize(results)
        warnings = [result for result in results if result.status == "WARN"]

        self.assertEqual(counts["FAIL"], 0, "missing_file_project should warn, not fail")
        self.assertTrue(
            any(result.name == "file:app.js" for result in warnings),
            "missing_file_project should explain that app.js is missing",
        )
        self.assertTrue(
            any(result.name == "version:app.js" for result in warnings),
            "missing_file_project should explain that app.js version check was skipped",
        )
        self.assertEqual(snapshot_fixture(root), before, "missing_file_project fixture files should not be modified")

    def test_mismatched_fixture_version_fails_with_clear_message(self):
        root = fixture_path("mismatched_version_project")
        before = snapshot_fixture(root)

        results = check_version_sync(root)
        failures = [result for result in results if result.failed]

        self.assertEqual(len(failures), 1, "mismatched_version_project should produce one version failure")
        self.assertEqual(failures[0].name, "version:app.js", "mismatched_version_project failure should identify app.js")
        self.assertIn("Expected v0.1.0", failures[0].detail)
        self.assertIn("v0.2.0", failures[0].detail)
        self.assertEqual(snapshot_fixture(root), before, "mismatched_version_project fixture files should not be modified")

    def test_audit_cli_uses_clean_fixture(self):
        exit_code, output = self.run_cli("audit", "--path", str(fixture_path("clean_project")))

        self.assertEqual(exit_code, 0, f"audit CLI should pass for clean_project. Output:\n{output}")
        self.assertIn("FAIL 0", output)
        self.assertIn("[PASS] project path", output)

    def test_version_cli_uses_mismatched_fixture(self):
        exit_code, output = self.run_cli("version", "--path", str(fixture_path("mismatched_version_project")))

        self.assertEqual(exit_code, 1, f"version CLI should fail for mismatched_version_project. Output:\n{output}")
        self.assertIn("[FAIL] version:app.js", output)
        self.assertIn("Expected v0.1.0", output)

    def test_report_cli_writes_requested_file_without_touching_fixture(self):
        root = fixture_path("clean_project")
        before = snapshot_fixture(root)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "devkit-report.md"
            exit_code, output = self.run_cli("report", "--path", str(root), "--output", str(output_path))
            report = output_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0, f"report CLI should pass for clean_project. Output:\n{output}")
        self.assertIn("Wrote report:", output)
        self.assertIn("# dev-kit Audit Report", report)
        self.assertIn("- FAIL: 0", report)
        self.assertEqual(snapshot_fixture(root), before, "report CLI should not modify clean_project fixture files")

    def test_render_markdown_summary_from_clean_fixture(self):
        root = fixture_path("clean_project")
        results = audit_project(root)
        counts = summarize(results)
        report = render_markdown(root, results)

        self.assertGreaterEqual(counts["PASS"], 1)
        self.assertIn("# dev-kit Audit Report", report)
        self.assertIn("## Checks", report)


if __name__ == "__main__":
    unittest.main()
