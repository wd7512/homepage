"""Logo converter tests: geometry, palette, ink mapping, and generated-file sync."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("PIL")
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "logos_to_pixels", ROOT / "scripts" / "logos_to_pixels.py"
)
tool = importlib.util.module_from_spec(_spec)
sys.modules["logos_to_pixels"] = tool
_spec.loader.exec_module(tool)


def test_convert_is_16x16_and_pads_non_square_images() -> None:
    img = Image.new("RGBA", (200, 100), (200, 30, 30, 255))
    data = tool.convert(img, colors=2)
    assert len(data["rows"]) == 16 and all(len(r) == 16 for r in data["rows"])
    # Wide image is padded to a square, so the top and bottom rows stay transparent.
    assert set(data["rows"][0]) == {"."} and set(data["rows"][-1]) == {"."}
    assert set(data["palette"].values()) == {"#c81e1e"}


def test_transparent_pixels_stay_transparent() -> None:
    img = Image.new("RGBA", (64, 64), (0, 120, 200, 255))
    for x in range(20, 44):
        for y in range(20, 44):
            img.putpixel((x, y), (0, 0, 0, 0))  # a hole in the middle
    data = tool.convert(img, colors=2)
    assert data["rows"][8][8] == "."
    assert data["rows"][0][0] != "."


def test_near_black_maps_to_ink_only_when_requested() -> None:
    img = Image.new("RGBA", (32, 32), (10, 10, 10, 255))
    assert set(tool.convert(img, colors=2, ink=True)["palette"].values()) == {"ink"}
    assert set(tool.convert(img, colors=2, ink=False)["palette"].values()) == {"#0a0a0a"}


def test_fully_transparent_logo_is_rejected() -> None:
    with pytest.raises(ValueError):
        tool.convert(Image.new("RGBA", (8, 8), (0, 0, 0, 0)), colors=2)


def test_generated_logo_file_is_in_sync_with_sources() -> None:
    committed = json.loads(tool.OUT_PATH.read_text())
    assert committed == tool.build()
