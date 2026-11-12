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


def test_section_defaults_exist() -> None:
    for name in pixel_icons.SECTION_ICONS.values():
        assert name in pixel_icons.icon_names()


def test_content_icons_are_known() -> None:
    bundle = load(CONTENT)
    for item in [*bundle.research, *bundle.projects]:
        if item.icon:
            assert item.icon in pixel_icons.icon_names(), item.title
