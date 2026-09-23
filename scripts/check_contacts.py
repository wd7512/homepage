#!/usr/bin/env python3
"""Contacts allowlist leak checker (stdlib only).

Fails (exit 1) if any email / phone / profile URL found in the working tree
or git history is NOT in contacts.allowlist.yaml.

Usage:
    python3 scripts/check_contacts.py [--mode tree|history|all]
        [--allowlist contacts.allowlist.yaml] [--rev-list HEAD]

Design notes:
  - No third-party deps: parses the known allowlist shape with a tiny
    line-based parser (sections: emails/phones/urls/allow_patterns).
  - Tree scan skips .git/, binaries (null-byte heuristic), and common
    LaTeX/PDF build artefacts listed in SKIP_SUFFIXES.
  - History scan covers patch text (git log -p) PLUS author/committer
    addresses (git log --format=%ae/%ce). That is what currently flags the
    3 private commits (uni author email) and b2d6906 (old home email).
  - Phone normalisation: keep digits only; leading '44' vs '0' variants are
    compared by suffix match (last 10 digits) to avoid format false-negatives.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
# UK-ish phones: +44(...), (0)..., 07xxx xxxxxx, digits with spaces/dashes.
PHONE_RE = re.compile(r"(?:\+44[\s\(\)0-9\-]{7,}|\(0\)\s?\d[\d\s\-]{6,}|07\d{3}\s?\d{3}\s?\d{3})")
LINKEDIN_RE = re.compile(r"https?://(?:[\w.]+\.)?linkedin\.com/in/[\w\-/]+", re.IGNORECASE)
GITHUB_RE = re.compile(r"https?://github\.com/[\w\-]+(?:/[\w.\-]+)?", re.IGNORECASE)

SKIP_DIRS = {".git", "__pycache__", ".venv", ".mypy_cache", ".ruff_cache"}
# Machine-generated lockfiles: version hashes routinely contain digit runs
# that look phone-like. Real contacts never belong here; review diffs instead.
SKIP_FILES = {"uv.lock", "poetry.lock", "package-lock.json", "pnpm-lock.yaml"}
SKIP_SUFFIXES = {
    ".pdf",
    ".aux",
    ".log",
    ".out",
    ".toc",
    ".fls",
    ".fdb_latexmk",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".woff",
    ".woff2",
}


def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {p.stderr.strip()}")
    return p.stdout


def load_allowlist(path: pathlib.Path) -> dict:
    """Minimal parser for the known allowlist shape (no PyYAML needed)."""
    data: dict[str, list[str]] = {
        "emails": [],
        "phones": [],
        "urls": [],
        "allow_patterns": [],
    }
    section: str | None = None
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line in (f"{k}:" for k in data):
            section = line[:-1]
            continue
        if any(line == f"{k}: []" for k in data):
            section = None
            continue
        if line.startswith("- ") and section:
            data[section].append(line[2:].strip())
    patterns = [re.compile(f"^(?:{p})$", re.IGNORECASE) for p in data["allow_patterns"]]
    return {
        "emails": {e.lower() for e in data["emails"]},
        "phone_digits": {re.sub(r"\D", "", p) for p in data["phones"]},
        "urls": {u.rstrip("/").lower() for u in data["urls"]},
        "patterns": patterns,
    }


def pattern_allowed(value: str, patterns: list[re.Pattern]) -> bool:
    return any(p.match(value) for p in patterns)


def phone_allowed(digits: str, allowed: set[str]) -> bool:
    if digits in allowed:
        return True
    # Compare on last-10-digit suffix so "+44..." and "07..." forms match.
    return any(digits[-10:] == a[-10:] for a in allowed if len(digits) >= 10 and len(a) >= 10)


def is_binary(path: pathlib.Path) -> bool:
    try:
        with open(path, "rb") as f:
            return b"\0" in f.read(8192)
    except OSError:
        return True


def tree_candidates() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for p in sorted(REPO.rglob("*")):
        if any(part in SKIP_DIRS for part in p.parts[len(REPO.parts) :]):
            continue
        if not p.is_file() or p.suffix.lower() in SKIP_SUFFIXES:
            continue
        if p.name in SKIP_FILES:
            continue
        if p.name == "contacts.allowlist.yaml":
            continue  # the whitelist itself defines allowed values
        if is_binary(p):
            continue
        try:
            text = p.read_text(errors="replace")
        except OSError:
            continue
        rel = str(p.relative_to(REPO))
        for m in EMAIL_RE.finditer(text):
            out.append((rel, "email", m.group(0)))
        for m in PHONE_RE.finditer(text):
            out.append((rel, "phone", m.group(0).strip()))
        for m in LINKEDIN_RE.finditer(text):
            out.append((rel, "url", m.group(0).rstrip("/")))
        for m in GITHUB_RE.finditer(text):
            # Skip bare code references like github.com/org (still checked as URL).
            out.append((rel, "url", m.group(0).rstrip("/")))
    return out


def history_candidates(rev_list: str) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    try:
        identities = run(["git", "log", rev_list, "--format=%H %ae %ce", "--"])
    except RuntimeError as e:
        return [("<git>", "error", str(e))]
    for line in identities.splitlines():
        parts = line.split()
        if len(parts) == 3:
            sha, ae, ce = parts
            out.append((f"{sha[:8]} author", "email", ae))
            if ce != ae:
                out.append((f"{sha[:8]} committer", "email", ce))
    try:
        patch = run(["git", "log", rev_list, "-p", "--format=commit %H", "--"])
    except RuntimeError as e:
        out.append(("<git>", "error", str(e)))
        return out
    loc = "<history>"
    skipped_file = False
    for line in patch.splitlines():
        if line.startswith("commit "):
            loc = line.split()[1][:8]
            skipped_file = False
            continue
        if line.startswith("diff --git "):
            # Track the new-file path so generated/binary artefacts are
            # skipped in history exactly as in the tree scan.
            skipped_file = False
            parts = line.split()
            if len(parts) >= 4:
                name = parts[-1].removeprefix("b/")
                base = name.rsplit("/", 1)[-1]
                if base in SKIP_FILES or any(name.endswith(s) for s in SKIP_SUFFIXES):
                    skipped_file = True
            continue
        if skipped_file:
            continue
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            # Strip the diff marker so `+@decorator` lines can't match
            # the email pattern via the leading `+`.
            text = line[1:]
            for m in EMAIL_RE.finditer(text):
                out.append((loc, "email", m.group(0)))
            for m in PHONE_RE.finditer(text):
                out.append((loc, "phone", m.group(0).strip()))
            for m in LINKEDIN_RE.finditer(text):
                out.append((loc, "url", m.group(0).rstrip("/")))
            for m in GITHUB_RE.finditer(text):
                out.append((loc, "url", m.group(0).rstrip("/")))
    return out


def check(cands: list[tuple[str, str, str]], allow: dict) -> list[str]:
    violations: list[str] = []
    for loc, kind, val in cands:
        if kind == "email":
            ok = val.lower() in allow["emails"] or pattern_allowed(val, allow["patterns"])
        elif kind == "phone":
            ok = phone_allowed(re.sub(r"\D", "", val), allow["phone_digits"])
        else:
            ok = val.rstrip("/").lower() in allow["urls"] or pattern_allowed(val, allow["patterns"])
        if not ok:
            violations.append(f"{loc} [{kind}] {val}")
    # De-duplicate while keeping order.
    return list(dict.fromkeys(violations))


def main() -> int:
    ap = argparse.ArgumentParser(description="Fail on non-whitelisted contacts.")
    ap.add_argument("--mode", choices=["tree", "history", "all"], default="all")
    ap.add_argument("--allowlist", default="contacts.allowlist.yaml")
    ap.add_argument("--rev-list", default="--all")
    args = ap.parse_args()

    allow = load_allowlist(REPO / args.allowlist)
    cands: list[tuple[str, str, str]] = []
    if args.mode in ("tree", "all"):
        cands += tree_candidates()
    if args.mode in ("history", "all"):
        cands += history_candidates(args.rev_list)

    violations = check(cands, allow)
    if violations:
        print(f"FAIL: {len(violations)} non-whitelisted contact(s):")
        for v in violations:
            print(f"  - {v}")
        print(
            "Fix: allowlist it in contacts.allowlist.yaml (if public-safe) "
            "or remove/scrub it. History scrub is deferred — see docs/PLAN.md."
        )
        return 1
    print(f"OK: {len(cands)} contact candidate(s) checked, all whitelisted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
