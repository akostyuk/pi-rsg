# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Phase 6 step 2 — Clean up draft artifacts**: after copying chapters to `rds/final/`, the entire `drafts/` directory is removed. Prevents stale intermediate files from contaminating subsequent runs.

### Fixed
- `coverage-check.py`: fix `NameError: name 'drafts' is not defined` in `build_report()` — the Mermaid validation call referenced a non-existent variable; renamed to `chapters` (the actual dict of scanned chapter files).

### Changed
- **Artifact directory renamed**: `.pi-rsg/` → `rds/` (Reverse-Designed Specs). All scripts, templates, agent prompts, and documentation updated. `rds/` is no longer a hidden directory — visible in project root alongside `.gitignore`. Archive path: `rds/archive/<session-name>/`.

### Added
- `scripts/source-map.py` wrapper — resolves its own location at runtime so `source_map_v2` works from **any working directory**. Agent no longer needs to `cd` or guess paths.
- Mermaid format requirement — ASCII-art diagrams explicitly forbidden; all diagrams MUST be ` ```mermaid ` fenced blocks.
- Mermaid self-validation — agent must verify diagram syntax before saving (no `state X --> Y:` anti-pattern, no bare `graph` without direction, ER cardinality required).
- `coverage-check.py` Mermaid syntax validation — new check #13: structural validation of every ` ```mermaid ` block (unclosed fences, invalid syntax patterns).
- `archive-session.py` — packs `rds/` artifacts into `rds/archive/<session-name>/` and cleans stale state for the next run. Archives both `drafts/` and `final/`, then removes all files from both directories.
- `HELP.md` — concise reference guide for quick start, common commands, and troubleshooting.

## [0.1.0] — 2026-07-17

### Added
- Initial port of cc-rsg to pi coding agent. Forked from [cc-rsg](https://github.com/earendil-works/cc-rsg) and adapted for the pi coding agent runtime.
- 6-phase state machine: goal setup, reconnaissance, WBS planning, parallel chapter investigation, quality verification, and iterative refinement.
- Tree-sitter-based source map extraction for 9 languages (TypeScript/JS, Python, Ruby/Rails, PHP/Laravel, Java/Spring, C#/ASP.NET, Go, SQL, COBOL).
- Per-chapter sub-agent delegation with Phase 4 loopback verification.
- Three depth modes: comprehensive, outline, interactive.
- English and Russian language support for deliverables.
- Verification scripts: `coverage-check.py`, `build-trace.py`, `build-traceability.py`.
- Templates for web-app, batch-system, api-service, and library-sdk specifications.

### Changed
- **Language policy**: Russian is the new base language (`"ru"`). Phase 0 Step 3 presents bilingual choice (Русский / English). All deliverables follow `output_language` — ru (default) → Русский; en → English. Japanese support removed.
- **`source_map_v2/`**: tree-sitter-based extractor with role typing, framework detection, 9 languages. Replaces v1 `source-map.py`. Fallback to file-level units with loud warning when tree-sitter is unavailable. Integrated into Phase 2 STEP A.

---

> **Note:** This project is a fork of [cc-rsg](https://github.com/earendil-works/cc-rsg), adapted for the pi coding agent runtime. All changes from the initial fork onward are specific to the pi-rsg port.
