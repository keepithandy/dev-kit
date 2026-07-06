# Portfolio Audit Mode

Portfolio audit mode scans immediate child project folders under a parent directory and creates a compact status report for each project.

This is read-only. It does not create, edit, delete, move, or rename files inside the scanned repositories.

## PowerShell

```powershell
python -m dev_kit.portfolio_cli --path .. --output .\portfolio-report.md
```

## Bash / macOS / Linux

```bash
python -m dev_kit.portfolio_cli --path .. --output ./portfolio-report.md
```

## What It Checks

For each immediate child folder that looks like a project, the portfolio helper records:

- folder name
- selected audit profile
- PASS/WARN/FAIL counts
- overall status
- one next-action line

A folder is considered project-like when it has common markers such as `.git`, `README.md`, `pyproject.toml`, `package.json`, or `index.html`.

## Intended Use

Run this from the `dev-kit` repo when your project folders are siblings, for example:

```text
Desktop/
  DungeonDex/
  depth-engine/
  guildmasters/
  dev-kit/
```

From `Desktop/dev-kit`, `--path ..` points at the parent folder containing those sibling repos.
