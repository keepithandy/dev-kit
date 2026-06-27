# dev-kit

A Python command-line toolkit for read-only project audits and release hygiene.

## Goal

Build a small non-JavaScript tooling repo that can support real project work. The first target is DungeonDex-style repo hygiene: version-label checks, baseline file checks, and Markdown audit reports.

## Safety model

`dev-kit` is designed to inspect local project folders, not rewrite them.

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

## Development

Run the unit tests from the repo root:

```bash
python -m unittest discover -s tests
```

The same command also works in Windows PowerShell:

```powershell
python -m unittest discover -s tests
```
