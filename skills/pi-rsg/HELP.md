# pi-rsg — Help

## What it does

Generates maintenance specifications from a codebase (code → spec). Runs in 6 phases.
Each analysis session is fully isolated under `rds/analysis/<session_name>/`:

```
Phase 0: Setup & Goal       → rds/analysis/<session_name>/goal.json
Phase 1: Recon & Template   → recon-report.md
Phase 2: Plan & WBS         → inventory.json, wbs.json
Phase 3: Investigate        → drafts/*.md (chapter drafts)
Phase 4: Verify             → coverage-check.py gate
Phase 5: Refine via Dialogue → questions.json resolved
Phase 6: Deliver            → rds/analysis/<session_name>/final/*.md (final specification)
```

## Quick Start

```bash
# 1. Run the skill via TUI: /skill:pi-rsg
#    Or from CLI: pi --skill skills/pi-rsg

# 2. Scripts (work from any directory):
python skills/pi-rsg/scripts/source-map.py --target ./src --output rds/analysis/<session_name>/source-map.json
python skills/pi-rsg/scripts/coverage-check.py --pi-rsg-dir rds/analysis/<session_name>
```

## Project Architecture

```
skills/pi-rsg/
├── SKILL.md              ← full instructions (1500+ lines)
├── HELP.md               ← this help file
├── agents/
│   └── chapter-investigator.md  ← sub-agent prompt (Phase 3)
├── references/           ← reference materials
│   ├── inventory-units.md    ← inventory units by language
│   ├── template-catalog.md   ← template catalog
│   ├── question-categories.md ← question categories
│   └── outline-tables.md     ← overview tables by language
├── templates/            ← specification templates
│   ├── web-app.md
│   ├── batch-system.md
│   ├── api-service.md
│   └── library-sdk.md
├── variants/B/           ← Mode B: context optimization (opt-in)
└── scripts/
    ├── source-map.py          ← wrapper for source_map_v2 (any cwd)
    ├── source_map_v2/         ← tree-sitter extractor (9 languages)
    ├── coverage-check.py      ← quality checks (13 checks)
    ├── build-trace.py         ← [REF:] → trace.json
    └── build-traceability.py  ← trace.json → traceability.md
```

## Key Rules

| Rule | Description |
|------|-------------|
| **Mermaid only** | ASCII diagrams are forbidden. All diagrams in ` ```mermaid ` blocks |
| **`[REF: path:L-L]`** | Every claim — a reference to source code with line numbers |
| **Sources Read** | At the start of each chapter — a list of read files (≥5) |
| **Skeleton cap** | Phase 2 skeletons ≤5 lines. Everything else — Phase 3 |
| **Zero deps** | All scripts use only Python stdlib, no `pip install` |

## Depth Modes (depth_mode)

| Mode | Description | When to use |
|------|-------------|-------------|
| `comprehensive` | Full specification: ≥200 lines, ≥10 REFs, ≥1 Mermaid per chapter | For small projects, when full documentation is needed |
| `outline` (default) | Overview tables + Mermaid + list of candidates for deepening | For most projects, quick overview |
| `interactive` | Overview only, details on user request | For large codebases, iterative exploration |

## Work Modes (Phase 3)

| Mode | Description | How to enable |
|------|-------------|---------------|
| **Mode A** (default) | Main agent writes chapters inline | No configuration needed |
| **Mode B** (opt-in) | Each chapter → isolated sub-agent (`run_in_background: true`) | `goal.json.context_optimization_mode = "B"` |

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` when running source_map_v2 | Use `scripts/source-map.py` — works from any cwd |
| ASCII diagrams instead of Mermaid | See `SKILL.md` § "Mermaid format requirement" — ASCII is forbidden |
| Invalid Mermaid syntax | See `SKILL.md` § "Mermaid self-validation" — 6 checks before saving |
| Agent cannot find scripts | Scripts are in `skills/pi-rsg/scripts/` — use absolute paths or `source-map.py` |

## `rds/` Structure After Run

Each analysis session is fully isolated:

```
rds/
└── analysis/
    └── <session_name>/
        ├── goal.json           # session goals (Phase 0)
        ├── state.json          # progress (pause/resume safe)
        ├── inventory.json      # code units inventory
        ├── wbs.json            # work breakdown structure
        ├── questions.json      # question bank (Phase 5)
        ├── source-map.json     # source map (tree-sitter)
        ├── recon-report.md     # codebase overview (Phase 1)
        ├── drafts/             # chapter drafts (Phase 3)
        │   ├── 01-overview.md
        │   ├── 02-architecture.md
        │   └── ...
        └── final/              # final specification (Phase 6)
            ├── 01-overview.md
            └── ...
```

## Useful Commands

```bash
# Check quality of the final specification
python skills/pi-rsg/scripts/coverage-check.py --pi-rsg-dir rds/analysis/<session_name>

# Get the source map
python skills/pi-rsg/scripts/source-map.py --target ./src --output rds/analysis/<session_name>/source-map.json
```

## Dependencies

All scripts use **only the Python 3 standard library**:
- `argparse`, `json`, `re`, `sys` — CLI and parsing
- `pathlib`, `os`, `shutil` — file operations
- `dataclasses`, `typing` — data types
- `datetime` — timestamps

No `pip install`, no external dependencies. Works on Python 3.7+.
