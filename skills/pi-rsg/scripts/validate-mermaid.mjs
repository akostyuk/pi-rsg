#!/usr/bin/env node
/**
 * validate-mermaid.mjs
 *
 * pi-rsg Mermaid validation wrapper.
 *
 * Extracts all ```mermaid fenced code blocks from Markdown files in a
 * directory (or a single file) and validates each block using
 * mermaid.parse().  Returns exit code 0 (all valid) or 1 (errors found)
 * plus a structured JSON report on stdout.
 *
 * Usage:
 *   node validate-mermaid.mjs --dir <path>
 *   node validate-mermaid.mjs --file <path>
 *   node validate-mermaid.mjs --stdin          # reads Markdown from stdin
 *
 * Exit codes:
 *   0 — all Mermaid blocks are structurally valid (or no blocks found)
 *   1 — one or more blocks failed validation
 *   2 — missing arguments / I/O error
 */

import { readdirSync, readFileSync, existsSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";

/* ─── Patch DOMPurify at startup ──────────────────────────────────── */

// Mermaid v10+ internally imports DOMPurify and calls .sanitize/.addHook
// even when parse() is used without rendering. In Node.js (no browser),
// DOMPurify crashes with "DOMPurify.sanitize is not a function".
//
// This patches dompurify's ESM entry so mermaid.parse() works in Node.
// Works both when installed via `npm install` (postinstall) and `pi install`
// (runtime patch). The patch is idempotent — safe to run multiple times.

const PKG_JSON = resolve(import.meta.dirname, "..", "..", "..", "package.json");
const PROJECT_ROOT = existsSync(PKG_JSON)
  ? dirname(PKG_JSON)
  : process.cwd();
const DOMPURIFY_PATH = resolve(
  PROJECT_ROOT,
  "node_modules",
  "dompurify",
  "dist",
  "purify.es.mjs"
);
if (existsSync(DOMPURIFY_PATH)) {
  const MOCK = `// Mock DOMPurify ESM module for mermaid validation.
// Mermaid imports this as ESM and calls .sanitize/.addHook.
// This mock satisfies those calls without needing a real DOM.
export function sanitize(html) {
  return typeof html === 'string' ? html : '';
}
export function addHook() {}
export default { sanitize, addHook };
`;
  writeFileSync(DOMPURIFY_PATH, MOCK);
}

import mermaid from "mermaid";

// mermaid v10 API: use mermaidAPI.parse() — it works without DOM/rendering
const { parse: mermaidParse } = mermaid.mermaidAPI;

// Initialize mermaid (required before parse)
await mermaid.initialize({ securityLevel: "loose" });

/* ─── CLI arg parsing ─────────────────────────────────────────────── */

const args = process.argv.slice(2);
let mode = null; // "file" | "dir" | "stdin"
let target = null;

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case "--dir":
    case "--directory":
      mode = "dir";
      target = args[++i];
      break;
    case "--file":
    case "--files":
      mode = "file";
      target = args[++i];
      break;
    case "--stdin":
      mode = "stdin";
      break;
    case "--help":
      console.error(`
Usage:
  node validate-mermaid.mjs --dir <path>
  node validate-mermaid.mjs --file <path>
  node validate-mermaid.mjs --stdin

Options:
  --dir, --directory  Validate all .md files under a directory (recursive)
  --file, --files     Validate a single .md file
  --stdin             Read Markdown from stdin
      `);
      process.exit(2);
    default:
      console.error(`Unknown argument: ${args[i]}`);
      process.exit(2);
  }
}

if (!mode) {
  console.error("Error: specify --dir, --file, or --stdin");
  process.exit(2);
}

/* ─── Helpers ─────────────────────────────────────────────────────── */

/**
 * Recursively find all .md files under a directory.
 * Pure Node.js — no external glob dependency.
 */
function _findMdFiles(dir) {
  const results = [];
  const entries = readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = resolve(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(..._findMdFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith(".md")) {
      results.push(fullPath);
    }
  }
  return results;
}

/* ─── Extraction ──────────────────────────────────────────────────── */

/**
 * Extract all Mermaid block bodies from Markdown content.
 * Returns array of { index, body } where body is the raw diagram source.
 *
 * Strategy: find each ```mermaid opening, then search for the next ```
 * that is NOT followed by a language identifier (negative lookahead).
 * The text between is the body.
 */
function extractMermaidBlocks(content) {
  const blocks = [];
  const fenceRe = /^```mermaid\s*$/gim;
  const openMatches = [...content.matchAll(fenceRe)];

  for (let i = 0; i < openMatches.length; i++) {
    const blockStart = openMatches[i].index + openMatches[i][0].length;
    const afterBlock = content.slice(blockStart);

    // Find the next ``` that is NOT followed by a letter (closing fence)
    const closeMatch = afterBlock.match(/```(?![a-zA-Z])/);
    const body = closeMatch
      ? afterBlock.slice(0, closeMatch.index).trim()
      : afterBlock.trim();

    blocks.push({ index: i + 1, body });
  }
  return blocks;
}

/* ─── Validation ──────────────────────────────────────────────────── */

/**
 * Validate a single Mermaid diagram source using mermaid.parse().
 * Returns { valid, errors: string[] }.
 */
async function validateBlock(blockNum, source) {
  try {
    // mermaid.parse() in v11 is async and returns a Promise
    await mermaidParse(source);
    return { valid: true, errors: [] };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return {
      valid: false,
      errors: [`Block #${blockNum}: ${msg}`],
    };
  }
}

/* ─── Main ────────────────────────────────────────────────────────── */

async function main() {
  const results = []; // { file, blocks: [{ index, source, valid, errors }] }
  let totalBlocks = 0;
  let totalErrors = 0;

  if (mode === "stdin") {
    const content = readFileSync("/dev/stdin", "utf-8");
    const blocks = extractMermaidBlocks(content);
    const blockResults = [];

    for (const block of blocks) {
      totalBlocks++;
      const { valid, errors } = await validateBlock(block.index, block.body);
      totalErrors += errors.length;
      blockResults.push({
        index: block.index,
        source: block.body.slice(0, 200) + (block.body.length > 200 ? "…" : ""),
        valid,
        errors,
      });
    }

    results.push({ file: "(stdin)", blocks: blockResults });
  } else {
    let files;
    if (mode === "file") {
      files = [resolve(target)];
    } else {
      // dir mode — recursively find all .md files (no external glob dependency)
      const absTarget = resolve(target);
      files = _findMdFiles(absTarget);
    }

    for (const filePath of files) {
      const content = readFileSync(filePath, "utf-8");
      const blocks = extractMermaidBlocks(content);
      const blockResults = [];

      for (const block of blocks) {
        totalBlocks++;
        const { valid, errors } = await validateBlock(block.index, block.body);
        totalErrors += errors.length;
        blockResults.push({
          index: block.index,
          source: block.body.slice(0, 200) + (block.body.length > 200 ? "…" : ""),
          valid,
          errors,
        });
      }

      if (blockResults.length > 0) {
        results.push({ file: filePath, blocks: blockResults });
      }
    }
  }

  const report = {
    valid: totalErrors === 0,
    totalBlocks,
    totalErrors,
    files: results,
  };

  // Print structured report to stdout
  console.log(JSON.stringify(report, null, 2));

  // Print human-readable errors to stderr
  if (totalErrors > 0) {
    console.error(`\n[validate-mermaid] ${totalErrors} error(s) in ${totalBlocks} Mermaid block(s):\n`);
    for (const result of results) {
      for (const block of result.blocks) {
        for (const err of block.errors) {
          console.error(`  ${result.file}: ${err}`);
        }
      }
    }
  }

  process.exit(totalErrors > 0 ? 1 : 0);
}

main().catch((err) => {
  console.error(`Fatal: ${err.message}`);
  process.exit(2);
});
