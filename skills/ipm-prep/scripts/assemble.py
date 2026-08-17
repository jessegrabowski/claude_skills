#!/usr/bin/env python3
"""Render an Obsidian note and everything it embeds as one PDF beside it.

Obsidian renders ``![[note]]`` inline, so an IPM OVERVIEW reads and exports as a
single document from inside the app. This does the same substitution outside it:
resolve each embed, demote its headings one level so the host note's hierarchy
survives, drop the embedded frontmatter, and reduce leftover wikilinks to their
display text. The flattened markdown is an intermediate and is discarded unless
asked for; the PDF is the deliverable.
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EMBED = re.compile(r"^!\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]\s*$", re.MULTILINE)
WIKILINK = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]")
FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
HEADING = re.compile(r"^(#{1,5}) ", re.MULTILINE)


class ResolutionError(Exception):
    pass


def find_note(target: str, host: Path, vault: Path) -> Path:
    """Resolve an embed target the way Obsidian does: exact path, then by name."""
    candidates = [host.parent / f"{target}.md",
                  vault / f"{target}.md"]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    name = Path(target).name
    by_name = sorted(vault.rglob(f"{name}.md"))

    if not by_name:
        raise ResolutionError(f"no note matches embed [[{target}]]")

    same_folder = [path for path in by_name if path.parent == host.parent]

    return same_folder[0] if same_folder else by_name[0]


def strip_wikilinks(text: str) -> str:
    return WIKILINK.sub(lambda match: match.group(2) or Path(match.group(1)).name,
                        text)


def demote_headings(text: str) -> str:
    return HEADING.sub(lambda match: f"{match.group(1)}# ", text)


def flatten(host: Path, vault: Path) -> tuple[str, list[str]]:
    text = host.read_text()
    embedded: list[str] = []

    def substitute(match: re.Match[str]) -> str:
        target = match.group(1).strip()
        note = find_note(target, host, vault)
        embedded.append(str(note.relative_to(vault)))

        body = FRONTMATTER.sub("", note.read_text()).strip()

        return demote_headings(body) + "\n"

    return EMBED.sub(substitute, text), embedded


def find_vault(start: Path) -> Path:
    for directory in [start, *start.parents]:
        if (directory / ".obsidian").is_dir():
            return directory

    raise ResolutionError(f"no vault (.obsidian directory) above {start}")


def write_pdf(markdown: Path, pdf: Path, portrait: bool) -> Path:
    """Render with pandoc. Wide PR tables overflow a portrait page, so landscape is the default."""
    geometry = ["--variable", "geometry:margin=0.9in",
                "--variable", "fontsize=10pt"] if portrait else \
               ["--variable", "geometry:margin=0.6in",
                "--variable", "geometry:landscape",
                "--variable", "fontsize=9pt"]

    subprocess.run(["pandoc",
                    str(markdown),
                    "--from=gfm",
                    "--output", str(pdf),
                    "--pdf-engine=tectonic",
                    "--variable", "colorlinks=true",
                    *geometry],
                   check=True)

    return pdf


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("overview",
                        type=Path,
                        help="the note whose embeds get inlined")
    parser.add_argument("-o", "--output",
                        type=Path,
                        help="pdf target (default: <folder name>.pdf beside the note)")
    parser.add_argument("--keep-markdown",
                        type=Path,
                        help="also keep the flattened markdown at this path (default: discarded)")
    parser.add_argument("--portrait",
                        action="store_true",
                        help="render portrait at 10pt instead of landscape at 9pt")
    parser.add_argument("--keep-wikilinks",
                        action="store_true",
                        help="leave [[...]] intact instead of reducing to display text")
    arguments = parser.parse_args()

    host = arguments.overview.expanduser().resolve()

    if not host.is_file():
        print(f"not a file: {host}", file=sys.stderr)
        return 1

    try:
        vault = find_vault(host.parent)
        text, embedded = flatten(host, vault)
    except ResolutionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if not arguments.keep_wikilinks:
        text = strip_wikilinks(text)

    pdf = arguments.output or host.parent / f"{host.parent.name}.pdf"

    print(f"inlined {len(embedded)} embeds")
    for note in embedded:
        print(f"  {note}")

    # The flattened markdown is an intermediate. Keeping it in the vault would leave
    # a second, stale copy of the brief for Obsidian to index next to the real one.
    with tempfile.TemporaryDirectory() as scratch:
        flattened = Path(scratch) / f"{host.parent.name}.md"
        flattened.write_text(text)

        if arguments.keep_markdown:
            arguments.keep_markdown.expanduser().write_text(text)
            print(f"markdown: {arguments.keep_markdown}")

        try:
            print(f"pdf: {write_pdf(flattened, pdf, arguments.portrait)}")
        except (subprocess.CalledProcessError, FileNotFoundError) as error:
            print(f"pandoc failed ({error}); export from Obsidian instead",
                  file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
