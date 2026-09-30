#!/usr/bin/env python3
"""Convert a Markdown file into a polished, self-contained HTML document.

Layout: a sticky left-hand menu (table of contents) beside the rendered
content, light theme by default. ```mermaid fenced blocks are rendered as
diagrams/charts via Mermaid.

Prefers the `markdown` package (with `pygments` for syntax highlighting) when
available — install on the fly with:

    uv run --with markdown --with pygments python3 md_to_html.py --input FILE

Falls back to a built-in minimal converter when `markdown` is not importable.
All styling is inlined; the only optional external asset is the Mermaid script
(loaded from a CDN) and only when the document actually contains a diagram.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
TEMPLATE = ASSETS / "template.html"

# Mermaid is pulled from a CDN only when a diagram is present, so a plain
# document stays fully self-contained.
MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"
MERMAID_TOKEN = "\x00MERMAID{}\x00"


def first_heading(text: str) -> str | None:
    """Return the text of the first ATX `# ` heading, if any."""
    for line in text.splitlines():
        m = re.match(r"^#\s+(.+?)\s*#*\s*$", line)
        if m:
            return m.group(1).strip()
    return None


def extract_mermaid(text: str) -> tuple[str, list[str]]:
    """Pull ```mermaid fenced blocks out so the renderer leaves them intact.

    Returns the text with each block replaced by a placeholder token, plus the
    list of raw diagram sources.
    """
    blocks: list[str] = []

    def repl(m: re.Match[str]) -> str:
        blocks.append(m.group(1))
        return MERMAID_TOKEN.format(len(blocks) - 1)

    pattern = re.compile(r"^```+\s*mermaid\s*\n(.*?)\n```+\s*$", re.DOTALL | re.MULTILINE)
    return pattern.sub(repl, text), blocks


def restore_mermaid(html_body: str, blocks: list[str]) -> str:
    """Swap placeholder tokens back in as Mermaid containers."""
    for idx, src in enumerate(blocks):
        token = MERMAID_TOKEN.format(idx)
        div = f'<pre class="mermaid">{html.escape(src)}</pre>'
        # the token may have been wrapped in <p>…</p> by the renderer
        html_body = re.sub(r"<p>\s*" + re.escape(token) + r"\s*</p>", div, html_body)
        html_body = html_body.replace(token, div)
    return html_body


def render_with_markdown(text: str) -> tuple[str, str] | None:
    """Render via the `markdown` package. Returns (body_html, toc_html) or None."""
    try:
        import markdown  # type: ignore
    except ImportError:
        return None

    extensions = ["fenced_code", "tables", "toc", "sane_lists", "attr_list", "md_in_html", "nl2br"]
    extension_configs = {"toc": {"permalink": True}}
    try:
        import pygments  # noqa: F401

        extensions.append("codehilite")
        extension_configs["codehilite"] = {"guess_lang": False}
    except ImportError:
        pass

    md = markdown.Markdown(extensions=extensions, extension_configs=extension_configs)
    body = md.convert(text)
    toc = getattr(md, "toc", "") or ""
    return body, toc


def slugify(text: str) -> str:
    s = re.sub(r"<[^>]+>", "", text)
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    return re.sub(r"[\s_]+", "-", s) or "section"


def render_fallback(text: str) -> tuple[str, str]:
    """Minimal Markdown→HTML plus a flat TOC, for environments without `markdown`."""
    lines = text.splitlines()
    out: list[str] = []
    toc: list[str] = []
    seen: dict[str, int] = {}
    i = 0
    list_stack: list[str] = []

    def close_lists() -> None:
        while list_stack:
            out.append(f"</{list_stack.pop()}>")

    def inline(s: str) -> str:
        codes: list[str] = []

        def stash(m: re.Match[str]) -> str:
            codes.append(html.escape(m.group(1)))
            return f"\x01{len(codes) - 1}\x01"

        s = re.sub(r"`([^`]+)`", stash, s)
        s = html.escape(s)
        s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img alt="\1" src="\2">', s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
        s = re.sub(r"\x01(\d+)\x01", lambda m: f"<code>{codes[int(m.group(1))]}</code>", s)
        return s

    while i < len(lines):
        line = lines[i]

        fence = re.match(r"^```+\s*([\w+-]*)\s*$", line)
        if fence:
            close_lists()
            lang = fence.group(1)
            buf: list[str] = []
            i += 1
            while i < len(lines) and not re.match(r"^```+\s*$", lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1
            code = chr(10).join(buf)
            if lang == "mermaid":
                out.append(f'<pre class="mermaid">{html.escape(code)}</pre>')
            else:
                cls = f' class="language-{lang}"' if lang else ""
                out.append(f"<pre><code{cls}>{html.escape(code)}</code></pre>")
            continue

        if not line.strip():
            close_lists()
            i += 1
            continue

        if re.match(r"^\s*([-*_])\s*(\1\s*){2,}$", line):
            close_lists()
            out.append("<hr>")
            i += 1
            continue

        h = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if h:
            close_lists()
            level = len(h.group(1))
            label = inline(h.group(2))
            base = slugify(h.group(2))
            seen[base] = seen.get(base, -1) + 1
            anchor = base if seen[base] == 0 else f"{base}-{seen[base]}"
            out.append(f'<h{level} id="{anchor}">{label}<a class="headerlink" href="#{anchor}">¶</a></h{level}>')
            toc.append(f'<li class="toc-l{level}"><a href="#{anchor}">{label}</a></li>')
            i += 1
            continue

        if line.startswith(">"):
            close_lists()
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            out.append(f"<blockquote><p>{inline(' '.join(buf))}</p></blockquote>")
            continue

        ul = re.match(r"^\s*[-*+]\s+(.+)$", line)
        if ul:
            if not list_stack or list_stack[-1] != "ul":
                close_lists()
                list_stack.append("ul")
                out.append("<ul>")
            out.append(f"<li>{inline(ul.group(1))}</li>")
            i += 1
            continue

        ol = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if ol:
            if not list_stack or list_stack[-1] != "ol":
                close_lists()
                list_stack.append("ol")
                out.append("<ol>")
            out.append(f"<li>{inline(ol.group(1))}</li>")
            i += 1
            continue

        close_lists()
        buf = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#{1,6}\s|>|\s*[-*+]\s|\s*\d+[.)]\s|```)", lines[i]
        ):
            buf.append(lines[i])
            i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>")

    close_lists()
    toc_html = ""
    if toc:
        toc_html = '<div class="toc"><ul>' + "".join(toc) + "</ul></div>"
    return "\n".join(out), toc_html


def mermaid_scripts(theme: str) -> str:
    mermaid_theme = "dark" if theme == "dark" else "default"
    # 'auto' resolves at load time from the system preference
    init = (
        "var _mt = '%s';" % mermaid_theme
        + "if ('%s' === 'auto') {" % theme
        + "_mt = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default'; }"
        + "mermaid.initialize({ startOnLoad: true, theme: _mt });"
    )
    return f'<script src="{MERMAID_CDN}"></script>\n<script>{init}</script>'


def build(args: argparse.Namespace) -> int:
    src = Path(args.input)
    if not src.is_file():
        print(f"error: input file not found: {src}", file=sys.stderr)
        return 1

    text = src.read_text(encoding="utf-8")
    title = args.title or first_heading(text) or src.stem

    text, mermaid_blocks = extract_mermaid(text)

    rendered = render_with_markdown(text)
    engine = "markdown"
    if rendered is None:
        body, toc = render_fallback(text)
        engine = "fallback"
    else:
        body, toc = rendered

    body = restore_mermaid(body, mermaid_blocks)

    scripts = mermaid_scripts(args.theme) if mermaid_blocks else ""
    body_class = "" if toc.strip() else "no-toc"

    template = TEMPLATE.read_text(encoding="utf-8")
    page = (
        template.replace("__THEME__", args.theme)
        .replace("__TITLE__", html.escape(title))
        .replace("__BODYCLASS__", body_class)
        .replace("__TOC__", toc or "")
        .replace("__CONTENT__", body)
        .replace("__SCRIPTS__", scripts)
    )

    out_path = Path(args.output) if args.output else src.with_suffix(".html")
    out_path.write_text(page, encoding="utf-8")

    extras = []
    if mermaid_blocks:
        extras.append(f"{len(mermaid_blocks)} diagram(s)")
    note = f" ({', '.join(extras)})" if extras else ""
    print(f"wrote {out_path} (theme={args.theme}, engine={engine}){note}")
    if engine == "fallback":
        print(
            "note: used built-in fallback converter. For full fidelity "
            "(tables, nested TOC, highlighting), run with:\n"
            "  uv run --with markdown --with pygments python3 " + __file__,
            file=sys.stderr,
        )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Convert Markdown to a styled, self-contained HTML file.")
    p.add_argument("--input", "-i", required=True, help="source .md file")
    p.add_argument("--output", "-o", help="destination .html file (default: alongside source)")
    p.add_argument("--theme", choices=["light", "dark", "auto"], default="light", help="color theme (default: light)")
    p.add_argument("--title", help="document title (default: first heading or filename)")
    return build(p.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
