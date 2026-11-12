"""Pixel icon tests: grid geometry, palette, rendering and content references."""

from pathlib import Path

import pytest

from adapters.inbound.markdown_loader import load
from adapters.outbound import pixel_icons

CONTENT = Path(__file__).resolve().parent.parent / "content"


@pytest.mark.parametrize("name", pixel_icons.icon_names())
def test_icon_is_16x16_with_known_palette(name: str) -> None:
    rows = pixel_icons.grid(name)
    assert len(rows) == 16
    assert all(len(r) == 16 for r in rows)
    assert set("".join(rows)) <= set(pixel_icons.PALETTE) | {"."}
    assert set("".join(rows)) != {"."}  # not blank


def test_svg_is_decorative_and_falls_back() -> None:
    out = pixel_icons.svg("book")
    assert 'aria-hidden="true"' in out
    assert 'viewBox="0 0 16 16"' in out
    assert pixel_icons.svg("no-such-icon") == pixel_icons.svg(pixel_icons.DEFAULT_ICON)


def test_section_and_link_icons_exist() -> None:
    for name in [*pixel_icons.SECTION_ICONS.values(), *pixel_icons.LINK_ICONS.values()]:
        assert name in pixel_icons.all_icon_names()


def test_content_icons_are_known() -> None:
    bundle = load(CONTENT)
    for item in [*bundle.research, *bundle.projects, *bundle.experience, *bundle.education]:
        if item.icon:
            assert item.icon in pixel_icons.all_icon_names(), item.title


@pytest.mark.parametrize("name", pixel_icons.icon_names())
def test_icon_is_not_tiny(name: str) -> None:
    """Whitespace is fine, but an icon should still be a sensible size (>= 8px)."""
    rows = pixel_icons.grid(name)
    xs = [x for r in rows for x, ch in enumerate(r) if ch != "."]
    ys = [y for y, r in enumerate(rows) if set(r) != {"."}]
    assert max(max(xs) - min(xs) + 1, max(ys) - min(ys) + 1) >= 8


@pytest.mark.parametrize("name", pixel_icons.logo_names())
def test_logo_is_16x16_and_renders(name: str) -> None:
    data = pixel_icons.LOGOS[name]
    assert len(data["rows"]) == pixel_icons.SIZE
    assert all(len(r) == pixel_icons.SIZE for r in data["rows"])
    used = set("".join(data["rows"])) - {"."}
    assert used and used <= set(data["palette"])
    out = pixel_icons.svg(name)
    assert 'aria-hidden="true"' in out and "<path" in out


def test_logos_cover_expected_brands() -> None:
    assert {"github", "linkedin", "orcid", "scholar", "steam", "bristol", "bath"} <= set(
        pixel_icons.logo_names()
    )
