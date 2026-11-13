"""Icon codec tests: artifact coverage, shipped JS parity, and size budget."""

from __future__ import annotations

import gzip
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from adapters.outbound import pixel_icons

ROOT = Path(__file__).resolve().parent.parent
CODEC_PATH = ROOT / "src/adapters/outbound/icon_codec.json"
JS_PATH = ROOT / "src/adapters/outbound/icon_codec.js"

NODE = shutil.which("node")


@pytest.fixture(scope="module")
def codec() -> dict:
    return json.loads(CODEC_PATH.read_text())


def test_codec_covers_every_icon(codec: dict) -> None:
    assert set(codec["latents"]) == set(pixel_icons.all_icon_names())
    assert set(codec["order"]) == set(codec["latents"])
    assert len(codec["order"]) == len(codec["latents"])


def test_every_symbol_has_a_paint_rule(codec: dict) -> None:
    for symbol in codec["symbols"]:
        if symbol == ".":
            continue
        assert symbol in codec["paint"], symbol
        rule = codec["paint"][symbol]
        assert ("class" in rule) ^ ("fill" in rule), symbol


def test_latents_are_evenly_spaced_on_the_circle(codec: dict) -> None:
    values = sorted(codec["latents"].values())
    assert values[0] >= 0.0
    assert values[-1] < 1.0
    step = 1 / len(values)
    for expected, actual in zip((i * step for i in range(len(values))), values, strict=True):
        assert actual == pytest.approx(expected, abs=1e-6)


def test_every_svg_is_marked_for_the_decoder() -> None:
    for name in pixel_icons.all_icon_names():
        assert f'data-pix="{name}"' in pixel_icons.svg(name)
    # Unknown names fall back to the default icon, and carry its marker.
    assert f'data-pix="{pixel_icons.DEFAULT_ICON}"' in pixel_icons.svg("no-such-icon")


def test_symbol_grid_is_16x16_and_uses_the_shared_alphabet(codec: dict) -> None:
    allowed = set(codec["symbols"])
    for name in pixel_icons.all_icon_names():
        rows = pixel_icons.symbol_grid(name)
        assert len(rows) == 16
        assert all(len(row) == 16 for row in rows)
        assert set("".join(rows)) <= allowed


def test_payload_fits_the_gzip_budget() -> None:
    assert len(gzip.compress(CODEC_PATH.read_bytes(), 9)) < 12_000


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_shipped_decoder_reproduces_every_anchor(codec: dict, tmp_path: Path) -> None:
    expected = {
        name: "".join(pixel_icons.symbol_grid(name)) for name in pixel_icons.all_icon_names()
    }
    expected_path = tmp_path / "expected.json"
    expected_path.write_text(json.dumps(expected))

    script = """
const fs = require("fs");
const { create } = require(process.argv[1]);
const codec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const expected = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const engine = create(codec);
const allowed = new Set(codec.symbols);
const bad = [];
for (const [name, grid] of Object.entries(expected)) {
  if (engine.gridFor(name, 0) !== grid) bad.push(name);
}
for (const phase of [0.13, 0.5, 0.77]) {
  for (const name of Object.keys(codec.latents)) {
    const grid = engine.gridFor(name, phase);
    if (grid.length !== 256) bad.push(name + "@" + phase + ":length");
    for (const ch of grid) if (!allowed.has(ch)) { bad.push(name + "@" + phase + ":symbol"); break; }
  }
}
if (bad.length) {
  console.error("decoder mismatches: " + bad.join(", "));
  process.exit(1);
}
"""
    result = subprocess.run(
        [NODE, "-e", script, str(JS_PATH), str(CODEC_PATH), str(expected_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_slider_redraws_every_svg() -> None:
    """Exercise boot() against a tiny fake DOM (no browser needed)."""
    script = r"""
const fs = require("fs");
const vm = require("vm");
const jsPath = process.argv[1];
const codecPath = process.argv[2];
const codecText = fs.readFileSync(codecPath, "utf8");
const jsText = fs.readFileSync(jsPath, "utf8");
const names = ["bank", "mail", "github", "chessboard"];  // bank's latent is 0.0
const svgs = names.map(function (name) {
  return {
    name: name,
    kids: [],
    getAttribute: function (key) { return key === "data-pix" ? name : null; },
    get firstChild() { return this.kids[0] || null; },
    removeChild: function (child) { this.kids = this.kids.filter(function (x) { return x !== child; }); },
    appendChild: function (child) { this.kids.push(child); },
  };
});
const listeners = {};
const slider = {
  value: "0", max: "1000", attrs: {},
  setAttribute: function (k, v) { this.attrs[k] = v; },
  addEventListener: function (kind, fn) { listeners[kind] = fn; },
};
let frame = null;
const readout = { textContent: "" };
const context = {
  console: console,
  URLSearchParams: URLSearchParams,
  atob: function (s) { return Buffer.from(s, "base64").toString("binary"); },
  document: {
    getElementById: function (id) {
      if (id === "pix-codec") return { textContent: codecText };
      if (id === "pix-z") return slider;
      if (id === "pix-z-out") return readout;
      return null;
    },
    querySelectorAll: function (sel) { return sel === "[data-pix]" ? svgs : []; },
    createElementNS: function () { return { attrs: {}, setAttribute: function (k, v) { this.attrs[k] = v; } }; },
  },
  window: { location: { search: "" } },
  localStorage: { getItem: function () { return null; }, setItem: function () {} },
  requestAnimationFrame: function (fn) { frame = fn; return 1; },
};
context.self = context;
vm.runInNewContext(jsText, context);
if (svgs.some(function (s) { return s.kids.length !== 0; })) {
  console.error("boot() redrew at phase 0");
  process.exit(1);
}
slider.value = "250";
listeners.input();
if (frame) frame();
const empty = svgs.filter(function (s) { return s.kids.length === 0; });
if (empty.length) {
  console.error("not redrawn: " + empty.map(function (s) { return s.name; }).join(","));
  process.exit(1);
}
if (slider.attrs["aria-valuetext"] !== "latent 0.25" || readout.textContent !== "latent 0.25") {
  console.error("aria/readout not updated");
  process.exit(1);
}
"""
    result = subprocess.run(
        [NODE, "-e", script, str(JS_PATH), str(CODEC_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
