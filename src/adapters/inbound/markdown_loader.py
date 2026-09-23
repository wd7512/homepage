"""Inbound adapter: Markdown + YAML frontmatter -> domain bundle.

Each ``content/<section>/*.md`` file holds YAML frontmatter (validated
fail-fast against the Pydantic domain) plus a Markdown body. Bullets are
``- `` lines in the body; research/personal projects carry an explicit
``kind`` that must match their directory.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import ValidationError

from domain.models import (
    Activity,
    DomainBundle,
    Education,
    Experience,
    Personal,
    PersonalProject,
    Publication,
    ResearchProject,
    SkillCategory,
)

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)", re.DOTALL)


class ContentError(ValueError):
    """Raised when a content file fails to parse or validate."""


def parse_md(path: Path) -> tuple[dict, str]:
    """Split a Markdown file into (frontmatter dict, body str)."""
    text = path.read_text()
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ContentError(f"{path}: missing or malformed frontmatter block")
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise ContentError(f"{path}: invalid YAML frontmatter: {e}") from e
    if not isinstance(meta, dict):
        raise ContentError(f"{path}: frontmatter must be a mapping")
    return meta, m.group(2).strip()


def bullets(body: str) -> list[str]:
    """Extract ``- `` bullet lines from a Markdown body."""
    return [
        line[2:].strip() for line in body.splitlines() if line.startswith("- ") and line[2:].strip()
    ]


def _str_year(meta: dict) -> dict:
    """YAML parses `year: 2025` as int; the domain models year as a string."""
    if isinstance(meta.get("year"), int):
        meta = dict(meta)
        meta["year"] = str(meta["year"])
    return meta


def _build(model: type, path: Path, meta: dict, **extra) -> object:
    try:
        return model(**meta, **extra)
    except ValidationError as e:
        raise ContentError(f"{path}: schema validation failed:\n{e}") from e


def _load_dir(content: Path, dirname: str) -> list[tuple[Path, dict, str]]:
    folder = content / dirname
    if not folder.is_dir():
        return []
    out = []
    for path in sorted(folder.glob("*.md")):
        meta, body = parse_md(path)
        out.append((path, meta, body))
    return out


def load(content_dir: Path) -> DomainBundle:
    """Load and validate the whole content tree (fail-fast).

    Each section is sorted by explicit ``order`` then filename, so display
    order never depends on dates or file naming.
    """
    content = Path(content_dir)
    bundle = DomainBundle()

    personal_path = content / "personal.md"
    if personal_path.exists():
        meta, _body = parse_md(personal_path)
        bundle.personal = _build(Personal, personal_path, meta)

    for path, meta, body in _load_dir(content, "experience"):
        bundle.experience.append(
            _build(Experience, path, meta, bullets=bullets(body), slug=path.stem)
        )
    for path, meta, body in _load_dir(content, "education"):
        bundle.education.append(_build(Education, path, meta, bullets=bullets(body)))
    for path, meta, body in _load_dir(content, "research"):
        if "kind" in meta and meta["kind"] != "research":
            raise ContentError(f"{path}: research/ entry must have kind 'research'")
        bundle.research.append(_build(ResearchProject, path, _str_year(meta), body=body))
    for path, meta, body in _load_dir(content, "projects"):
        if "kind" in meta and meta["kind"] != "personal":
            raise ContentError(f"{path}: projects/ entry must have kind 'personal'")
        bundle.projects.append(_build(PersonalProject, path, _str_year(meta), body=body))
    for path, meta, _body in _load_dir(content, "publications"):
        bundle.publications.append(_build(Publication, path, meta))
    for path, meta, _body in _load_dir(content, "skills"):
        bundle.skills.append(_build(SkillCategory, path, meta))
    for path, meta, _body in _load_dir(content, "activities"):
        bundle.activities.append(_build(Activity, path, meta))

    for section in (
        bundle.experience,
        bundle.education,
        bundle.research,
        bundle.projects,
        bundle.publications,
        bundle.skills,
        bundle.activities,
    ):
        section.sort(key=lambda e: e.order)

    return bundle
