"""Render docs/technical_brief.md to docs/technical_brief.pdf and check the page limit.

    pip install markdown        # build-time only; the app does not need it
    python docs/build_brief.py

Uses a local Chrome or Edge in headless mode to print the HTML. Set BROWSER to a
browser executable to override the search. References start on a new page, so the
body page count is every page before that one. The challenge limit is three.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "technical_brief.md"
TARGET = HERE / "technical_brief.pdf"
BODY_PAGE_LIMIT = 3

CSS = """
@page { size: Letter; margin: 0.7in 0.75in; }
body { font-family: "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif;
       font-size: 10.5pt; line-height: 1.38; color: #1B1E23; }
h1 { font-size: 17pt; margin: 0 0 4pt; letter-spacing: -0.01em; }
.sub { color: #5C6570; font-size: 9.5pt; margin: 0 0 10pt; }
h2 { font-size: 12pt; margin: 12pt 0 4pt; color: #B85C38; }
p { margin: 0 0 6pt; }
ul { margin: 0 0 6pt; padding-left: 16pt; }
li { margin: 0 0 3pt; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9.5pt; }
a { color: #1B1E23; }
.references { break-before: page; }
.references li { font-size: 9.5pt; }
"""

SUBTITLE = (
    "BRD Command Center · AISFS × Merck Animal Health Interdisciplinary Hackathon 2026, Problem 1 · "
    "https://github.com/snr2753423/brd-command-center"
)


def _browser() -> str:
    override = os.environ.get("BROWSER")
    candidates = [override] if override else []
    candidates += [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "google-chrome",
        "chromium",
        "chromium-browser",
        "microsoft-edge",
    ]
    for candidate in candidates:
        if candidate and (Path(candidate).exists() or shutil.which(candidate)):
            return candidate
    sys.exit("No Chrome or Edge found. Set BROWSER to a Chromium-based browser executable.")


def _html() -> str:
    text = SOURCE.read_text(encoding="utf-8")
    body, _, references = text.partition("## References")
    body_html = markdown.markdown(body, extensions=["tables"])
    body_html = body_html.replace("</h1>", f"</h1>\n<p class=\"sub\">{SUBTITLE}</p>", 1)
    refs_html = markdown.markdown("## References" + references, extensions=["tables"])
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\"><title>Technical brief</title>"
        f"<style>{CSS}</style></head><body>{body_html}"
        f"<section class=\"references\">{refs_html}</section></body></html>"
    )


def _page_count(pdf: Path) -> int:
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))


def _print(html: str, target: Path, scratch: Path) -> None:
    page = scratch / f"{target.stem}.html"
    page.write_text(html, encoding="utf-8")
    subprocess.run(
        [
            _browser(),
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--user-data-dir={scratch / 'profile'}",
            f"--print-to-pdf={target}",
            page.as_uri(),
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )


def main() -> None:
    html = _html()
    with tempfile.TemporaryDirectory() as folder:
        scratch = Path(folder)
        _print(html, TARGET, scratch)
        body_only = scratch / "body.pdf"
        _print(html.split('<section class="references">')[0] + "</body></html>", body_only, scratch)
        body_pages = _page_count(body_only)
    total = _page_count(TARGET)
    print(f"Wrote {TARGET.relative_to(HERE.parent)}: {body_pages} body page(s), {total} in all.")
    if body_pages > BODY_PAGE_LIMIT:
        sys.exit(f"The body is {body_pages} pages. The limit is {BODY_PAGE_LIMIT}, excluding references.")


if __name__ == "__main__":
    main()
