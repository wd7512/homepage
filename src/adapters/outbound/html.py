"""Outbound adapter: domain bundle -> single-page academic site.

Renders the ``website`` channel of a :class:`DomainBundle` to a
self-contained ``index.html`` (inline CSS, inline dependency-free JS, no
external assets beyond Google Fonts). Design: minimal, text-first, single
column, research first, light/dark via ``prefers-color-scheme``, with tiny
decorative pixel-art icons (inline SVG, see
:mod:`adapters.outbound.pixel_icons`). A hidden footer slider slides the
icons' one-dimensional latent code. All text is HTML-escaped; sections render
only when they have website-visible entries.
"""

from __future__ import annotations

import html as _html
from pathlib import Path

from adapters.outbound import pixel_icons
from domain.models import DomainBundle, LinkItem

_HERE = Path(__file__).resolve().parent
_CODEC_PATH = _HERE / "icon_codec.json"
_JS_PATH = _HERE / "icon_codec.js"


def _asset(path: Path) -> str:
    return path.read_text() if path.exists() else ""


_CODEC = _asset(_CODEC_PATH)
_CODEC_JS = _asset(_JS_PATH)


def esc(text: str) -> str:
    return _html.escape(text, quote=True)


def _lis(items: list[str]) -> str:
    return "".join(f"<li>{esc(b)}</li>" for b in items)


def _authors(authors: str, highlight: str | None) -> str:
    """Escape an author list and emphasise the profile owner's name."""
    rendered = esc(authors)
    if highlight:
        target = esc(highlight)
        if target in rendered:
            rendered = rendered.replace(target, f"<strong>{target}</strong>", 1)
    return rendered


def _ext(href: str, label: str) -> str:
    return f'<a class="ext" href="{esc(href)}" target="_blank" rel="noopener">{esc(label)}</a>'


def _link_line(links: list[LinkItem]) -> str:
    if not links:
        return ""
    joined = " · ".join(_ext(str(link.url), link.label) for link in links)
    return f'<p class="links">{joined}</p>'


def _tag_line(tags: list[str]) -> str:
    return f'<p class="meta">{esc(", ".join(tags))}</p>' if tags else ""


def _icon(name: str | None) -> str:
    """Optional decorative icon (empty when the entry has none)."""
    return pixel_icons.svg(name) if name else ""


def _heading(section: str, title: str) -> str:
    icon = pixel_icons.svg(pixel_icons.SECTION_ICONS[section])
    return f"<h2>{icon}<span>{esc(title)}</span></h2>"


def _section(section: str, title: str, inner: str) -> str:
    return f'\n<section id="{section}">\n  {_heading(section, title)}\n{inner}\n</section>'


_CSS = """
    *, *::before, *::after { box-sizing: border-box; }
    html { -webkit-text-size-adjust: 100%; }

    :root {
      --bg: #ffffff;
      --text: #1b1b1b;
      --muted: #5f6368;
      --rule: #e4e4e4;
      --link: #1f4e8c;
      --link-hover: #0f2d57;
      --ic-ink: #2b2b2b;
      --ic-paper: #ffffff;
      --ic-blue: #4a6fa5;
      --ic-sky: #b4c9e6;
      --ic-gold: #e0b84a;
      --ic-green: #5a9a5a;
      --ic-red: #c8554f;
      --ic-brown: #b38e63;
      --ic-honey: #f3dc8b;
      --ic-scholar: #4285f4;
      --ic-scholarlight: #a1c2fa;
      --ic-white: #ffffff;
      --ic-cream: #f1dfbd;
      --ic-walnut: #845d42;
      --ic-terminalbg: #101b13;
      --ic-terminalgreen: #39ff78;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #16181b;
        --text: #e6e6e6;
        --muted: #9aa0a6;
        --rule: #2d3035;
        --link: #8db4e8;
        --link-hover: #b9d2f3;
        --ic-ink: #d6d6d6;
        --ic-paper: #2b2e33;
        --ic-blue: #6f94cc;
        --ic-sky: #a9c1e4;
        --ic-gold: #d9b24a;
        --ic-green: #6fb36f;
        --ic-red: #d9665f;
        --ic-brown: #a98159;
        --ic-honey: #e9cf7a;
      }
    }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: 'Source Serif 4', Georgia, 'Times New Roman', serif;
      font-size: 17px;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }
    header, main, footer { max-width: 720px; margin: 0 auto; padding-left: 20px; padding-right: 20px; }

    a { color: var(--link); text-decoration: none; }
    a:hover { color: var(--link-hover); text-decoration: underline; }
    a:focus-visible { outline: 2px solid var(--link); outline-offset: 2px; }

    .pix {
      width: 32px; height: 32px; flex: none;
      image-rendering: pixelated;
    }
    .ic-ink { fill: var(--ic-ink); }
    .ic-paper { fill: var(--ic-paper); }
    .ic-blue { fill: var(--ic-blue); }
    .ic-sky { fill: var(--ic-sky); }
    .ic-gold { fill: var(--ic-gold); }
    .ic-green { fill: var(--ic-green); }
    .ic-red { fill: var(--ic-red); }
    .ic-brown { fill: var(--ic-brown); }
    .ic-honey { fill: var(--ic-honey); }
    .ic-scholar { fill: var(--ic-scholar); }
    .ic-scholarlight { fill: var(--ic-scholarlight); }
    .ic-white { fill: var(--ic-white); }
    .ic-cream { fill: var(--ic-cream); }
    .ic-walnut { fill: var(--ic-walnut); }
    .ic-terminalbg { fill: var(--ic-terminalbg); }
    .ic-terminalgreen { fill: var(--ic-terminalgreen); }

    header { padding-top: 64px; padding-bottom: 8px; }
    h1 { font-size: 2.1rem; font-weight: 600; line-height: 1.15; margin: 0 0 6px; letter-spacing: -0.01em; }
    .role { margin: 0 0 14px; color: var(--muted); font-size: 1.05rem; }
    .contact { margin: 0; display: flex; flex-wrap: wrap; gap: 14px; margin-top: 4px; }
    .pbtn {
      position: relative; display: inline-flex; align-items: center; justify-content: center;
      width: 32px; height: 32px; transition: transform 0.08s;
    }
    .pbtn .pix { width: 32px; height: 32px; }
    .pbtn:hover { text-decoration: none; transform: translateY(-3px); }
    .pbtn::after {
      content: attr(data-tip); position: absolute; top: calc(100% + 10px); left: 50%;
      transform: translateX(-50%); background: var(--ic-ink); color: var(--bg);
      font-size: 0.75rem; line-height: 1.4; padding: 2px 8px; white-space: nowrap;
      opacity: 0; pointer-events: none; transition: opacity 0.1s; z-index: 2;
    }
    .pbtn:hover::after, .pbtn:focus-visible::after { opacity: 1; }
    @media (prefers-reduced-motion: reduce) {
      .pbtn, .pbtn::after { transition: none; }
      .pbtn:hover { transform: none; }
    }

    section { margin-top: 44px; }
    #about { padding-top: 12px; }
    h2 {
      display: flex; align-items: center; gap: 0.5em;
      font-size: 1.3rem; font-weight: 600; margin: 0 0 16px;
      padding-bottom: 6px; border-bottom: 1px solid var(--rule);
    }
    h3 { font-size: 1rem; font-weight: 600; margin: 0; }
    p { margin: 0 0 10px; }
    .meta { color: var(--muted); font-size: 0.92rem; }
    .links { font-size: 0.92rem; }
    .when, .period { color: var(--muted); font-size: 0.92rem; font-variant-numeric: tabular-nums; white-space: nowrap; }

    ol.pubs { list-style: none; margin: 0; padding: 0; }
    ol.pubs li { margin: 0 0 14px; }
    .pub-title { font-weight: 500; }
    .note { color: var(--muted); font-style: italic; }

    .item { margin: 0 0 22px; }
    .item-head {
      display: flex; align-items: baseline; justify-content: space-between; gap: 16px;
    }
    .item-head h3 { display: flex; align-items: center; gap: 0.5em; }
    .item-head h3 .pix { align-self: center; margin: -6px 0; }
    .item p { margin: 4px 0 6px; font-size: 0.97rem; }
    .sub { margin: 0; color: var(--muted); font-style: italic; font-size: 0.95rem; }
    .item ul { margin: 6px 0 0; padding-left: 1.2em; font-size: 0.95rem; }
    .item li { margin-bottom: 3px; }

    ul.plain { list-style: none; margin: 0; padding: 0; }
    ul.plain li { margin: 0 0 12px; font-size: 0.97rem; }
    ul.plain .pix { vertical-align: middle; margin: -6px 0.45em -6px 0; }

    dl.skills { margin: 0; display: grid; grid-template-columns: max-content 1fr; gap: 6px 20px; font-size: 0.97rem; }
    dl.skills dt { font-weight: 600; }
    dl.skills dd { margin: 0; color: var(--muted); }

    footer { margin-top: 56px; padding-top: 16px; padding-bottom: 40px; border-top: 1px solid var(--rule); color: var(--muted); font-size: 0.85rem; }

    .sr-only {
      position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
      overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0;
    }
    /* The slider is a 1px hairline until you hover or focus it. */
    .latent { position: relative; margin-top: 14px; height: 12px; }
    .latent input[type="range"] {
      -webkit-appearance: none; appearance: none; position: absolute; inset: 0;
      width: 100%; height: 12px; margin: 0; padding: 0;
      background: transparent; cursor: ew-resize;
    }
    .latent input[type="range"]::-webkit-slider-runnable-track {
      height: 1px; background: var(--rule);
    }
    .latent input[type="range"]::-moz-range-track {
      height: 1px; background: var(--rule);
    }
    .latent input[type="range"]::-webkit-slider-thumb {
      -webkit-appearance: none; width: 6px; height: 6px; margin-top: -2.5px;
      border-radius: 50%; background: var(--muted); opacity: 0;
      transition: opacity 0.12s;
    }
    .latent input[type="range"]::-moz-range-thumb {
      width: 6px; height: 6px; border: 0; border-radius: 50%;
      background: var(--muted); opacity: 0; transition: opacity 0.12s;
    }
    .latent:hover input[type="range"]::-webkit-slider-thumb,
    .latent input[type="range"]:focus-visible::-webkit-slider-thumb { opacity: 0.7; }
    .latent:hover input[type="range"]::-moz-range-thumb,
    .latent input[type="range"]:focus-visible::-moz-range-thumb { opacity: 0.7; }
    .latent:focus-within input[type="range"]::-webkit-slider-runnable-track,
    .latent:hover input[type="range"]::-webkit-slider-runnable-track { background: var(--muted); }
    .latent:focus-within input[type="range"]::-moz-range-track,
    .latent:hover input[type="range"]::-moz-range-track { background: var(--muted); }
    .latent-out {
      position: absolute; right: 0; top: -17px; font-size: 0.7rem;
      color: var(--muted); font-variant-numeric: tabular-nums;
      opacity: 0; transition: opacity 0.12s; pointer-events: none;
    }
    .latent:hover .latent-out, .latent:focus-within .latent-out { opacity: 1; }
    @media (prefers-reduced-motion: reduce) {
      .latent input[type="range"]::-webkit-slider-thumb,
      .latent input[type="range"]::-moz-range-thumb,
      .latent-out { transition: none; }
    }

    @media (max-width: 600px) {
      body { font-size: 16px; }
      header { padding-top: 40px; }
      h1 { font-size: 1.75rem; }
      .item-head { flex-direction: column; gap: 0; }
      dl.skills { grid-template-columns: 1fr; gap: 0; }
      dl.skills dd { margin-bottom: 8px; }
    }
"""


def render_site(bundle: DomainBundle) -> str:
    """Render the website-visible slice of the bundle to index.html."""
    web = bundle.visible("website")
    personal = web.personal
    if personal is None:
        raise ValueError("content/personal.md is required to render the site")

    name = esc(personal.name)

    def pbtn(kind: str, label: str, href: str, external: bool = True) -> str:
        target = ' target="_blank" rel="noopener"' if external else ""
        return (
            f'<a class="pbtn" href="{esc(href)}"{target} aria-label="{esc(label)}" '
            f'data-tip="{esc(label)}">{pixel_icons.svg(pixel_icons.LINK_ICONS[kind])}</a>'
        )

    contact_links = [pbtn("email", "Email", f"mailto:{personal.email}", external=False)]
    if personal.cv_pdf:
        contact_links.append(pbtn("cv", "CV (PDF)", personal.cv_pdf))
    if personal.scholar:
        contact_links.append(pbtn("scholar", "Google Scholar", str(personal.scholar)))
    if personal.orcid:
        contact_links.append(pbtn("orcid", "ORCID", str(personal.orcid)))
    contact_links.append(pbtn("github", "GitHub", str(personal.github)))
    contact_links.append(pbtn("linkedin", "LinkedIn", str(personal.linkedin)))
    contact = "".join(contact_links)

    sections_html = ""

    if personal.research_statement:
        sections_html += f'\n<p id="about">{esc(personal.research_statement)}</p>'

    if web.publications:
        items = []
        for p in web.publications:
            title = (
                f'<a class="pub-title" href="{esc(str(p.link))}" target="_blank" '
                f'rel="noopener">{esc(p.title)}</a>'
                if p.link
                else f'<span class="pub-title">{esc(p.title)}</span>'
            )
            note = (
                f' <span class="note">({esc(p.status.lower())})</span>'
                if p.status != "Published"
                else ""
            )
            items.append(
                f"    <li>{_authors(p.authors.rstrip('. ') if p.authors.endswith('.') else p.authors, p.highlight_author)}. {title}. "
                f"<em>{esc(p.venue)}</em>, {esc(p.date)}.{note}</li>"
            )
        sections_html += _section(
            "publications", "Publications", '  <ol class="pubs">\n' + "\n".join(items) + "\n  </ol>"
        )

    if web.research:
        items = [
            '  <article class="item">\n'
            '    <div class="item-head">\n'
            f"      <h3>{pixel_icons.svg(r.icon, pixel_icons.SECTION_ICONS['research'])}"
            f"<span>{esc(r.title)}</span></h3>\n"
            f'      <span class="when">{esc(r.year)}</span>\n'
            "    </div>\n"
            f"    <p>{esc(r.body)}</p>\n"
            f"    {_tag_line(r.tags)}\n"
            f"    {_link_line(r.links)}\n"
            "  </article>"
            for r in web.research
        ]
        sections_html += _section("research", "Research", "\n".join(items))

    if web.education:
        items = [
            '  <article class="item">\n'
            '    <div class="item-head">\n'
            f"      <h3>{_icon(e.icon)}<span>{esc(e.institution)}</span></h3>\n"
            f'      <span class="period">{esc(e.period)}</span>\n'
            "    </div>\n"
            f'    <p class="sub">{esc(e.degree)}</p>\n'
            + (f'    <p class="meta">{esc(e.details)}</p>\n' if e.details else "")
            + f"    <ul>{_lis(e.bullets)}</ul>\n"
            + "  </article>"
            for e in web.education
        ]
        sections_html += _section("education", "Education", "\n".join(items))

    if web.experience:
        items = [
            '  <article class="item">\n'
            '    <div class="item-head">\n'
            f"      <h3>{_icon(e.icon)}<span>{esc(e.role)}</span></h3>\n"
            f'      <span class="period">{esc(e.period)}</span>\n'
            "    </div>\n"
            f'    <p class="sub">{esc(e.company)} · {esc(e.location)}</p>\n'
            f"    <ul>{_lis(e.bullets)}</ul>\n"
            "  </article>"
            for e in web.experience
        ]
        sections_html += _section("experience", "Experience", "\n".join(items))

    if web.projects:
        items = [
            "    <li>"
            f"{pixel_icons.svg(p.icon, pixel_icons.SECTION_ICONS['projects'])}"
            f"<strong>{esc(p.title)}</strong> "
            f'<span class="when">({esc(p.year)})</span>. {esc(p.body)}'
            + (
                " " + " · ".join(_ext(str(link.url), link.label) for link in p.links)
                if p.links
                else ""
            )
            + "</li>"
            for p in web.projects
        ]
        sections_html += _section(
            "projects",
            "Personal Projects",
            '  <ul class="plain">\n' + "\n".join(items) + "\n  </ul>",
        )

    if web.skills:
        rows = "\n".join(
            f"    <dt>{esc(s.category)}</dt><dd>{esc(', '.join(s.skills))}</dd>" for s in web.skills
        )
        sections_html += _section(
            "skills", "Technical Skills", f'  <dl class="skills">\n{rows}\n  </dl>'
        )

    if _CODEC and _CODEC_JS:
        latent = (
            '  <div class="latent">\n'
            '    <label class="sr-only" for="pix-z">Icon latent phase</label>\n'
            '    <input id="pix-z" type="range" min="0" max="1000" step="1" value="0" '
            'aria-label="Icon latent phase" aria-valuetext="latent 0.00">\n'
            '    <span id="pix-z-out" class="latent-out" aria-hidden="true">latent 0.00</span>\n'
            "  </div>"
        )
        scripts = (
            '<script type="application/json" id="pix-codec">'
            + _CODEC.replace("</", "<\\/")
            + "</script>\n<script>"
            + _CODEC_JS
            + "</script>"
        )
    else:
        latent = ""
        scripts = ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light dark">
  <title>{name} | {esc(personal.title)}</title>
  <meta name="description" content="{esc(personal.tagline)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
  <style>{_CSS}
  </style>
</head>
<body>

<header>
  <h1>{name}</h1>
  <p class="role">{esc(personal.title)}</p>
  <p class="contact">{contact}</p>
</header>

<main>{sections_html}
</main>

<footer>
  <p>© {name} · <a href="https://github.com/wd7512/homepage/blob/main/content/">Source content</a></p>
{latent}
</footer>

{scripts}
</body>
</html>
"""
