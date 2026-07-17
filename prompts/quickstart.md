# pi-rsg — Quick Start

## What is this

pi-rsg is a skill for **reverse engineering** specifications from a codebase. It operates in the **code → spec** direction: takes an existing project and generates documentation for maintenance/development.

## Quick Start

```bash
# 1. Run the skill in the target project
# (via pi interface — select the pi-rsg skill)

# 2. Or run scripts directly:
python skills/pi-rsg/scripts/source-map.py --target ./src --output rds/source-map.json
python skills/pi-rsg/scripts/coverage-check.py --target-dir rds/final
```

## Architecture (6 phases)

| Phase | What it does | Output |
|-------|-------------|--------|
| **0** | Setup & Goal — define objectives | `rds/goal.json` |
| **1** | Reconnaissance — codebase overview | `recon-report.md` |
| **2** | Plan & WBS — inventory + decomposition | `inventory.json`, `wbs.json` |
| **3** | Investigate — chapter investigation | `drafts/*.md` |
| **4** | Verify — quality check | `coverage-report.json` |
| **5** | Refine — clarification via questions | `questions.json` |
| **6** | Deliver — final specification | `rds/final/*.md` |

## Key files

```
rds/
├── goal.json           # session objectives (Phase 0)
├── state.json          # progress (pause/resume safe)
├── inventory.json      # code units inventory
├── wbs.json            # work breakdown structure
├── questions.json      # question bank
├── source-map.json     # source map (tree-sitter)
├── drafts/             # chapter drafts
│   ├── 01-overview.md
│   ├── 02-architecture.md
│   └── ...
└── final/              # final specification
    ├── 01-overview.md
    └── ...
```

## Useful commands

```bash
# Archive session and clean rds/ for a new run
python skills/pi-rsg/scripts/archive-session.py

# Check final specification quality
python skills/pi-rsg/scripts/coverage-check.py --target-dir rds/final

# Generate source map
python skills/pi-rsg/scripts/source-map.py --target ./src --output rds/source-map.json
```

## Important rules

- **Mermaid only** — ASCII diagrams are forbidden, all diagrams in ` ```mermaid ` blocks
- **`[REF: path:L-L]`** — every claim must have a reference to source code
- **Sources Read** — at the beginning of each chapter, list of read files (≥5)
- **Self-validation** — agent validates Mermaid syntax before saving

## Depth modes (depth_mode)

| Mode | Description |
|------|-------------|
| `comprehensive` | Full specification: ≥200 lines, ≥10 REFs, ≥1 Mermaid per chapter |
| `outline` (default) | Overview tables + Mermaid + list of candidates for deepening |
| `interactive` | Overview only, details on user request |

## Scripts

| Script | Purpose |
|--------|---------|
| `source-map.py` | Source map (tree-sitter, 9 languages) |
| `coverage-check.py` | Quality check (13 checks, including Mermaid syntax) |
| `archive-session.py` | Session packaging + `rds/` cleanup |
| `build-trace.py` | Resolve `[REF:]` into `trace.json` |
| `build-traceability.py` | Generate `traceability.md` from `trace.json` |

## Execution modes (Phase 3)

| Mode | Description |
|------|-------------|
| **Mode A** (default) | Main agent writes chapters inline |
| **Mode B** (opt-in) | Each chapter → isolated sub-agent (`run_in_background: true`) |

Mode B is activated via `goal.json.context_optimization_mode = "B"`.

## Script dependencies

All scripts use **only the standard Python 3 library** — no `pip install` required.
