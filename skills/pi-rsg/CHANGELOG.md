# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] — 2026-07-18

### Added
- **Session name prompt** in Phase 0: user provides a short English name for the analysis (e.g. `myapp-backend`, `payment-service`).

### Changed
- **Session isolation**: all artifacts now live under `rds/analysis/<session_name>/` instead of directly in `rds/`. Each analysis session is fully isolated — no stale artifacts, no archive needed.
- **Phase 0 Step 2**: agent now asks the user for a short English session name (or generates one from project directory), then creates `rds/analysis/<session_name>/` as the working directory.
- All path references in `SKILL.md`, scripts, and documentation updated to use `rds/analysis/<session_name>/`.

### Removed
- **`archive-session.py`**: no longer needed. Session isolation makes archiving obsolete — each analysis is already in its own directory.

---

## [Unreleased]

### Fixed
- `coverage-check.py`: fix `NameError: name 'drafts' is not defined` in `build_report()` — the Mermaid validation call referenced a non-existent variable; renamed to `chapters` (the actual dict of scanned chapter files).

## [0.2.0] — 2026-07-18

### Added
- **Configurable sub-agent parallelism**: `goal.json.phase3_subagent_parallelism` (default: 1) controls how many chapter-investigator sub-agents run concurrently in Phase 3. Value `1` = sequential; value `N > 1` = batched parallel (N calls per turn, wait for all results, then next batch).
- **Configurable Phase 4 verification parallelism**: `goal.json.phase4_parallelism` (default: 1) controls how many chapter-verifier sub-agents run concurrently in Phase 4.
- **New `chapter-verifier` sub-agent** (`agents/chapter-verifier.md`): read-only verifier that checks per-chapter quality gates (body lines ≥ 200, `[REF:]` count ≥ 10, code blocks ≥ 3, Mermaid diagrams ≥ 1, Sources Read ≥ 5) and returns structured PASS/FAIL report with detailed feedback.
- **Phase 0 Q6-Q7**: two new configuration questions — chapter investigation parallelism (Q6) and verification parallelism (Q7). Total Phase 0 questions increased from 5 to 7.
- **Phase 4 per-chapter verification via sub-agents**: after `coverage-check.py` global checks, each chapter is verified by an isolated `chapter-verifier` sub-agent. Failing chapters are looped back to Phase 3 with detailed failure feedback.
- **Re-investigation mode for `chapter-investigator`**: when looped back from Phase 4, the investigator receives verification feedback and reads additional source files to thicken the chapter.

### Changed
- **Phase 3 STEP G**: sequential dispatch is now the default and recommended mode. Parallel batched dispatch (N > 1) is opt-in via `phase3_subagent_parallelism`. The previous "MANDATORY parallel dispatch" rule has been removed.
- **Phase 4 loopback procedure**: failing chapters are now re-dispatched to a new `chapter-investigator` sub-agent (with verification feedback) instead of being patched by the main agent. Maximum 2 loopback iterations per chapter.
- **`references/subagent-prompt.md`**: updated with Phase 4 verifier prompt template and re-investigation example.
- **`AGENTS.md`**: updated common pitfalls #6 to reflect configurable parallelism for both Phase 3 and Phase 4.

### Fixed
- **`Task` tool references removed**: all occurrences of `Task` (legacy pi runtime tool name) replaced with `subagent` or removed in agent prompts and documentation.

---

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
