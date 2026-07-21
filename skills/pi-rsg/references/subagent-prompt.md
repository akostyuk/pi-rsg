# Subagent Prompt Reference

Full template for the prompt handed to the sub-agent launched in Phase 3 via the subagent tool.

Sub-agents operate in their own isolated context, so every piece of information they need must be in the prompt. At the same time, excessive information bloats the context and degrades accuracy. This document defines the "necessary and sufficient" line.

---

## Prompt structure

The sub-agent prompt is composed of these 7 sections:

1. **Role**
2. **Goal Context** (excerpt)
3. **Chapter Assignment**
4. **Inventory** to reference
5. **Task Instructions**
6. **Output Format**
7. **Constraints**

---

## Full prompt template

```
You are an investigation agent in charge of a specific chapter of the spec.
Produce a draft of the assigned chapter and report completion to the main agent.

================================
[1. Role]
================================
- Role: investigation agent (chapter-draft author)
- Main agent: pi-rsg coordinator
- Cross-chapter consistency checks happen separately in Phase 4,
  so focus on accuracy within your assigned chapter.

================================
[2. Goal context (excerpt)]
================================
- Primary reader: {primary_reader}
  ({reader_description})
- What the reader does after reading: {reader_action}
- Desired granularity: {granularity}
- Emphasised perspectives: {perspectives}
- Existing documentation: {existing_docs}

[Granularity interpretation]
- High-level overview: macro structure only. Do not delve into class internals.
- Medium: macro + middle units (classes, functions, endpoints). Method-level details may be omitted.
- Detailed: all tiers. State configuration values and thresholds explicitly.

================================
[3. Chapter assignment]
================================
- Chapter ID: {chapter_id}
- Chapter title: {chapter_title}
- Position in the TOC: {chapter_position}
- Output file name: {output_file_name}    ← already assigned by the main agent. Do NOT decide naming yourself.
- Template definition (the structure of this chapter):
{template_section_markdown}

================================
[4. Inventory items to reference]
================================
The following inventory items are what your assigned chapter must cover.
For each item, read the source code carefully.

{inventory_items_json}

Example:
[
  {
    "id": "INV-042",
    "type": "class",
    "name": "UserDeactivationJob",
    "file": "src/jobs/UserDeactivationJob.php",
    "line": 12
  },
  ...
]

================================
[5. Task instructions]
================================
1. Use the Read tool to carefully read the source files corresponding to the assigned inventory items.
2. As needed, use Grep / Glob to explore related code.
3. Generate the chapter body in Markdown.
4. For every statement, attach a `[REF: file:lines]` citation with precise line ranges.
   - Example: "Users are physically deleted 30 days after withdrawal [REF: src/jobs/UserDeactivationJob.php:34-42]"
5. Do not hide uncertainty; use these markers:
   - [CONFIDENCE: HIGH]   reliably derivable from the code
   - [CONFIDENCE: MED]    multiple interpretations are possible; written with the most likely one
   - [CONFIDENCE: LOW]    high inference; needs confirmation
   - [ASK SME]            requires confirmation from a subject-matter expert
   - [ASSUMED: {content}; basis: {evidence}]   surface the inference and its basis
   - [BLOCKED: see Q-XXX] left blank because of a critical question; see the Question Bank
6. Append a "detail questions raised in this chapter" list at the end of the chapter.
   - Each question follows this format:
     - Q: {question body}
     - Evidence: {file:lines code excerpt}
     - Category: {one of the 7 standard categories}
     - Severity: critical / important / nice-to-have
     - Inference: {current best inference}

================================
[6. Output format]
================================
Return Markdown shaped as follows. The frontmatter (including `output_file_name`) is mandatory.

---
chapter_id: {chapter_id}
chapter_title: {chapter_title}
output_file_name: {output_file_name}
generated_at: {ISO8601}
references_count: {number}
questions_count: {number}
blocked_sections: [{section_name}, ...]
---

# {chapter_title}

## (chapter body here)

...

---

## Detail questions raised in this chapter

### Q-XXX (severity: important, category: business_rule)
- Question: ...
- Evidence: src/foo.php:34-42
  ```php
  // code excerpt
  ```
- Inference: ...

### Q-YYY (severity: critical, category: architecture_decision)
...

================================
[7. Constraints]
================================
- Never conflate inference with fact. Inference must always carry the [ASSUMED] marker.
- Do not write detail beyond the goal granularity (verbosity hurts).
- Do not mention inventory items outside your assignment (do not encroach on other sub-agents).
- If you hit a critical question, leave the section as [BLOCKED] and report completion.
  Better to ship the sections you can finish than to stall on perfection.
- Before fully Read-ing a file, narrow it down with Grep first.
- **All diagrams MUST be Mermaid fenced code blocks** (` ```mermaid `). ASCII-art, box-drawing text diagrams, and any other hand-crafted diagram format are FORBIDDEN. See the quality gates table above for minimum Mermaid count per chapter.
- **Self-validate every Mermaid diagram before saving:**
  - Every ` ```mermaid ` has a closing ` ``` `
  - No `state X --> Y:` anti-pattern (transitions are `X --> Y: label`, NOT `state X --> Y:`)
  - No bare `graph` / `flowchart` — must have direction: `graph TB`, `flowchart LR`
  - ER relationships use cardinality (`}o|--||`, `||--|{`), not bare `-->`
  - A malformed diagram will be caught by `coverage-check.py` and trigger a Phase 4 loopback.
  For files under 100 lines, a full Read is fine.
- Use WebFetch / WebSearch only to consult the official docs of an external library.
  Do NOT use them for internal code exploration.
- Suggested chapter body length: medium → 200-500 lines; detailed → 500-1500 lines.
  Exceeding this significantly means the WBS split needs to be revisited — report to the main agent.
- **Use exactly the `{output_file_name}` handed down by the main agent.**
  Free-form naming is forbidden (no `chapter2_architecture.md`-style names).
  Save location is fixed at `drafts/{output_file_name}`.

================================
[Completion report]
================================
When you finish, return:
1. The generated chapter draft (Markdown).
2. The detail-questions list (structured).
3. If any sections are blocked, the list of them.
4. Any unexpected situations you encountered.
```

---

## Prompt-variable filling example

The main agent fills these variables when launching the sub-agent:

```python
prompt_variables = {
    "primary_reader": "Maintenance developer",
    "reader_description": "Engineer who inherited the codebase",
    "reader_action": "Code change",
    "granularity": "medium",
    "perspectives": ["functional_correctness", "operational"],
    "existing_docs": "none",
    "chapter_id": "ch-04-routes",
    "chapter_title": "Routes / endpoints",
    "chapter_position": "Chapter 4 / 8",
    "output_file_name": "04-routes.md",   # ASCII slug; the sub-agent obeys this strictly
    "template_section_markdown": "...(excerpt of the relevant chapter from templates/web-app.md)...",
    "inventory_items_json": "[{...}, {...}, ...]"
}
```

---

## Sub-agent operating mode

The sub-agent's decision logic follows this pseudocode:

```python
def investigate_chapter(prompt):
    # 1. Read every assigned inventory item
    for item in inventory_items:
        read_source(item.file, item.line)

    # 2. Generate the body section by section; record questions as they arise
    questions = []
    for section in chapter_sections:
        try:
            content = generate_section_content(section)
        except UncertaintyDetected as q:
            questions.append(q)
            if q.severity == "critical":
                content = f"[BLOCKED: see {q.id}]"
            else:
                content = generate_with_assumption(section, q)
                # Marked with [CONFIDENCE: LOW; ASSUMED: ...]

    # 3. Append the question list at the end of the chapter
    return chapter_draft + format_questions(questions)
```

---

## Failure patterns the sub-agent must avoid

### Pattern 1: stalling while trying to write the chapter "perfectly"
- When you hit a critical question, leave it as [BLOCKED] and finish the sections you can.
- "Stall on everything and write nothing" is the worst pattern.

### Pattern 2: writing inference as fact
- Mixing "probably" / "seems to" into the prose makes it impossible for later readers to tell fact from inference.
- Always use [CONFIDENCE: LOW] or [ASSUMED] markers.

### Pattern 3: omitting traceability citations
- Writing the body without citations leaves later verification with "no basis".
- Put at least one `[REF:]` in every paragraph.

### Pattern 4: stepping outside your assignment
- Going deep into another chapter's inventory items causes overlap or contradictions between chapters.
- When needed, just write "→ see Chapter N for details".

### Pattern 5: blindly Reading the whole file
- Reading a large file (1000+ lines) in full bloats the context.
- First narrow with Grep, then Read only the relevant line ranges.

---

## Example sub-agent launch from the main agent

Pseudocode (Python-like):

```python
def launch_subagents(wbs, goal, inventory, parallelism=1):
    """
    Launch chapter-investigator sub-agents.

    parallelism=1  → sequential (one at a time)
    parallelism=N>1 → batched (N per turn, wait for all, then next batch)
    """
    chapters = list(wbs.chapters)

    if parallelism == 1:
        # Sequential mode
        for chapter in chapters:
            prompt = _build_prompt(chapter, goal, inventory)
            result = subagent(
                prompt=prompt,
                description=f"Investigate chapter: {chapter.chapter_title}",
                subagent_type="chapter-investigator",
                run_in_background: true
            ).result
            save_draft(f"drafts/{chapter.file_name}", result.markdown)
            merge_questions(result.questions)

    else:
        # Batched mode: emit `parallelism` calls per turn
        for i in range(0, len(chapters), parallelism):
            batch = chapters[i:i + parallelism]
            tasks = []
            for chapter in batch:
                prompt = _build_prompt(chapter, goal, inventory)
                tasks.append(subagent(
                    prompt=prompt,
                    description=f"Investigate chapter: {chapter.chapter_title}",
                    subagent_type="chapter-investigator",
                    run_in_background: true
                ))
            # Wait for all tasks in this batch
            results = [t.result for t in tasks]
            for result, chapter in zip(results, batch):
                save_draft(f"drafts/{chapter.file_name}", result.markdown)
                merge_questions(result.questions)

def _build_prompt(chapter, goal, inventory):
    chapter_inventory = [
        item for item in inventory.items
        if item.id in chapter.assigned_inventory_ids
    ]
    return render_subagent_prompt(
        chapter=chapter,
        goal=goal,
        inventory_items=chapter_inventory,
        output_file_name=chapter.file_name,
    )
```
```

---

## Post-execution quality check

The main agent confirms the following on every sub-agent result:

- [ ] Frontmatter (`chapter_id`, `chapter_title`, `output_file_name`, `references_count`, etc.) is present.
- [ ] `output_file_name` matches `wbs.json.chapters[].file_name` (deviations trigger re-run).
- [ ] `references_count` is non-zero (a chapter without basis is invalid; re-run if zero).
- [ ] If `blocked_sections` is non-empty, the Question Bank contains corresponding entries.
- [ ] No Markdown syntax errors in the body (e.g. unclosed code blocks).
- [ ] No detail mentions of out-of-scope inventory items (cross-check with grep).

Sub-agent results that fail these checks are re-run or sent to manual correction.

---

## Phase 4: Chapter Verifier Sub-agent

In Phase 4, the main agent dispatches `chapter-verifier` sub-agents to verify each chapter draft against quality gates. This is controlled by `goal.json.phase4_parallelism` (default: `1`).

### Prompt structure for chapter-verifier

The verifier prompt is simpler than the investigator prompt — it only needs:

1. **Role**: "You are a chapter verifier. Read-only check."
2. **Chapter path**: e.g. `rds/analysis/<session_name>/drafts/05-data-model.md`
3. **Chapter kind**: `"standard"` or `"user_custom"`
4. **Quality gates**: the metrics to check
5. **Output format**: structured report with PASS/FAIL + feedback

### Full verifier prompt template

```
You are the chapter-verifier handling {chapter_path} (kind: {chapter_kind}).

Verify this chapter against the quality gates:
- Body lines (excluding code blocks and comments): ≥ 200 (standard) / ≥ 10 (user_custom)
- [REF: path:start-end] citations: ≥ 10, with precise line ranges
- fenced code blocks: ≥ 3
- Mermaid diagrams (```mermaid): ≥ 1
- ## Sources Read section: ≥ 5 files listed

Read the file with the Read tool, count each metric, and return a structured report:
- Status: PASS or FAIL
- Quality metrics (count / required)
- Failures (if any) with suggestions for improvement
- Malformed references (if any)

NOTE: Do NOT modify the file. You are read-only. Return the verification report only.
```

### Dispatch logic (sequential vs batched)

```python
def verify_chapters(wbs, parallelism=1):
    chapters = list(wbs.chapters)

    if parallelism == 1:
        # Sequential mode
        for chapter in chapters:
            result = subagent(
                prompt=f"Verify {chapter.file_name}...",
                description=f"verify {chapter.chapter_title}",
                subagent_type="chapter-verifier",
                run_in_background: true
            ).result
            if result.status == "FAIL":
                loopback_to_phase3(chapter, result.failures)

    else:
        # Batched mode: emit `parallelism` calls per turn
        for i in range(0, len(chapters), parallelism):
            batch = chapters[i:i + parallelism]
            tasks = []
            for chapter in batch:
                tasks.append(subagent(
                    prompt=f"Verify {chapter.file_name}...",
                    description=f"verify {chapter.chapter_title}",
                    subagent_type="chapter-verifier",
                    run_in_background: true
                ))
            # Wait for all tasks in this batch
            results = [t.result for t in tasks]
            for result, chapter in zip(results, batch):
                if result.status == "FAIL":
                    loopback_to_phase3(chapter, result.failures)
```

### Loopback procedure

When a verifier returns `Status: FAIL`:
1. Identify the failed chapter and collect all failure details (e.g. `body lines: 150/200, [REF:] count: 7/10`)
2. **Dispatch a new `chapter-investigator` sub-agent** with:
   - The same `inventory_ids` as before
   - The failure report from the verifier
   - Instruction: "Read additional sources beyond those already cited. Thicken the body, add more `[REF:]` citations with precise line ranges, and ensure all quality gates pass."
3. The new investigator runs in an **isolated context**, reads additional source files, and rewrites the chapter draft.
4. Re-dispatch the chapter-verifier for that chapter.
5. **Maximum loopback iterations: 2**. If still failing after 2 re-investigation cycles: demote to `99-unresolved.md` (standard) or prompt user (user_custom).

### Example: re-investigation prompt

```
You are the chapter-investigator handling Chapter 5: Data Model (re-investigation).

Previous verification failed with these issues:
- Body lines: 150 / required ≥ 200
- [REF:] citations: 7 / required ≥ 10
- Mermaid diagrams: 0 / required ≥ 1

Target inventory_ids:
- INV-012 (Project)
- INV-013 (Issue)
- INV-014 (User)
- INV-015 (Role)

Corresponding real sources (Read these with the Read tool):
- app/models/project.rb
- app/models/issue.rb
- app/models/user.rb
- app/models/role.rb
- db/schema.rb (relevant portions)

**IMPORTANT**: You must read ADDITIONAL source files beyond those listed above.
Check app/models/concerns/, lib/, config/ for related logic.

Draft output path: rds/analysis/<session_name>/drafts/05-data-model.md (overwrite existing)

Quality bar (MUST meet all):
- Body ≥ 200 lines
- [REF: path:start-end] ≥ 10, with precise line ranges
- fenced code blocks ≥ 3
- Mermaid diagrams ≥ 1 (ER diagram recommended)
- ≥ 5 files under ## Sources Read

When done, return the chapter's key points + a list of detail questions raised.
Do NOT paste the chapter body into the return value — it is already saved to `rds/analysis/<session_name>/drafts/NN-slug.md`.
```
