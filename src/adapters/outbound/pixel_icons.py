"""Tiny 16x16 pixel-art icons rendered as inline, theme-aware SVG.

Each icon is authored as a small character grid (at most 16x16) and padded,
centred, onto a 16x16 canvas. Characters index :data:`PALETTE`; ``.`` is
transparent. Colours are not hard-coded: every palette entry becomes a CSS
class (``ic-<char>``) whose fill is a custom property, so the icons follow the
page's light/dark theme. Icons are decorative (``aria-hidden``).
"""

from __future__ import annotations

import json
from pathlib import Path

SIZE = 16

# char -> CSS class suffix. Actual colours live in the page stylesheet.
PALETTE: dict[str, str] = {
    "k": "ink",  # outline
    "w": "paper",  # light fill (inverts in dark mode)
    "a": "blue",  # accent
    "l": "sky",  # light accent
    "y": "gold",
    "g": "green",
    "r": "red",
    "n": "brown",
    "h": "honey",  # light gold
    "s": "scholar",  # Scholar blue (fixed in both themes)
    "c": "scholarlight",
    "x": "white",  # pure white (fixed in both themes)
    "p": "cream",  # chessboard colours stay warm in both themes
    "t": "walnut",
    "v": "terminalbg",
    "e": "terminalgreen",
}

# Fixed colours used by the official logos. They extend the hand-drawn
# vocabulary so the latent codec can represent every icon with one alphabet.
EXTRA_COLOURS: dict[str, str] = {
    "L": "#0077b5",  # LinkedIn blue
    "O": "#a6ce39",  # ORCID green
    "B": "#081282",  # Bath navy
    "T": "#c4d8ef",  # Bath light blue
    "R": "#fbf4f5",  # Bristol near-white
    "S": "#c35461",  # Bristol maroon
}

_LOGO_SYMBOLS: dict[str, str] = {
    "ink": "k",
    "#ffffff": "x",
    **{colour: symbol for symbol, colour in EXTRA_COLOURS.items()},
}


def _pulse() -> tuple[str, ...]:
    """ECG trace (2px) inside a monitor frame, 16 wide x 9 tall."""
    inner = (
        ".....r........",
        "....r.r.......",
        "....r.r.......",
        "...r...r......",
        "rrr.....r.rrr.",
        ".........r.r..",
        "..........r...",
    )
    thick = []
    for row in inner:
        cells = list(row)
        for i, ch in enumerate(row):
            if ch == "r" and i + 1 < len(row) and cells[i + 1] == ".":
                cells[i + 1] = "r"
        thick.append("".join(cells))
    return ("k" * 16, *("k" + t + "k" for t in thick), "k" * 16)


def _sprite(layers: list[tuple[str, list[tuple[int, int]]]], after=()) -> tuple[str, ...]:
    """Compose coloured ``(y, x)`` layers, add a 1px ``k`` outline, then paint ``after``."""
    cells: dict[tuple[int, int], str] = {}
    for ch, pts in layers:
        for pt in pts:
            cells[pt] = ch
    out = dict(cells)
    for y, x in cells:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                n = (y + dy, x + dx)
                if n not in cells and 0 <= n[0] < SIZE and 0 <= n[1] < SIZE:
                    out[n] = "k"
    for ch, pts in after:
        for pt in pts:
            out[pt] = ch
    return tuple("".join(out.get((y, x), ".") for x in range(SIZE)) for y in range(SIZE))


def _climber() -> tuple[str, ...]:
    """A climber in a red helmet hanging from a rope (like the climbing emoji)."""
    layers = [
        ("a", [(6, 8), (5, 9), (4, 10), (3, 11), (7, 4), (8, 3)]),  # arms
        ("a", [(r, c) for r in range(6, 10) for c in (5, 6, 7)]),  # torso
        ("a", [(10, 5), (11, 4), (12, 4), (10, 7), (11, 8), (12, 9)]),  # legs
        ("n", [(9, 5), (9, 6), (9, 7), (13, 3), (13, 4), (13, 9), (13, 10)]),  # belt, boots
        ("y", [(2, 12), (9, 2)] + [(r, c) for r in (4, 5) for c in (5, 6, 7)]),  # hands, face
        ("r", [(2, 5), (2, 6), (2, 7)] + [(3, c) for c in range(4, 9)]),  # helmet
    ]
    return _sprite(layers, after=[("n", [(r, 13) for r in range(12)])])


def _runner() -> tuple[str, ...]:
    """A compact running stride with bent knees and a small speed trail."""
    return _sprite(
        [
            (
                "a",
                [
                    (9, 8),
                    (9, 9),
                    (10, 7),
                    (11, 6),
                    (10, 5),
                    (9, 5),
                    (10, 10),
                    (11, 11),
                    (12, 10),
                    (13, 9),
                ],
            ),
            (
                "r",
                [
                    (5, 9),
                    (5, 10),
                    (6, 8),
                    (6, 9),
                    (6, 10),
                    (7, 8),
                    (7, 9),
                    (8, 8),
                    (8, 9),
                    (6, 7),
                    (7, 6),
                    (6, 11),
                    (7, 12),
                ],
            ),
            (
                "y",
                [
                    (2, 10),
                    (2, 11),
                    (3, 10),
                    (3, 11),
                    (3, 12),
                    (4, 10),
                    (6, 6),
                    (5, 6),
                    (6, 13),
                    (5, 13),
                ],
            ),
            ("n", [(1, 10), (1, 11), (1, 12), (2, 10), (8, 4), (8, 5), (14, 9), (14, 10)]),
        ],
        after=[("l", [(5, 1), (5, 2), (5, 3), (8, 0), (8, 1), (8, 2), (11, 1), (11, 2)])],
    )


# Icons are centred on a 16x16 canvas; whitespace around them is fine.
_ART: dict[str, tuple[str, ...]] = {
    "book": (
        "..kkk......kkk..",
        ".kwwwkk..kkwwwk.",
        "kwwwwwwkkwwwwwwk",
        "kwaaaawkkwaaaawk",
        "kwwwwwwkkwwwwwwk",
        "kwaaawwkkwwaaawk",
        "kwwwwwwkkwwwwwwk",
        "kwaaaawkkwaaaawk",
        "kwwwwwwkkwwwwwwk",
        "kwwwkkkkkkkkwwwk",
        "kkkkaaakkaaakkkk",
        ".kaaakkkkkkaaak.",
        "..kkk......kkk..",
    ),
    "briefcase": (
        "....kkkkkkkk....",
        "....k......k....",
        ".kkkkkkkkkkkkkk.",
        "knnnnnnnnnnnnnnk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnyynnnnnnk",
        "knnnnnnyynnnnnnk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnnnnnnnnnk",
        ".kkkkkkkkkkkkkk.",
    ),
    "satellite": (
        "......kyyk......",
        ".......kk.......",
        ".......kk.......",
        "kkkkk.kkkk.kkkkk",
        "kaaak.kyyk.kaaak",
        "klllkkkyykkklllk",
        "kaaakkkyykkkaaak",
        "klllk.kyyk.klllk",
        "kkkkk.kkkk.kkkkk",
        ".......kk.......",
    ),
    "sock": (
        "..kkkkkkk.......",
        "..kawawak.......",
        "..kawawak.......",
        "..kaaaaak.......",
        "..kwwwwwk.......",
        "..kwrwrwk.......",
        "..kwrrrwk.......",
        "..kwwrwwk.......",
        ".kwwwwwwkkkk....",
        ".kawwwwwwwwwkk..",
        ".kaawwwwwwwwaak.",
        ".kaawwwwwwwaaak.",
        "..kkkkkkkkkkkk..",
    ),
    "wearable": (
        "....kkkkkkkk....",
        "....kaaaaaak....",
        "....kaaaaaak....",
        "....kaaaaaak....",
        "...kkkkkkkkkk...",
        "...kllllllllk...",
        "...klrrllrrlk...",
        "...klrrrrrrlk...",
        "...kllrrrrllk...",
        "...klllrrlllk...",
        "...kkkkkkkkkk...",
        "....kaaaaaak....",
        "....kaaaaaak....",
        "....kaaaaaak....",
        "....kkkkkkkk....",
    ),
    "lightning": (
        ".....kkkkkk.",
        "....khhyyyyk",
        "...khhyyyyk.",
        "...khyyyyk..",
        "..khhyyyk...",
        "..khyyyykkkk",
        ".khyyyyyyyyk",
        ".kyyyyyyyyk.",
        "..kkkyyyyk..",
        "...kyyyyk...",
        "...kyyyk....",
        "..kyyyk.....",
        "..kyyk......",
        ".kyyk.......",
        ".kyk........",
        "..k.........",
    ),
    "canvas": (
        "..kkkkkkkkkkkk..",
        "..kllllllllllk..",
        "..kllllllllyyk..",
        "..kllllllllyyk..",
        "..kllllllllllk..",
        "..kllllllllllk..",
        "..kgggglgggggk..",
        "..kggggggggggk..",
        "..kggggggggggk..",
        "..kkkkkkkkkkkk..",
        "...k...kk...k...",
        "..k....kk....k..",
        "..k....kk....k..",
        ".k.....kk.....k.",
        ".k.....kk.....k.",
    ),
    "scholar": (
        "......kkkk......",
        "....kkccsskk....",
        "..kkcsssssssskk.",
        "kkcssssssssssskk",
        ".kksssssyssssskk",
        "..kkkkkkkkkkkky.",
        "....kcccccck..y.",
        "....kcccccck..y.",
        "....ksccccsk.yyy",
        ".....kkkkkk..yyy",
    ),
    "certificate": (
        "kkkkkkkkkkkkkkk.",
        "kwwwwwwwwwwwwwk.",
        "kwwaaaaaaaaawwk.",
        "kwwwwwwwwwwwwwk.",
        "kwllllllllllwwk.",
        "kwlllllllwwwwwk.",
        "kwwwwwwwwkkkkwk.",
        "kwllllwwkrrrrkk.",
        "kwwwwwwkrrhrrrk.",
        "kkkkkkkkrhrrrrk.",
        "........krrrrk..",
        ".......krkkkrk..",
        ".......kk...kk..",
    ),
    "bank": (
        ".......kk.......",
        "......kwwk......",
        ".....kwwwwk.....",
        "....kwwwwwwk....",
        "...kwwwwwwwwk...",
        "..kkkkkkkkkkkk..",
        "...la..la..la...",
        "...la..la..la...",
        "...la..la..la...",
        "...la..la..la...",
        "..kkkkkkkkkkkk..",
        ".kkkkkkkkkkkkkk.",
    ),
    "ingot": (
        "............y...",
        "...kkkkkkkk.yxy.",
        "..khxxhhhhhk.y..",
        ".khhhhhhhhhhk...",
        "kyyyyyyyyyyyynk.",
        "kyyyyyyyyyyyynk.",
        "kyyyyyyyyyyyynk.",
        "kkkkkkkkkkkkkkk.",
    ),
    "cash": (
        "kkkkkkkkkkkkkkkk",
        "kggggggggggggggk",
        "kgxgggxxxxgggxgk",
        "kggggxggggxggggk",
        "kggggxgxxgxggggk",
        "kggggxggggxggggk",
        "kgxgggxxxxgggxgk",
        "kggggggggggggggk",
        "kkkkkkkkkkkkkkkk",
    ),
    "climber": _climber(),
    "chip": (
        "...k.k.k.k.k....",
        "...k.k.k.k.k....",
        "..kkkkkkkkkkkk..",
        "..kaaaaaaaaaak..",
        "kkkaaaaaaaaaakkk",
        "..kaallllllaak..",
        "kkkaallllllaakkk",
        "..kaallllllaak..",
        "kkkaallllllaakkk",
        "..kaaaaaaaaaak..",
        "kkkaaaaaaaaaakkk",
        "..kkkkkkkkkkkk..",
        "...k.k.k.k.k....",
        "...k.k.k.k.k....",
    ),
    "terminal": (
        ".kkkkkkkkkkkkkk.",
        "kvevevevvvvvvvvk",
        "kvvvvvvvvvvvvvvk",
        "kkkkkkkkkkkkkkkk",
        "kvvvvvvvvvvvvvvk",
        "kvvevvvvvvvvvvvk",
        "kvvvevvvvvvvvvvk",
        "kvvvvevvvvvvvvvk",
        "kvvvevvvvvvvvvvk",
        "kvvevvvveeeevvvk",
        "kvvvvvvvvvvvvvvk",
        "kvvvvvvvvvvvvvvk",
        "kvvvvvvvvvvvvvvk",
        ".kkkkkkkkkkkkkk.",
    ),
    "controller": (
        "..kkkkkkkkkkkk..",
        ".kllllllllllllk.",
        "klllkllllllylllk",
        "kllkkkllllrlrllk",
        "klllkllllllylllk",
        "kllllllllllllllk",
        "klllkkkkkkkklllk",
        "kllk........kllk",
        ".kk..........kk.",
    ),
    "doc": (
        "kkkkkkkkk...",
        "kwwwwwwwkk..",
        "kwwwwwwwkwk.",
        "kwwwwwwwkkkk",
        "kwwwwwwwwwwk",
        "kwaaaaaaaawk",
        "kwwwwwwwwwwk",
        "kwaaaaaaaawk",
        "kwwwwwwwwwwk",
        "kwaaaaaaaawk",
        "kwwwwwwwwwwk",
        "kwaaaaaawwwk",
        "kwwwwwwwwwwk",
        "kwaaaaaaaawk",
        "kwwwwwwwwwwk",
        "kkkkkkkkkkkk",
    ),
    "magnifier": (
        "...kkkk.........",
        ".kkxlllkk.......",
        ".kxlllllk.......",
        "kxlllllllk......",
        "kxlllllllk......",
        "kllllllllk......",
        "kllllllllk......",
        ".kllllllk.......",
        ".kkllllkkk......",
        "...kkkkknnk.....",
        "........knnk....",
        ".........knnk...",
        "..........knnk..",
        "...........knnk.",
        "............kkk.",
    ),
    "mail": (
        "kkkkkkkkkkkkkkkk",
        "kkkwwwwwwwwwwkkk",
        "kwwkkwwwwwwkkwwk",
        "kwwwwkkwwkkwwwwk",
        "kwwwwwwkkwwwwwwk",
        "kwwwwwwwwwwwwwwk",
        "kwwwwwwwwwwwwwwk",
        "kwwwwwwwwwwwwwwk",
        "kkkkkkkkkkkkkkkk",
    ),
    "pulse": _pulse(),
    "runner": _runner(),
    "pylon": (
        "................",
        "...........k....",
        "k.........klk...",
        ".k....kk..klk...",
        "..kkkk..kkklkkk.",
        "........yllllly.",
        "k.........klk...",
        ".k.....kkkklkkkk",
        "..k...kyllllllly",
        "...kkk...klalk..",
        ".........kl.lk..",
        "........kl.a.lk.",
        "........kl...lk.",
        ".......kll...llk",
        "................",
        "................",
    ),
    "neural_network": (
        "................",
        "................",
        ".kkk............",
        ".kak............",
        ".kkklllkkk......",
        "....l..kak......",
        "....lllkkkl.....",
        ".kkkll.l...lkkk.",
        ".kak..l.....kgk.",
        ".kkkll.l...lkkk.",
        "....lllkkkl.....",
        "....l..kak......",
        ".kkklllkkk......",
        ".kak............",
        ".kkk............",
        "................",
    ),
    "speech_bubble": (
        "..kkkkkkkkkkkk..",
        ".kwwwwwwwwwwwwk.",
        "kwwwwwwwwwwwwwwk",
        "kwwaaaaaaaaaawwk",
        "kwwwwwwwwwwwwwwk",
        "kwwaaaaaaaawwwwk",
        "kwwwwwwwwwwwwwwk",
        "kwwwwwwwwwwwwwwk",
        "kwwwwwwwwwwwwwwk",
        ".kwwwwwwwwwwwwk.",
        "..kkkkwwkkkkkk..",
        ".....kwk........",
        "....kwk.........",
        "....kk..........",
    ),
    "chessboard": (
        "ppttppttppttpptt",
        "ppttppttppttpptt",
        "ttppttppttppttpp",
        "ttppttppttppttpp",
        "ppttppttppttpptt",
        "ppttppttppttpptt",
        "ttppttppttppttpp",
        "ttppttppttppttpp",
        "ppttppttppttpptt",
        "ppttppttppttpptt",
        "ttppttppttppttpp",
        "ttppttppttppttpp",
        "ppttppttppttpptt",
        "ppttppttppttpptt",
        "ttppttppttppttpp",
        "ttppttppttppttpp",
    ),
    "snake": (
        "kkkkkkkkkkkkkkkk",
        "k..............k",
        "k..............k",
        "k..gg......rr..k",
        "k..gg......rr..k",
        "k..gg..........k",
        "k..gg...gggg...k",
        "k..gg...gggg...k",
        "k..gg...gg.....k",
        "k..ggggggg.....k",
        "k..ggggggg.....k",
        "k..............k",
        "k..............k",
        "k..............k",
        "k..............k",
        "kkkkkkkkkkkkkkkk",
    ),
}

# Fallback icons for section headings / items with no (or an unknown) icon.
DEFAULT_ICON = "chip"
LINK_ICONS: dict[str, str] = {
    "email": "mail",
    "cv": "doc",
    "scholar": "scholar",
    "orcid": "orcid",
    "github": "github",
    "linkedin": "linkedin",
}
SECTION_ICONS: dict[str, str] = {
    "publications": "book",
    "research": "magnifier",
    "education": "certificate",
    "experience": "briefcase",
    "projects": "canvas",
    "skills": "chip",
}


_LOGO_PATH = Path(__file__).with_name("logo_pixels.json")


def _load_logos() -> dict[str, dict]:
    if not _LOGO_PATH.exists():
        return {}
    return json.loads(_LOGO_PATH.read_text())


# Official logos converted by scripts/logos_to_pixels.py (see assets/logos/).
LOGOS: dict[str, dict] = _load_logos()


def icon_names() -> list[str]:
    """Hand-drawn icons (character grids)."""
    return sorted(_ART)


def logo_names() -> list[str]:
    return sorted(LOGOS)


def all_icon_names() -> list[str]:
    return sorted({*_ART, *LOGOS})


def grid(name: str) -> list[str]:
    """Return a hand-drawn icon as exactly ``SIZE`` rows of ``SIZE`` characters."""
    art = _ART[name]
    width = len(art[0])
    if any(len(row) != width for row in art):
        raise ValueError(f"icon {name!r} has ragged rows")
    if width > SIZE or len(art) > SIZE:
        raise ValueError(f"icon {name!r} is larger than {SIZE}x{SIZE}")
    left = (SIZE - width) // 2
    top = (SIZE - len(art)) // 2
    rows = ["." * SIZE] * top
    rows += ["." * left + row + "." * (SIZE - width - left) for row in art]
    rows += ["." * SIZE] * (SIZE - len(rows))
    return rows


def symbol_grid(name: str) -> list[str]:
    """Any icon (hand-drawn or logo) on the codec's shared symbol alphabet.

    Hand-drawn icons already use :data:`PALETTE`; logos are translated from
    their fixed brand colours into the matching symbol (see
    :data:`EXTRA_COLOURS`).  The result is what ``scripts/train_icons.py``
    learns and what the client-side decoder reproduces at its anchors.
    """
    if name in LOGOS:
        palette = LOGOS[name]["palette"]
        return [
            "".join("." if ch == "." else _LOGO_SYMBOLS[palette[ch]] for ch in row)
            for row in LOGOS[name]["rows"]
        ]
    return grid(name)


def paint() -> dict[str, dict[str, str]]:
    """Map each non-transparent symbol to how it is painted in the SVG."""
    out = {symbol: {"class": f"ic-{suffix}"} for symbol, suffix in PALETTE.items()}
    out.update({symbol: {"fill": colour} for symbol, colour in EXTRA_COLOURS.items()})
    return out


def _runs(rows: list[str]) -> dict[str, list[str]]:
    paths: dict[str, list[str]] = {}
    for y, row in enumerate(rows):
        x = 0
        while x < SIZE:
            ch = row[x]
            if ch == ".":
                x += 1
                continue
            start = x
            while x < SIZE and row[x] == ch:
                x += 1
            paths.setdefault(ch, []).append(f"M{start} {y}h{x - start}v1h-{x - start}z")
    return paths


def svg(name: str | None, fallback: str = DEFAULT_ICON) -> str:
    """Inline decorative SVG for ``name`` (unknown names use ``fallback``)."""
    if name in LOGOS:
        key = name
        data = LOGOS[name]
        body = ""
        for ch, segs in _runs(data["rows"]).items():
            colour = data["palette"][ch]
            attr = 'class="ic-ink"' if colour == "ink" else f'fill="{colour}"'
            body += f'<path {attr} d="{"".join(segs)}"/>'
    else:
        key = name if name in _ART else fallback
        body = "".join(
            f'<path class="ic-{PALETTE[ch]}" d="{"".join(segs)}"/>'
            for ch, segs in _runs(grid(key)).items()
        )
    return (
        f'<svg class="pix" data-pix="{key}" viewBox="0 0 16 16" '
        'shape-rendering="crispEdges" '
        f'aria-hidden="true" focusable="false">{body}</svg>'
    )
