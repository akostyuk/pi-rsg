# pi-rsg — Pi Package

Reverse-engineer comprehensive specification documents from existing codebases through goal-driven reconnaissance, WBS-based parallel investigation, and iterative question-bank dialogue.

## Install

```bash
git clone https://github.com/akostyuk/pi-rsg.git
cd pi-rsg
pi install .
```

## Usage

After installation, invoke the skill:

```bash
/skill:pi-rsg
```

Or just ask naturally: *"Generate a spec document from this codebase"* — pi will auto-discover and load the skill.

## What it does

pi-rsg reverse-engineers maintenance- or delivery-targeted specification documents from existing codebases (legacy or current). It operates in the "code → spec" direction.

### Key features

- **6-phase state machine** with pause/resume support
- **3 depth modes**: comprehensive (audit), outline (default), interactive (team reference)
- **Mechanical source extraction** via tree-sitter for 9 languages (Python, TS/JS, Ruby/Rails, PHP, Java, C#, Go, SQL, COBOL)
- **Question Bank** with 7 categories and severity levels
- **Traceability**: every statement has `[REF: path:line]` citations
- **Honesty-first**: uncertainty markers, abandoned questions → "Unresolved Items" chapter

## Requirements

- Python 3.10+ (for `scripts/` utilities)
- **tree-sitter** (optional, for full language-aware extraction via `source_map_v2/`)

### tree-sitter fallback behavior

`source_map_v2/` uses tree-sitter for per-language extraction (classes, methods, endpoints, etc.). If tree-sitter is not installed:

- The extractor **falls back to file-level units** (one `module`-role unit per source file)
- A **loud warning** is printed to stderr (never a silent drop)
- Phase 2 inventory extraction still works, but with reduced granularity

To install tree-sitter for full extraction:
```bash
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-ruby tree-sitter-php tree-sitter-java tree-sitter-c-sharp tree-sitter-go tree-sitter-sql
```

Without tree-sitter, the skill still functions — just with coarser-grained inventory items.

## License

MIT
