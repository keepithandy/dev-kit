from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dev_kit.portfolio import audit_portfolio, render_portfolio_markdown


class PortfolioAuditTests(unittest.TestCase):
    def test_portfolio_audit_finds_child_projects_without_mutating_them(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            project = parent / "sample_project"
            ignored = parent / "notes_only"
            project.mkdir()
            ignored.mkdir()

            readme = project / "README.md"
            readme.write_text("# Sample Project\n", encoding="utf-8")
            before = readme.read_text(encoding="utf-8")

            summaries = audit_portfolio(parent)

            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0].name, "sample_project")
            self.assertEqual(readme.read_text(encoding="utf-8"), before)

    def test_portfolio_markdown_renders_summary_table(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            project = parent / "sample_project"
            project.mkdir()
            (project / "README.md").write_text("# Sample Project\n", encoding="utf-8")

            summaries = audit_portfolio(parent)
            report = render_portfolio_markdown(parent, summaries)

            self.assertIn("# dev-kit Portfolio Audit Report", report)
            self.assertIn("sample_project", report)
            self.assertIn("| Repo | Profile | Status |", report)


if __name__ == "__main__":
    unittest.main()
