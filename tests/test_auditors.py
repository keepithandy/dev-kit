from pathlib import Path
import tempfile
import unittest

from dev_kit.auditors import audit_project, check_version_sync, extract_version_labels, render_markdown, summarize


class AuditorTests(unittest.TestCase):
    def test_extract_version_labels_keeps_unique_order(self):
        text = "v1.2.3, v1.2.3, v1.2.4"
        self.assertEqual(extract_version_labels(text), ["v1.2.3", "v1.2.4"])

    def test_matching_runtime_versions_pass(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "VERSION.md").write_text("v1.20.40\n", encoding="utf-8")
            (root / "index.html").write_text("<title>DungeonDex v1.20.40</title>", encoding="utf-8")
            (root / "sw.js").write_text("const CACHE = 'dungeondex-v1.20.40';", encoding="utf-8")
            (root / "app.js").write_text("window.APP_VERSION = 'v1.20.40';", encoding="utf-8")

            results = check_version_sync(root)
            self.assertFalse(any(result.failed for result in results))

    def test_mismatched_runtime_version_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "VERSION.md").write_text("v1.20.40\n", encoding="utf-8")
            (root / "index.html").write_text("DungeonDex v1.20.36", encoding="utf-8")
            (root / "sw.js").write_text("DungeonDex v1.20.40", encoding="utf-8")
            (root / "app.js").write_text("DungeonDex v1.20.40", encoding="utf-8")

            results = check_version_sync(root)
            failures = [result for result in results if result.failed]
            self.assertEqual(len(failures), 1)
            self.assertIn("Expected v1.20.40", failures[0].detail)

    def test_audit_and_markdown_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "VERSION.md").write_text("v0.1.0", encoding="utf-8")
            (root / "index.html").write_text("v0.1.0", encoding="utf-8")
            (root / "sw.js").write_text("v0.1.0", encoding="utf-8")
            (root / "app.js").write_text("v0.1.0", encoding="utf-8")

            results = audit_project(root)
            counts = summarize(results)
            report = render_markdown(root, results)

            self.assertGreaterEqual(counts["PASS"], 1)
            self.assertIn("# dev-kit Audit Report", report)
            self.assertIn("## Checks", report)


if __name__ == "__main__":
    unittest.main()
