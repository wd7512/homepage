#!/usr/bin/env python3
"""Dry-run validator: load content/ through the domain and report counts.

Usage:
    uv run python scripts/validate.py [--content content]

Exit 0 when every file parses and validates; exit 1 with a file-level
report otherwise (the conflict ledger for the home -> homepage port).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adapters.inbound.markdown_loader import ContentError, load


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate homepage content.")
    ap.add_argument("--content", default="content")
    args = ap.parse_args()

    try:
        bundle = load(Path(args.content))
    except ContentError as e:
        print(f"FAIL: {e}")
        return 1

    for channel in ("website", "cv"):
        view = bundle.visible(channel)
        print(
            f"{channel}: experience={len(view.experience)} "
            f"education={len(view.education)} research={len(view.research)} "
            f"projects={len(view.projects)} publications={len(view.publications)} "
            f"skills={len(view.skills)} activities={len(view.activities)}"
        )
    print(f"personal={'set' if bundle.personal else 'MISSING'}")
    if bundle.personal is None:
        print("FAIL: content/personal.md is required")
        return 1
    print("OK: all content files parsed and validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
