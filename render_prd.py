"""Render PRD.md to PRD.pdf (styled HTML -> headless Chrome print-to-pdf)."""

import subprocess
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "PRD.md"
HTML = ROOT / "PRD.html"
PDF = ROOT / "PRD.pdf"

CSS = """
@page { margin: 18mm 16mm; }
body {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 10.5pt; line-height: 1.55; color: #1a1a1a; max-width: 760px;
}
h1 { font-size: 21pt; border-bottom: 2.5px solid #111; padding-bottom: 6px; }
h2 { font-size: 14.5pt; margin-top: 26px; border-bottom: 1px solid #999; padding-bottom: 3px; }
h3 { font-size: 11.5pt; margin-top: 18px; color: #333; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 8.8pt; }
th, td { border: 0.6px solid #777; padding: 4px 7px; text-align: left; vertical-align: top; }
th { background: #efefef; }
code { font-family: "SF Mono", Menlo, monospace; font-size: 8.8pt;
       background: #f4f4f4; padding: 0.5px 3px; border-radius: 2px; }
li { margin-bottom: 3px; }
blockquote { color: #444; border-left: 3px solid #bbb; margin-left: 0; padding-left: 12px; }
hr { border: none; border-top: 1px solid #bbb; margin: 20px 0; }
strong { font-weight: 650; }
"""


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    HTML.write_text(
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>Ofrenda — PRD v2.0</title><style>{CSS}</style></head>"
        f"<body>{body}</body></html>",
        encoding="utf-8",
    )
    subprocess.run(
        [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "--headless", "--disable-gpu", "--no-pdf-header-footer",
            f"--print-to-pdf={PDF}",
            f"file://{HTML}",
        ],
        check=True, capture_output=True,
    )
    print(f"rendered {PDF} ({PDF.stat().st_size // 1024} KB) from {SRC.name}")


if __name__ == "__main__":
    main()
