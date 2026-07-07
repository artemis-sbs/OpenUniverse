"""Build WRITERS_GUIDE.pdf from the mkdocs writer's-walkthrough pages.

Stitches docs/writing/* (in nav order) + docs/reference/ into one PDF using the
markdown-pdf package (PyMuPDF) - the same toolchain that produced
missions/AMD_AUTHORS_GUIDE.pdf. mkdocs-only syntax is adapted for print:
admonitions become bold blockquotes, and internal .md page links become plain
emphasized text (a PDF has no pages to link to).

Usage (from OpenUniverse/mkdocs):
    python make_pdf.py            -> ../WRITERS_GUIDE.pdf
"""
import os
import re

from markdown_pdf import MarkdownPdf, Section

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "docs")
OUT = os.path.join(HERE, "..", "WRITERS_GUIDE.pdf")

# The walkthrough in nav order (mirrors mkdocs.yml).
PAGES = [
    "writing/index.md",
    "writing/getting-started.md",
    "writing/clans.md",
    "writing/jobs.md",
    "writing/story.md",
    "writing/map.md",
    "writing/people.md",
    "writing/dialogue.md",
    "writing/dials.md",
    "writing/silver-reach.md",
    "writing/troubleshooting.md",
    "reference/index.md",
]

CSS = """
code, pre { background-color: #f2f2f2; }
pre { padding: 6px; font-size: 8.5pt; white-space: pre-wrap; }
table, th, td { border: 1px solid #999; border-collapse: collapse; padding: 4px; }
blockquote { border-left: 3px solid #999; padding-left: 8px; color: #333; }
"""


def adapt(text):
    """Convert mkdocs-flavored markdown to plain markdown for the PDF."""
    out = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^!!!\s+\w+(?:\s+"([^"]*)")?\s*$', line)
        if m:
            # Admonition -> blockquote with a bold title; body is the following
            # 4-space-indented block.
            title = m.group(1) or "Note"
            out.append("> **" + title + "**")
            out.append(">")
            i += 1
            while i < len(lines) and (lines[i].startswith("    ") or lines[i] == ""):
                if i < len(lines) - 1 and lines[i] == "" and not (
                    lines[i + 1].startswith("    ") or lines[i + 1] == ""
                ):
                    break
                out.append(("> " + lines[i][4:]).rstrip())
                i += 1
            continue
        out.append(line)
        i += 1
    text = "\n".join(out)
    # Internal page links -> emphasized text ([label](page.md) / (page.md#anchor)).
    text = re.sub(r"\[([^\]]+)\]\((?:\.\./)?[\w/-]+\.md(?:#[\w-]+)?\)", r"*\1*", text)
    # "Next: ..." footers make sense on a website, not in a linear book.
    text = re.sub(r"^\*\*Next: .*$", "", text, flags=re.MULTILINE)
    return text


def main():
    pdf = MarkdownPdf(toc_level=2, optimize=True)
    pdf.meta["title"] = "Build a Universe - The Writer's Walkthrough"
    pdf.meta["author"] = "Artemis Cosmos - Open Universe"
    cover = (
        "# Build a Universe\n\n## The Writer's Walkthrough\n\n"
        "How to author a galaxy for the **Open Universe** - clans, jobs, story,\n"
        "regions, characters, and dialogue - in one plain-text file, no\n"
        "programming required.\n\n"
        "*An Artemis Cosmos mission - https://github.com/artemis-sbs/OpenUniverse*\n"
    )
    pdf.add_section(Section(cover, toc=False), user_css=CSS)
    for page in PAGES:
        with open(os.path.join(DOCS, page), encoding="utf-8") as f:
            pdf.add_section(Section(adapt(f.read())), user_css=CSS)
    pdf.save(OUT)
    print("wrote", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
