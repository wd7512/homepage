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
    "o": "orcid",  # ORCID brand green (fixed in both themes)
    "s": "scholar",  # Scholar blue (fixed in both themes)
    "c": "scholarlight",
    "x": "white",  # pure white (fixed in both themes)
}


def _chart() -> tuple[str, ...]:
    """Three bars on an axis, 16 wide x 14 tall."""
    rows = []
    for r in range(13):
        cells = ["k"] + ["."] * 15
        for c0, top, ch in ((2, 7, "y"), (7, 4, "l"), (12, 1, "a")):
            if r >= top:
                cells[c0 : c0 + 4] = [ch] * 4
        rows.append("".join(cells))
    rows.append("k" * 16)
    return tuple(rows)


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


def _outlined(mask: tuple[str, ...], fill: str = "y") -> tuple[str, ...]:
    """Fill a ``#`` mask with ``fill`` and add a 1px ``k`` outline around it."""
    h, w = len(mask), len(mask[0])
    filled = {(y + 1, x + 1) for y, row in enumerate(mask) for x, c in enumerate(row) if c == "#"}
    rows = []
    for y in range(h + 2):
        row = ""
        for x in range(w + 2):
            if (y, x) in filled:
                row += fill
            elif any((y + dy, x + dx) in filled for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                row += "k"
            else:
                row += "."
        rows.append(row)
    return tuple(rows)


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
    """A runner leaning forward, with bent arms and a long stride."""
    return _sprite(
        [
            (
                "a",
                [
                    (9, 7),
                    (10, 6),
                    (11, 5),
                    (11, 4),
                    (11, 3),
                    (10, 2),
                    (9, 8),
                    (10, 9),
                    (11, 10),
                    (12, 9),
                    (13, 8),
                    (14, 8),
                ],
            ),
            (
                "r",
                [
                    (5, 8),
                    (5, 9),
                    (6, 7),
                    (6, 8),
                    (6, 9),
                    (7, 7),
                    (7, 8),
                    (8, 6),
                    (8, 7),
                    (8, 8),
                    (5, 6),
                    (5, 5),
                    (6, 4),
                    (6, 10),
                    (7, 11),
                    (7, 12),
                ],
            ),
            ("y", [(2, 10), (2, 11), (3, 9), (3, 10), (3, 11), (4, 9), (4, 4), (3, 4), (6, 13)]),
            ("n", [(1, 9), (1, 10), (1, 11), (2, 9), (9, 1), (9, 2), (14, 8), (14, 9)]),
        ]
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
    "battery": (
        "kkkkkkkkkkkkkk..",
        "kwwwwwwwwwwwwk..",
        "kgggwgggwgggwk..",
        "kgggwgggwgggwkkk",
        "kgggwgggwgggwkkk",
        "kgggwgggwgggwk..",
        "kwwwwwwwwwwwwk..",
        "kkkkkkkkkkkkkk..",
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
    "faultgrid": (
        "............y...",
        "............y...",
        "..........yyxyy.",
        "kkkkkkkkkkkky...",
        "kwwwklllkaaay...",
        "kwwwklllkaaak...",
        "kwwwklllkaaak...",
        "kkkkkkkkkkkkk...",
        "kaaakrrrklllk...",
        "kaaakrxrklllk...",
        "kaaakrrrklllk...",
        "kkkkkkkkkkkkk...",
        "klllkaaakwwwk...",
        "klllkaaakwwwk...",
        "klllkaaakwwwk...",
        "kkkkkkkkkkkkk...",
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
    "bulb": (
        "...kkkkkk...",
        "..kyyyyyyk..",
        ".kyyyyyyyyk.",
        "kyyxxyyyyyyk",
        "kyyxyyyyyyyk",
        "kyyyyyyyyyyk",
        "kyyyyyyyyyyk",
        "kyyyyyyyyyyk",
        ".kyyyyyyyyk.",
        "..kyyyyyyk..",
        "...kyyyyk...",
        "...kkkkkk...",
        "...kaaaak...",
        "...kkkkkk...",
        "....kaak....",
        ".....kk.....",
    ),
    "chart": _chart(),
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
    "computer": (
        ".kkkkkkkkkkkkkk.",
        ".kllllllllllllk.",
        ".klxxlllllllllk.",
        ".klxllllllllllk.",
        ".kllllllllllllk.",
        ".kllllllllllllk.",
        ".kllllllllllllk.",
        ".kkkkkkkkkkkkkk.",
        "......kaak......",
        "....kkkkkkkk....",
        "................",
        ".kkkkkkkkkkkkkk.",
        "kwwwwwwwwwwwwwwk",
        "kkkkkkkkkkkkkkkk",
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
    "flask": (
        "...kkkkkk...",
        "....kwwk....",
        "....kwwk....",
        "....kwwk....",
        "....kwwk....",
        "...kwwwwk...",
        "..kwwwwwwk..",
        ".kwwwwlwwwk.",
        ".kgxxgggggk.",
        "kggggggggggk",
        "kggxgggggggk",
        "kggggggggggk",
        "kggggggggggk",
        ".kggggggggk.",
        "..kkkkkkkk..",
    ),
    "heart": (
        "..kkkk....kkkk..",
        ".krrrrrkkrrrrrk.",
        "krrxrrrrrrrrrrrk",
        "krrrrrrrrrrrrrrk",
        "krrrrrrrrrrrrrrk",
        ".krrrrrrrrrrrrk.",
        "..krrrrrrrrrrk..",
        "...krrrrrrrrk...",
        "....krrrrrrk....",
        ".....krrrrk.....",
        "......krrk......",
        ".......kk.......",
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
    "pawn": (
        "....kkkk....",
        "..kkaaaakk..",
        "..klaaaaak..",
        "..klaaaaak..",
        "..kaaaaaak..",
        "...kaaaak...",
        "....kaak....",
        "..kkaaaakk..",
        "...klaaak...",
        "...klaaak...",
        "...kaaaak...",
        "..kaaaaaak..",
        ".kaaaaaaaak.",
        ".kaaaaaaaak.",
        "kaaaaaaaaaak",
        "kkkkkkkkkkkk",
    ),
    "pulse": _pulse(),
    "runner": _runner(),
    "pylon": (
        ".......kk.......",
        "......k..k......",
        "......k..k......",
        "....kkkkkkkk....",
        "...k..k..k..k...",
        ".....k.kk.k.....",
        ".....k.kk.k.....",
        "..kkkkkkkkkkkk..",
        ".k..k.k..k.k..k.",
        "....k..kk..k....",
        "....k.k..k.k....",
        "....kk....kk....",
        "...k..k..k..k...",
        "...k...kk...k...",
        "..k...k..k...k..",
        ".kkkkk....kkkkk.",
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
    "snake": (
        ".........kkkk...",
        "........kggggk..",
        "........kgxkgk..",
        "........kggggkrr",
        ".........kgggk..",
        "....kkkkkkggk...",
        "...kgggggggk....",
        "..kggkkkkkk.....",
        "..kggk..........",
        "...kggkkkkkk....",
        "....kgggggggk...",
        ".....kkkkkkggk..",
        "..kk......kggk..",
        ".kgkkkkkkkggk...",
        "..kggggggggk....",
        "...kkkkkkkk.....",
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
    "about": "bulb",
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
        '<svg class="pix" viewBox="0 0 16 16" shape-rendering="crispEdges" '
        f'aria-hidden="true" focusable="false">{body}</svg>'
    )
