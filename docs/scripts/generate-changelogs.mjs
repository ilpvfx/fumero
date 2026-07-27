import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const outDir = join(root, "docs", "content", "docs");

mkdirSync(outDir, { recursive: true });

const raw = readFileSync(join(root, "CHANGELOG.md"), "utf-8");

// Strip the top-level "# Changelog" heading — the page title replaces it. Unwrap links in headings
// to avoid nested <a> tags (fumadocs wraps headings in anchors). e.g.
// "## [0.5.1](https://...compare/a...b) (2026-03-16)" → "## 0.5.1 (2026-03-16)"
// Add placeholder for entries that have no content.
const body = raw
  .replace(/^# Changelog\s*\n/, "")
  .replace(/^(#{2,3})\s+\[([^\]]+)\]\([^)]+\)/gm, "$1 $2")
  .split(/^(?=## )/m)
  .filter((s) => s.trim())
  .map((section) => {
    const [heading, ...rest] = section.split("\n");
    const content = rest.join("\n").trim();
    return content ? section : `${heading}\n\nNo notable changes.\n`;
  })
  .join("\n");

const mdx = `---
title: "Changelog"
icon: "History"
---

${body}`;

writeFileSync(join(outDir, `changelog.mdx`), mdx);
