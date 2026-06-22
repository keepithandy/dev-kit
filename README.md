# dev-kit

A Python command-line toolkit for read-only project audits and release hygiene.

## Goal

Build a small non-JavaScript tooling repo that can support real project work. The first target is DungeonDex-style repo hygiene: version-label checks, baseline file checks, and Markdown audit reports.

## Quick start

```bash
python -m pip install -e .
python -m dev_kit audit --path ../DungeonDex
python -m dev_kit version --path ../DungeonDex
python -m dev_kit report --path ../DungeonDex --output devkit-report.md
```

## Commands

- `audit`: run the default read-only audit suite.
- `version`: compare `VERSION.md` with runtime files.
- `report`: write a Markdown audit report.

## Development

```bash
python -m unittest discover -s tests
```
