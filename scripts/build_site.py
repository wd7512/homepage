#!/usr/bin/env python3
"""Build the portfolio site from content/: Markdown -> dist/index.html.

Usage:
    uv run python scripts/build_site.py [--content content] [--out dist/index.html]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adapters.inbound.markdown_loader import ContentError, load
from adapters.outbound.html import render_site


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the portfolio site from content/.")
    ap.add_argument("--content", default="content")
    ap.add_argument("--out", default="dist/index.html")
    args = ap.parse_args()

    try:
        bundle = load(Path(args.content))
    except ContentError as e:
        print(f"FAIL: {e}")
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_site(bundle))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
