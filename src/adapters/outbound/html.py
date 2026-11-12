"""Outbound adapter: domain bundle -> single-page academic site.

Renders the ``website`` channel of a :class:`DomainBundle` to a
self-contained ``index.html`` (inline CSS, no JS, no external assets beyond
Google Fonts). Design: minimal, text-first, single column, research first,
light/dark via ``prefers-color-scheme``, with tiny decorative pixel-art icons
(inline SVG, see :mod:`adapters.outbound.pixel_icons`). All text is
HTML-escaped; sections render only when they have website-visible entries.
"""

from __future__ import annotations

import html as _html

from adapters.outbound import pixel_icons
from domain.models import DomainBundle, LinkItem


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


def _ext(href: str, label: str, cls: str = ' class="ext"') -> str:
    return f'<a{cls} href="{esc(href)}" target="_blank" rel="noopener">{esc(label)}</a>'


def _link_line(links: list[LinkItem]) -> str:
    if not links:
        return ""
    joined = " · ".join(_ext(str(link.url), link.label) for link in links)
    return f'<p class="links">{joined}</p>'


def _tag_line(tags: list[str]) -> str:
    return f'<p class="meta">{esc(", ".join(tags))}</p>' if tags else ""


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
      --ic-brown: #9a7451;
      --ic-orcid: #a6ce39;
      --ic-white: #ffffff;
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
        --ic-sky: #3d5a85;
        --ic-gold: #d9b24a;
        --ic-green: #6fb36f;
        --ic-red: #d9665f;
        --ic-brown: #a98159;
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
    .ic-orcid { fill: var(--ic-orcid); }
    .ic-white { fill: var(--ic-white); }

    header { padding-top: 64px; padding-bottom: 8px; }
    h1 { font-size: 2.1rem; font-weight: 600; line-height: 1.15; margin: 0 0 6px; letter-spacing: -0.01em; }
    .role { margin: 0 0 14px; color: var(--muted); font-size: 1.05rem; }
    .contact { margin: 0; display: flex; flex-wrap: wrap; gap: 14px; margin-top: 4px; }
    .pbtn {
      position: relative; display: inline-flex; align-items: center; justify-content: center;
      width: 48px; height: 48px; transition: transform 0.08s;
    }
    .pbtn .pix { width: 48px; height: 48px; }
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
    h2 {
      display: flex; align-items: center; gap: 0.5em;
      font-size: 1.3rem; font-weight: 600; margin: 0 0 16px;
      padding-bottom: 6px; border-bottom: 1px solid var(--rule);
    }
    h3 { font-size: 1rem; font-weight: 600; margin: 0; }
    p { margin: 0 0 10px; }
    .interests, .meta { color: var(--muted); font-size: 0.92rem; }
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
        sections_html += _section("about", "About", f"  <p>{esc(personal.research_statement)}</p>")

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
            f"      <h3>{esc(e.institution)}</h3>\n"
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
            f"      <h3>{esc(e.role)}</h3>\n"
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
</footer>

</body>
</html>
"""
