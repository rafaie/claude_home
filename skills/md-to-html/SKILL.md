---
name: md-to-html
description: This skill should be used when the user asks to "convert markdown to html", "turn this md file into html", "make a nice html from markdown", "render README as html", "export markdown to a styled web page", or wants a polished, self-contained HTML document generated from a Markdown file.
version: 2.0.0
---

# Markdown → HTML

Turn a Markdown file into a **polished, self-contained HTML page**. The goal is not a mechanical 1:1 transcription of the Markdown — it is a *designed document*: hand-authored layout, a light theme by default, inline CSS, and **purpose-built visuals** (SVG charts, diagrams, color-coded cards, scorecards) wherever the content earns them.

> **Core principle — do not ship "pure md→html".** A flat render of headings-and-paragraphs is the fallback, not the target. Read the content, understand its structure, and build the HTML that best *presents* it. Two documents with the same Markdown can deserve very different pages.

## Inputs

Determine from the user request or context:
- **Source** — the `.md` file to convert (required). Read it fully first.
- **Output** — destination `.html` path. Default: same directory and basename as the source, with `.html`.
- **Theme** — `light` (default), `dark`, or `auto`. Light is the default; only go dark if asked.
- **Title** — for the `<title>` tag and page header. Default: the first `# ` heading, else the file basename.

If the source file is ambiguous or missing, ask before proceeding. If the content clearly has rankings/comparisons/multiple items and the desired *visual direction* is unclear (e.g. theme, or "dashboard vs document"), ask one quick clarifying question rather than guessing.

## Decide the treatment first

After reading the source, classify it — this decides how much to build:

1. **Rich / structured content** — rankings, scored comparisons, a catalog of items (ideas, proposals, options), pipelines, taxonomies, before/after, metrics. → **Hand-author a visual dashboard** (see *Authoring principles*). This is the headline use of the skill.
2. **Mostly prose** — a README, a guide, an essay, release notes. → A clean **document** layout is fine. You may use the bundled converter (see *Fallback converter*) and then enrich it, or author it directly.

When in doubt, lean toward more design, not less. The user invoked this skill because they want something nicer than the raw Markdown.

## Authoring principles (the visual dashboard)

Build a single self-contained `.html` file. Match the polish of a well-made one-page report. Concretely:

- **Self-contained.** All CSS inline in a `<style>` block. No external stylesheets, fonts, or JS. The *only* permitted external reference is the Mermaid CDN script, and only if you use a Mermaid block (prefer hand-authored SVG instead — see below). The page must work offline by default.
- **Light, polished theme by default.** White/very-light background, dark slate text, a small palette of accent colors. Use CSS custom properties (`:root { --ink; --muted; --line; --panel; … }`) so the theme is consistent and easy to retune. Soft borders, subtle shadows, generous spacing, system font stack.
- **A color system that carries meaning.** If the content has categories/themes/streams, assign each a color and use it consistently across charts, card borders, and section tags — a legend at the top teaches the reader the code once.
- **At-a-glance, then depth.** Lead with a scannable overview (a card grid, a ranked chart, a summary table), then provide **deep-dive sections** with the full detail. Readers should be able to skim *or* read.
- **Hand-authored SVG visuals — preferred over prose for anything quantitative or structural.** Inline `<svg>` is fully offline, crisp, and themeable. Build the visual the content needs, e.g.:
  - **Ranked bar chart** for scores/sizes (start the axis above zero to make gaps legible; label each bar with its value in the bar's color).
  - **Scatter / quadrant map** for two-axis trade-offs (e.g. novelty × feasibility), bubble size = a third dimension, color = category.
  - **Pipeline / flow diagrams** with boxes, arrows (`<marker>`), and a decision diamond for stages and branches.
  - **Process / stage diagrams** mapping items onto a framework.
  Give every chart a `role="img"` + `aria-label`, and a `<figcaption>` that states the takeaway, not just "a chart."
- **Cards** for a catalog of items: a responsive `grid` of equal cards, each with a category tag, title, one-paragraph summary, a concrete example line, and small status "pills." Color the left border by category.
- **Scorecards / comparison tables** with a highlighted header row, zebra striping, and (optionally) a highlighted top-N. Center numeric columns.
- **Deep-dive blocks** per item: a heading with a category tag + score/badge, a lead sentence, a **"How it works"** ordered list, **multiple worked examples** (include the case that stresses or breaks the mechanism, not just the happy path), and a footer line with eval/metrics and risks. This is where "more content" lives — expand, don't restate.
- **Examples are mandatory where the source has any.** If the source mentions or implies an example, render it concretely. If an idea has none, add an illustrative one that faithfully walks the mechanism.
- **Faithfulness.** Enrich and reorganize, but never invent facts, numbers, or citations the source doesn't support. Pull extra accurate detail from sibling files the user points to (companion proposal/spec docs) rather than fabricating.

A worked reference implementation of all of the above lives at
`/Users/mostafa/git/research/ideas/paper-2/research_ideas.html` — open it to copy structure, the CSS variable scheme, and the SVG chart patterns (ranked bars, novelty/feasibility scatter, MMT-stage and flagship pipelines, idea cards, scorecard, deep-dive sections). Adapt it to the content at hand; do not copy its domain text.

### Hand-authored SVG vs Mermaid

Prefer **hand-authored inline SVG** for charts and bespoke diagrams — it is fully offline, precisely styleable, and matches the page theme. Use a Mermaid block only for a quick standard diagram (flowchart/sequence/Gantt) where authoring SVG by hand isn't worth it; note that Mermaid pulls in a CDN script and so breaks offline use.

## Fallback converter (plain prose, or a starting point)

For prose-heavy docs, or to get a quick structural baseline you then enrich, the bundled converter renders Markdown into a document layout with a sticky left-hand table-of-contents menu, inline CSS, light theme, syntax-highlighted code, tables, task lists, blockquotes, images, and Mermaid blocks:

```bash
uv run --with markdown --with pygments python3 "${CLAUDE_PLUGIN_ROOT}/skills/md-to-html/scripts/md_to_html.py" \
  --input <source.md> --output <output.html> --theme <light|dark|auto> --title "<title>"
```

`--output`, `--theme`, `--title` are optional. Without `uv`/the `markdown` package it falls back to a minimal built-in converter (headings, paragraphs, code, lists, links, bold/italic). This converter does **not** produce charts, cards, or deep-dive layouts — if the content deserves those, author the HTML directly per the principles above instead of (or on top of) running it.

## Verify

After producing the HTML:
1. Confirm the file exists and is non-empty, and is materially richer than the raw Markdown when a dashboard was warranted.
2. Check it is **self-contained**: grep for external references — there should be none, except an intentional Mermaid `<script>` if you used a Mermaid block. (UTF-8 em-dashes can make `grep` treat the file as binary; use `grep -a`.)
3. Spot-check that charts/diagrams have sensible geometry (bars/bubbles in range, arrows connecting the right boxes), cards/tables render, and code blocks are intact.

Report: the output path, the theme used, the treatment chosen (dashboard vs document), and a one-line inventory of the visuals built (e.g. "ranked bar chart, novelty×feasibility scatter, 2 pipeline diagrams, 15 cards, scorecard, 15 deep-dives").
