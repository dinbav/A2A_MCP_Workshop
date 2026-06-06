# Post 5 Assets Guide — Migrating a2a-sdk 0.3 to 1.0

## Diagrams to Include

### D5.1 — Import Tree Comparison (Before / After)
- **File:** `../diagrams/post5_migration_overview.excalidraw`
- **Placement:** After "What Changed and Why" section, before "Change 1: The Part Type"
- **Caption:** *The full picture of what changes at the import level — most changes are one-line swaps.*
- **What it shows:** Two-column side-by-side of 0.3.22 imports vs 1.0 imports, red/green color coding

### D5.2 — Migration Checklist Flowchart
- **File:** `../diagrams/post5_migration_checklist.excalidraw`
- **Placement:** At the start of "Upgrading Step by Step" section
- **Caption:** *8 steps from 0.3.22 to 1.0 — estimated 2–4 hours for the workshop codebase.*
- **What it shows:** 8 colored step boxes with file names and what to change; green for setup/testing, orange for file edits

---

## Hero Image

### Option A — Freepik Search Terms

Search on [freepik.com](https://freepik.com):

- `"bridge construction migration flat illustration"`
- `"software upgrade version migration flat design"`
- `"API version upgrade flat illustration"`
- `"code refactoring developer flat"`
- `"two islands bridge connecting flat digital art"`

**Style to select:** Bridge metaphor strongly preferred — two distinct areas connected by a bridge under construction, or a finished bridge. Could be abstract with version numbers labeled. Flat illustration, optimistic colors (morning light, soft blues and oranges).

### Option B — DALL-E / Midjourney Generation Prompt

```
Flat digital illustration of a bridge being built between two floating islands. The left island is labeled "0.3" with older-style infrastructure (round domes, simple shapes). The right island is labeled "1.0" with modern clean architecture (sharp edges, organized pathways). Small robot construction workers are laying cable across the bridge. Morning sunlight. Color palette: soft blue sky, warm amber, mint green. Clean, optimistic, flat illustration style, no photorealism.
```

**Aspect ratio:** 16:9

---

## Tags for Medium

`#Python` `#A2A` `#APIBreakingChanges` `#MigrationGuide` `#MultiAgent` `#AIEngineering` `#OpenSource` `#SoftwareDevelopment` `#Protobuf` `#SDK`

## Subtitle for Medium

> A Practical Before/After Guide for Every Breaking Change — From Part Types to Server Setup

## Series Header

> *This is Part 5 of the **When Agents Talk** series — the final post. The workshop runs on `a2a-sdk==0.3.22`. This is the bridge to v1.0.*

---

## Key Sections with Callout Potential (use Medium quote blocks)

1. "Total estimate for the workshop codebase: 2–4 hours for a careful, test-driven migration. Most changes are grep-and-replace with no logic change."
2. "`hasattr(part, 'text')` does not work reliably with Protobuf types. Use `HasField()` or the new helper functions."
3. "If upgrading everything at once feels daunting, here is the minimal viable migration..."

---

## Estimated Read Time
**10–12 minutes** (before/after code blocks are the dominant content; skim-friendly due to tabular format)
