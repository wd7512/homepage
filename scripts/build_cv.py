#!/usr/bin/env python3
"""Build the CV from content/: Markdown -> dist/cv.tex, optionally dist/cv.pdf.

Usage:
    uv run python scripts/build_cv.py [--content content] [--out dist/cv.tex] [--pdf]

--pdf compiles with latexmk (requires a local TeX install) and scrubs
identifying PDF metadata, keeping only title/author from content/personal.md.
TeX artefacts stay in dist/ (gitignored); no PDF is ever committed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adapters.inbound.markdown_loader import ContentError, load
from adapters.outbound.latex import render_cv


def compile_pdf(tex_path: Path) -> Path:
    """Compile with latexmk in the output dir (relative name: no abs paths leak)."""
    pdf_path = tex_path.with_suffix(".pdf")
    cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", tex_path.name]
    proc = subprocess.run(cmd, cwd=tex_path.parent, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not pdf_path.exists():
        print(proc.stdout[-3000:])
        print(proc.stderr[-3000:], file=sys.stderr)
        raise SystemExit("FAIL: latexmk did not produce a PDF")
    return pdf_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the LaTeX CV from content/.")
    ap.add_argument("--content", default="content")
    ap.add_argument("--out", default="dist/cv.tex")
    ap.add_argument("--pdf", action="store_true", help="Also compile dist/cv.pdf")
    ap.add_argument(
        "--pdf-out",
        default="cv.pdf",
        help="Tracked copy of the built PDF (repo-root link target for the site).",
    )
    args = ap.parse_args()

    try:
        bundle = load(Path(args.content))
    except ContentError as e:
        print(f"FAIL: {e}")
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_cv(bundle))
    print(f"Wrote {out}")

    if args.pdf:
        import shutil

        pdf = compile_pdf(out)
        print(f"Wrote {pdf}")
        tracked = Path(args.pdf_out)
        shutil.copyfile(pdf, tracked)
        print(f"Wrote {tracked} (tracked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
