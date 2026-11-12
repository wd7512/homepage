"""Tiny 16x16 pixel-art icons rendered as inline, theme-aware SVG.

Each icon is authored as a small character grid (at most 16x16) and padded,
centred, onto a 16x16 canvas. Characters index :data:`PALETTE`; ``.`` is
transparent. Colours are not hard-coded: every palette entry becomes a CSS
class (``ic-<char>``) whose fill is a custom property, so the icons follow the
page's light/dark theme. Icons are decorative (``aria-hidden``).
"""

from __future__ import annotations

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
    "o": "orcid",  # ORCID brand green (fixed in both themes)
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


# Every icon fills the 16x16 canvas on its longest side (enforced by tests).
_ART: dict[str, tuple[str, ...]] = {
    "agents": (
        ".kkkk......kkkk.",
        "kaaaak....kaaaak",
        "kaaaakkkkkkaaaak",
        "kaaaak....kaaaak",
        "kaaaak....kaaaak",
        ".kkkk......kkkk.",
        "..kk........kk..",
        "...kk......kk...",
        "....kk....kk....",
        "......kkkk......",
        ".....kyyyyk.....",
        ".....kyyyyk.....",
        ".....kyyyyk.....",
        ".....kyyyyk.....",
        "......kkkk......",
    ),
    "book": (
        ".kkkkkk..kkkkkk.",
        "kwwwwwwkkwwwwwwk",
        "kwaaaaakkaaaaawk",
        "kwwwwwwkkwwwwwwk",
        "kwaaaaakkaaaaawk",
        "kwwwwwwkkwwwwwwk",
        "kwaaaaakkaaaaawk",
        "kwwwwwwkkwwwwwwk",
        "kwaaaaakkaaaaawk",
        "kwwwwwwkkwwwwwwk",
        ".kkkkkkkkkkkkkk.",
    ),
    "briefcase": (
        "....kkkkkkkk....",
        "....k......k....",
        "kkkkkkkkkkkkkkkk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnyynnnnnnk",
        "kkkkkkkkkkkkkkkk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnnnnnnnnnk",
        "kkkkkkkkkkkkkkkk",
    ),
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
    "cap": (
        "......kkkk......",
        "....kkaaaakk....",
        "..kkaaaaaaaakk..",
        "kkaaaaaaaaaaaakk",
        ".kkaaaaaaaaaakk.",
        "..kkkkkkkkkkkky.",
        "....kwwwwwwk..y.",
        "....kwwwwwwk..y.",
        "....kwwwwwwk.yyy",
        "....kkkkkkkk....",
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
    "coin": (
        "....kkkkkkkk....",
        "..kkyyyyyyyykk..",
        ".kyyyyyyyyyyyyk.",
        ".kyyxxyyyyyyyyk.",
        "kyyxyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        ".kyyyyyyyyyyyyk.",
        ".kyyyyyyyyyyyyk.",
        "..kkyyyyyyyykk..",
        "....kkkkkkkk....",
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
        "..kkkkkkkk..",
        "....kwwk....",
        "....kwwk....",
        "....kwwk....",
        "....kwwk....",
        "...kwwwwk...",
        "..kwwwwwwk..",
        ".kwwwwwwwwk.",
        ".kwwggggwwk.",
        "kwggggggggwk",
        "kggxgggggggk",
        "kggggggggggk",
        "kgggggggxggk",
        "kggggggggggk",
        ".kggggggggk.",
        "..kkkkkkkk..",
    ),
    "folder": (
        "kkkkkk..........",
        "kyyyykkkkkkkkkk.",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kkkkkkkkkkkkkkkk",
    ),
    "github": (
        "..kk........kk..",
        ".kkkk......kkkk.",
        ".kwwkkkkkkkkwwk.",
        "kwwwwwwwwwwwwwwk",
        "kwwwwwwwwwwwwwwk",
        "kwwkkwwwwwwkkwwk",
        "kwwkkwwwwwwkkwwk",
        "kwwwwwwkkwwwwwwk",
        "kwwwwwwwwwwwwwwk",
        ".kwwwwwwwwwwwwk.",
        "..kwwwwwwwwwwk..",
        "...kkkwwwwkkk...",
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
    "linkedin": (
        "kkkkkkkkkkkkkkkk",
        "kaaaaaaaaaaaaaak",
        "kaaaaaaaaaaaaaak",
        "kaaaxxaaaaaaaaak",
        "kaaaxxaaaaaaaaak",
        "kaaaaaaaaaaaaaak",
        "kaaxxaaxxxxxxaak",
        "kaaxxaaxxxxxxaak",
        "kaaxxaaxxaaxxaak",
        "kaaxxaaxxaaxxaak",
        "kaaxxaaxxaaxxaak",
        "kaaxxaaxxaaxxaak",
        "kaaxxaaxxaaxxaak",
        "kaaaaaaaaaaaaaak",
        "kaaaaaaaaaaaaaak",
        "kkkkkkkkkkkkkkkk",
    ),
    "magnifier": (
        "...kkkkkkk......",
        ".kkwwwwwwwkk....",
        ".kwwwwwwwwwk....",
        "kwwwlllllwwwk...",
        "kwwlllllllwwk...",
        "kwwlllllllwwk...",
        "kwwlllllllwwk...",
        "kwwwlllllwwwk...",
        ".kwwwwwwwwwk....",
        ".kkwwwwwwwkkn...",
        "...kkkkkkk.nn...",
        "............nn..",
        ".............nn.",
        "..............kk",
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
    "mountain": (
        ".........kk.....",
        "........kxxk....",
        ".......kxxxxk...",
        "......kaxaxaak..",
        "...kkkaaaaaaaak.",
        "..kxkaaaaaaaaaak",
        ".kakaaaaaaaaaaak",
        "kakaaaaaaaaaaaak",
        "kaaaaaaaaaaaaaak",
        "kkkkkkkkkkkkkkkk",
    ),
    "orcid": (
        "....oooooooo....",
        "..oooooooooooo..",
        ".oooooooooooooo.",
        ".oooooooooooooo.",
        "oooxxoxxxxxooooo",
        "oooxxoxxxxxxoooo",
        "ooooooxxoooxxooo",
        "oooxxoxxoooxxooo",
        "oooxxoxxoooxxooo",
        "oooxxoxxoooxxooo",
        "oooxxoxxoooxxooo",
        "oooxxoxxxxxxoooo",
        ".ooxxoxxxxxoooo.",
        ".oooooooooooooo.",
        "..oooooooooooo..",
        "....oooooooo....",
    ),
    "pawn": (
        "....kkkk....",
        "..kkaaaakk..",
        "..kaaaaaak..",
        "..kaaxaaak..",
        "..kaaaaaak..",
        "...kaaaak...",
        "....kaak....",
        "..kkaaaakk..",
        "...kaaaak...",
        "...kaaaak...",
        "...kaaaak...",
        "..kaaaaaak..",
        ".kaaaaaaaak.",
        ".kaaaaaaaak.",
        "kaaaaaaaaaak",
        "kkkkkkkkkkkk",
    ),
    "pulse": _pulse(),
    "shield": (
        "kkkkkkkkkkkkkk",
        "kaaaaaallllllk",
        "kaaaaaallllllk",
        "kaaaaaallllllk",
        "kaaaaaallllllk",
        "kaaaaaallllllk",
        "kaaaaaallllllk",
        "kaaaaaallllllk",
        "kaaaaaallllllk",
        "kaaaaaallllllk",
        ".kaaaaalllllk.",
        "..kaaaallllk..",
        "...kaaalllk...",
        "....kaallk....",
        ".....kalk.....",
        "......kk......",
    ),
    "snake": (
        "gggggggggggggg..",
        "gggggggggggggg..",
        "gg..............",
        "gg..............",
        "gggggggggggggg..",
        "gggggggggggggg..",
        "............gg..",
        "............gg..",
        "gggggggggggggxkg",
        "gggggggggggggggr",
    ),
}

# Fallback icons for section headings / items with no (or an unknown) icon.
DEFAULT_ICON = "chip"
LINK_ICONS: dict[str, str] = {
    "email": "mail",
    "cv": "doc",
    "scholar": "cap",
    "orcid": "orcid",
    "github": "github",
    "linkedin": "linkedin",
}
SECTION_ICONS: dict[str, str] = {
    "about": "bulb",
    "publications": "book",
    "research": "flask",
    "education": "cap",
    "experience": "briefcase",
    "projects": "folder",
    "skills": "chip",
}


def icon_names() -> list[str]:
    return sorted(_ART)


def grid(name: str) -> list[str]:
    """Return the icon as exactly ``SIZE`` rows of ``SIZE`` characters."""
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


def svg(name: str | None, fallback: str = DEFAULT_ICON) -> str:
    """Inline decorative SVG for ``name`` (unknown names use ``fallback``)."""
    key = name if name in _ART else fallback
    rows = grid(key)
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
    body = "".join(
        f'<path class="ic-{PALETTE[ch]}" d="{"".join(segs)}"/>' for ch, segs in paths.items()
    )
    return (
        '<svg class="pix" viewBox="0 0 16 16" shape-rendering="crispEdges" '
        f'aria-hidden="true" focusable="false">{body}</svg>'
    )
