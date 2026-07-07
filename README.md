# dev-kit

A Python command-line toolkit for read-only project audits and release hygiene.

`dev-kit` helps check whether a local project is ready to ship by inspecting the files that usually drift during release work: version labels, baseline docs, browser entry files, service worker labels, smoke scripts, and generated audit reports. It is built as reusable developer tooling, not a one-off DungeonDex helper.

## Try It First

From the `dev-kit` repo folder, install in editable mode and run a DungeonDex-style audit:

```powershell
python -m pip install -e .
python -m dev_kit audit --path ..\DungeonDex --profile dungeondex
```

Generate a Markdown report:

```powershell
python -m dev_kit report --path ..\DungeonDex --profile dungeondex --output .\devkit-report.md
```

Run the test suite:

```powershell
python -m unittest discover -s tests
```

Current status: active tooling repo. The current CLI supports `audit`, `version`, and `report`. Portfolio-wide sibling-repo audit mode is still planned, not implemented.

## What it audits

`dev-kit` currently focuses on practical release-hygiene checks:

- whether expected baseline files are present
- whether `VERSION.md` agrees with runtime/public version labels
- whether a static browser-game project has a smoke-test safety net
- whether a Markdown report can be generated for issue notes, release notes, or project notes

This is useful for DungeonDex now, but the same pattern can support other local repos later, such as NovaDeck, Depth Engine, Guildmasters, or future toolkit projects.

## Goal

Build a small non-JavaScript tooling repo that can support real project work across multiple repositories. The first target is DungeonDex-style repo hygiene: version-label checks, baseline file checks, and Markdown audit reports.

## Safety model

`dev-kit` is designed to inspect local project folders, not rewrite them. This is intentional: the tool should be safe to run before a release without risking gameplay, app behavior, or repo files.

- `audit` reads the target project and prints audit results.
- `version` reads `VERSION.md` and common runtime label files, then reports whether they match.
- `report` reads the target project and writes only the Markdown file you choose with `--output`.

If you place the report output inside the audited project, that report file is the only file `dev-kit` should create or overwrite.

## Quick start: Windows PowerShell

Run these commands from the `dev-kit` repo folder:

```powershell
python -m pip install -e .
python -m dev_kit audit --path ..\DungeonDex
python -m dev_kit audit --path ..\DungeonDex --profile dungeondex
python -m dev_kit version --path ..\DungeonDex
python -m dev_kit report --path ..\DungeonDex --profile dungeondex --output .\devkit-report.md
python -m unittest discover -s tests
```

PowerShell path notes:

- `..\DungeonDex` means "the `DungeonDex` folder next to this `dev-kit` folder."
- `.\devkit-report.md` means "write the report file in the current `dev-kit` folder."
- Use quotes when a folder path contains spaces, for example `--path "..\My Game Repo"`.

## Quick start: bash / macOS / Linux

Run these commands from the `dev-kit` repo folder:

```bash
python -m pip install -e .
python -m dev_kit audit --path ../DungeonDex
python -m dev_kit audit --path ../DungeonDex --profile dungeondex
python -m dev_kit version --path ../DungeonDex
python -m dev_kit report --path ../DungeonDex --profile dungeondex --output ./devkit-report.md
python -m unittest discover -s tests
```

Bash path notes:

- `../DungeonDex` means "the `DungeonDex` folder next to this `dev-kit` folder."
- `./devkit-report.md` means "write the report file in the current `dev-kit` folder."
- Use quotes when a folder path contains spaces, for example `--path "../My Game Repo"`.

## Editable install

`python -m pip install -e .` installs `dev-kit` in editable mode. That means Python points to this local checkout instead of copying the package somewhere else.

Editable mode is useful while developing because README examples, CLI changes, and tests can use the current repo files immediately.

After the editable install, both styles are available:

```powershell
python -m dev_kit audit --path ..\DungeonDex
dev-kit audit --path ..\DungeonDex
```

The `python -m dev_kit ...` style is used throughout this README because it works clearly across PowerShell, bash, and fresh Python environments.

## Commands

- `audit`: run the default read-only audit suite.
- `version`: compare `VERSION.md` with runtime files.
- `report`: write a Markdown audit report to the exact file path passed with `--output`.

## Audit profiles

Profiles let `dev-kit` run checks for a specific kind of project while staying generic and read-only.

Available profiles:

| Profile | Purpose |
| --- | --- |
| `default` | General static project audit. Checks `VERSION.md`, `index.html`, `sw.js`, and `app.js`. |
| `browser-game-static` | Static browser-game audit for HTML/CSS/JS projects with release labels, documentation files, and smoke scripts. |
| `dungeondex` | Alias for `browser-game-static`, kept copy-friendly for DungeonDex-style projects. |

For DungeonDex-style browser projects, use:

```powershell
python -m dev_kit audit --path ..\DungeonDex --profile dungeondex
```

The `browser-game-static` / `dungeondex` profile checks for:

- `VERSION.md`
- `README.md`
- `CHANGELOG.md`
- `index.html`
- `app.js`
- `sw.js`
- at least one root-level `smoke*.mjs` script

The profile also keeps version-label checks read-only and compares `VERSION.md` against common runtime label files.

## How this supports a portfolio

`dev-kit` is meant to become the lightweight quality gate for a group of small projects. Instead of remembering release checks by hand for every repo, each project can get a profile and a repeatable command.

Current path:

1. Use the `dungeondex` profile for DungeonDex release hygiene.
2. Keep the default profile generic for smaller static projects.
3. Add future profiles only when another repo has a real repeated audit need.
4. Keep the tool focused on audit, report, and release hygiene instead of broad automation.

## Exit codes

`dev-kit` uses stable exit codes so PowerShell, scripts, and future CI jobs can tell the difference between an audit result and a command problem.

| Code | Meaning |
| --- | --- |
| `0` | Command completed and no failing audit checks were found. |
| `1` | Command completed, but at least one audit check failed. |
| `2` | Usage or input error, such as an invalid `--path`, unknown profile, missing output directory, or bad command arguments. |
| `3` | Runtime or file-system error, such as being unable to write the requested report file. |

Friendly CLI errors are printed as `ERROR: ...` without raw Python tracebacks.

## Report output

The report command creates or overwrites the file named by `--output`:

```powershell
python -m dev_kit report --path ..\DungeonDex --profile dungeondex --output .\devkit-report.md
```

In that PowerShell example, the generated Markdown report is written to:

```text
.\devkit-report.md
```

The parent folder for `--output` should already exist. Use an explicit path so it is obvious where the report will be written.

Generated reports are structured for pasting into GitHub issues, release notes, or mobile project notes. Current sections include:

- project path, generated timestamp, and overall status
- PASS / WARN / FAIL summary
- audit-group summary
- version-label check results
- baseline file check results
- warnings and recommended next actions
- full check list

See `docs/SAMPLE_REPORT.md` for example report output.

Report generation does not modify the audited project. It only creates or overwrites the exact file passed through `--output`.

## Development

Run the unit tests from the repo root:

```bash
python -m unittest discover -s tests
```

The same command also works in Windows PowerShell:

```powershell
python -m unittest discover -s tests
```
