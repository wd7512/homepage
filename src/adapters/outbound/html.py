"""Outbound adapter: domain bundle -> single-page portfolio site.

Renders the ``website`` channel of a :class:`DomainBundle` to a
self-contained ``index.html`` (inline CSS, no JS, no external assets beyond
Google Fonts). Visual design ported from the retired ``home`` repo: dark
theme, fixed nav, hero, timeline experience, card grids. All text is
HTML-escaped; sections render only when they have website-visible entries.
"""

from __future__ import annotations

import html as _html

from domain.models import DomainBundle


def esc(text: str) -> str:
    return _html.escape(text, quote=True)


def _lis(items: list[str]) -> str:
    return "".join(f"<li>{esc(b)}</li>" for b in items)


def _tags(tags: list[str]) -> str:
    if not tags:
        return ""
    spans = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags)
    return f'<div class="tags">{spans}</div>'


_CSS = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #0f172a;
      --bg-card: #1e293b;
      --bg-card-hover: #263348;
      --text: #e2e8f0;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --accent: #818cf8;
      --accent-dim: #4f46e5;
      --border: #334155;
      --success: #34d399;
      --pending: #fbbf24;
      --radius: 12px;
      --max-w: 1100px;
    }

    html { scroll-behavior: smooth; }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }

    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }

    .container { max-width: var(--max-w); margin: 0 auto; padding: 0 24px; }
    section { padding: 80px 0; }
    .section-title {
      font-size: 1.75rem; font-weight: 700; margin-bottom: 48px;
      padding-bottom: 16px; border-bottom: 2px solid var(--accent-dim);
      display: inline-block;
    }

    nav {
      position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
    }
    nav .container {
      display: flex; justify-content: space-between; align-items: center;
      height: 56px;
    }
    nav .logo { font-weight: 700; color: var(--text); font-size: 1.1rem; }
    nav .logo:hover { text-decoration: none; color: var(--accent); }
    nav .links { display: flex; gap: 24px; }
    nav .links a { color: var(--text-muted); font-size: 0.875rem; font-weight: 500; }
    nav .links a:hover { color: var(--text); text-decoration: none; }

    #hero {
      min-height: 100vh; display: flex; align-items: center;
      padding-top: 56px;
      background: radial-gradient(ellipse at 50% 0%, rgba(99, 102, 241, 0.08) 0%, transparent 60%);
    }
    #hero h1 { font-size: 3rem; font-weight: 700; line-height: 1.1; margin-bottom: 16px; }
    #hero .subtitle { font-size: 1.25rem; color: var(--text-muted); margin-bottom: 32px; max-width: 560px; }
    #hero .cta { display: flex; gap: 16px; flex-wrap: wrap; }
    .btn {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 10px 20px; border-radius: 8px; font-weight: 500; font-size: 0.875rem;
      transition: all 0.15s;
    }
    .btn-primary { background: var(--accent-dim); color: white; }
    .btn-primary:hover { background: var(--accent); text-decoration: none; }
    .btn-outline { border: 1px solid var(--border); color: var(--text); }
    .btn-outline:hover { border-color: var(--text-muted); text-decoration: none; }

    .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; margin-bottom: 20px; transition: border-color 0.15s; }
    .card:hover { border-color: var(--text-dim); }
    .card h3 { font-size: 1.1rem; font-weight: 600; margin-bottom: 4px; }
    .card h4 { font-size: 1rem; font-weight: 600; }
    .card .meta { color: var(--accent); font-size: 0.875rem; font-weight: 500; }
    .card .period { color: var(--text-dim); font-size: 0.8rem; font-family: monospace; }
    .card ul { margin-top: 12px; padding-left: 20px; }
    .card li { color: var(--text-muted); font-size: 0.875rem; margin-bottom: 4px; }
    .card p { color: var(--text-muted); font-size: 0.875rem; margin: 8px 0; }

    .card-header {
      display: flex; justify-content: space-between; align-items: baseline;
      margin-bottom: 8px;
    }

    .timeline { position: relative; }
    .timeline::before {
      content: ''; position: absolute; left: 19px; top: 0; bottom: 0;
      width: 2px; background: var(--border);
    }
    .timeline-item { position: relative; padding-left: 56px; margin-bottom: 32px; }
    .timeline-dot {
      position: absolute; left: 12px; top: 24px;
      width: 16px; height: 16px; border-radius: 50%;
      background: var(--bg-card); border: 3px solid var(--accent-dim);
    }

    .edu-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 24px; }
    .edu-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
    .badge {
      display: inline-block; margin: 8px 0 16px; padding: 4px 12px;
      background: rgba(251, 191, 36, 0.1); color: var(--pending);
      border: 1px solid rgba(251, 191, 36, 0.2);
      border-radius: 99px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
    }

    .research-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
    @media (max-width: 768px) { .research-grid { grid-template-columns: 1fr; } }

    .projects-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
    .project-card { display: flex; flex-direction: column; }
    .project-card p { flex-grow: 1; }
    .project-card > .link-btn { align-self: flex-start; }

    .tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
    .tag {
      padding: 2px 10px; background: rgba(129, 140, 248, 0.1);
      color: var(--accent); border: 1px solid rgba(129, 140, 248, 0.2);
      border-radius: 99px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .links { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
    .link-btn {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 6px 14px; background: rgba(129, 140, 248, 0.1);
      border: 1px solid rgba(129, 140, 248, 0.2); border-radius: 6px;
      font-size: 0.8rem; font-weight: 500; color: var(--accent);
    }
    .link-btn:hover { background: rgba(129, 140, 248, 0.2); text-decoration: none; }

    .pub-item {
      padding: 20px; border-left: 3px solid var(--accent-dim);
      background: var(--bg-card); border-radius: 0 var(--radius) var(--radius) 0;
      margin-bottom: 16px;
    }
    .pub-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 4px; }
    .pub-top h4 { font-size: 0.95rem; font-weight: 600; }
    .pub-top h4 a { color: var(--text); }
    .pub-top h4 a:hover { color: var(--accent); }
    .authors { color: var(--text-muted); font-size: 0.85rem; margin-bottom: 8px; }
    .pub-bottom { display: flex; justify-content: space-between; gap: 12px; padding-top: 8px; border-top: 1px solid var(--border); }
    .pub-bottom .period { white-space: nowrap; }
    .venue { color: var(--accent); font-size: 0.8rem; font-weight: 500; }
    .status {
      padding: 2px 10px; border-radius: 99px; font-size: 0.7rem;
      font-weight: 600; text-transform: uppercase; white-space: nowrap;
    }
    .status.published { background: rgba(52, 211, 153, 0.1); color: var(--success); }
    .status.pending { background: rgba(251, 191, 36, 0.1); color: var(--pending); }

    .skills-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 32px; }
    .skill-group h3 { font-size: 1rem; font-weight: 600; color: var(--text-muted); margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
    .skills { display: flex; flex-wrap: wrap; gap: 8px; }
    .skill {
      padding: 6px 14px; background: var(--bg-card); border: 1px solid var(--border);
      border-radius: 8px; font-size: 0.85rem; color: var(--text);
    }

    footer { padding: 40px 0; border-top: 1px solid var(--border); text-align: center; color: var(--text-dim); font-size: 0.85rem; }

    @media (max-width: 640px) {
      #hero h1 { font-size: 2rem; }
      nav .links { gap: 16px; }
      nav .links a { font-size: 0.8rem; }
      section { padding: 60px 0; }
      .timeline::before { left: 9px; }
      .timeline-item { padding-left: 36px; }
      .timeline-dot { left: 2px; width: 14px; height: 14px; }
    }
"""


def render_site(bundle: DomainBundle) -> str:
    """Render the website-visible slice of the bundle to index.html."""
    web = bundle.visible("website")
    personal = web.personal
    if personal is None:
        raise ValueError("content/personal.md is required to render the site")

    name = esc(personal.name)
    email = esc(str(personal.email))
    linkedin = esc(str(personal.linkedin))
    github = esc(str(personal.github))
    cv_pdf = esc(personal.cv_pdf) if personal.cv_pdf else None

    cta = (
        f'<a href="mailto:{email}" class="btn btn-primary">Email Me</a>\n'
        f'      <a href="{linkedin}" class="btn btn-outline" target="_blank" rel="noopener">LinkedIn</a>\n'
        f'      <a href="{github}" class="btn btn-outline" target="_blank" rel="noopener">GitHub</a>'
    )
    if cv_pdf:
        cta += f'\n      <a href="{cv_pdf}" class="btn btn-outline" target="_blank" rel="noopener">Download CV (PDF)</a>'

    nav_links = ""
    if web.experience:
        nav_links += '\n      <a href="#experience">Experience</a>'
    if web.education:
        nav_links += '\n      <a href="#education">Education</a>'
    if web.research or web.publications:
        nav_links += '\n      <a href="#research">Research</a>'
    if web.projects:
        nav_links += '\n      <a href="#projects">Projects</a>'
    if web.skills:
        nav_links += '\n      <a href="#skills">Skills</a>'

    sections_html = ""

    if web.experience:
        items = "".join(
            '        <div class="timeline-item">\n'
            '          <div class="timeline-dot"></div>\n'
            '          <div class="card">\n'
            f"            <h3>{esc(e.role)}</h3>\n"
            f'            <div class="meta">{esc(e.company)} · {esc(e.location)}</div>\n'
            f'            <div class="period">{esc(e.period)}</div>\n'
            f"            <ul>{_lis(e.bullets)}</ul>\n"
            "          </div>\n"
            "        </div>"
            for e in web.experience
        )
        sections_html += (
            '\n<section id="experience">\n  <div class="container">\n'
            '    <h2 class="section-title">Experience</h2>\n'
            f'    <div class="timeline">{items}</div>\n'
            "  </div>\n</section>"
        )

    if web.education:
        items = "".join(
            '        <div class="card">\n'
            '          <div class="edu-header">\n'
            "            <div>\n"
            f"              <h3>{esc(e.institution)}</h3>\n"
            f'              <div class="meta">{esc(e.degree)}</div>\n'
            "            </div>\n"
            f'            <span class="period">{esc(e.period)}</span>\n'
            "          </div>\n"
            + (f'          <div class="badge">{esc(e.details)}</div>\n' if e.details else "")
            + f"          <ul>{_lis(e.bullets)}</ul>\n"
            + "        </div>"
            for e in web.education
        )
        sections_html += (
            '\n<section id="education">\n  <div class="container">\n'
            '    <h2 class="section-title">Education</h2>\n'
            f'    <div class="edu-grid">{items}</div>\n'
            "  </div>\n</section>"
        )

    if web.research or web.publications:
        pub_items = "".join(
            '        <div class="pub-item">\n'
            '          <div class="pub-top">\n'
            + (
                f'            <h4><a href="{esc(str(p.link))}" target="_blank" rel="noopener">{esc(p.title)}</a></h4>\n'
                if p.link
                else f"            <h4>{esc(p.title)}</h4>\n"
            )
            + f'            <span class="status {"published" if p.status == "Published" else "pending"}">{esc(p.status)}</span>\n'
            + "          </div>\n"
            + f'          <p class="authors">{esc(p.authors)}</p>\n'
            + '          <div class="pub-bottom">\n'
            + f'            <span class="venue">{esc(p.venue)}</span>\n'
            + f'            <span class="period">{esc(p.date)}</span>\n'
            + "          </div>\n"
            + "        </div>"
            for p in web.publications
        )
        research_items = "".join(
            '        <div class="card">\n'
            '          <div class="card-header">\n'
            f"            <h4>{esc(r.title)}</h4>\n"
            f'            <span class="period">{esc(r.year)}</span>\n'
            "          </div>\n"
            f"          <p>{esc(r.body)}</p>\n"
            f"          {_tags(r.tags)}\n"
            + (
                '          <div class="links">'
                + "".join(
                    f'<a href="{esc(str(link.url))}" class="link-btn" target="_blank" rel="noopener">{esc(link.label)}</a>'
                    for link in r.links
                )
                + "</div>\n"
                if r.links
                else ""
            )
            + "        </div>"
            for r in web.research
        )
        sections_html += (
            '\n<section id="research">\n  <div class="container">\n'
            '    <h2 class="section-title">Research & Publications</h2>\n'
            '    <div class="research-grid">\n'
            "      <div>\n"
            '        <h3 style="color:var(--text-muted);font-size:0.85rem;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:20px;">Publications</h3>\n'
            f"        {pub_items}\n"
            "      </div>\n"
            "      <div>\n"
            '        <h3 style="color:var(--text-muted);font-size:0.85rem;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:20px;">Research Projects</h3>\n'
            f"        {research_items}\n"
            "      </div>\n"
            "    </div>\n"
            "  </div>\n</section>"
        )

    if web.projects:
        items = "".join(
            '        <div class="card project-card">\n'
            '          <div class="card-header">\n'
            f"            <h4>{esc(p.title)}</h4>\n"
            f'            <span class="period">{esc(p.year)}</span>\n'
            "          </div>\n"
            f"          <p>{esc(p.body)}</p>\n"
            f"          {_tags(p.tags)}\n"
            + (
                f'          <a href="{esc(str(p.link))}" class="link-btn" target="_blank" rel="noopener">View →</a>\n'
                if p.link
                else ""
            )
            + "        </div>"
            for p in web.projects
        )
        sections_html += (
            '\n<section id="projects">\n  <div class="container">\n'
            '    <h2 class="section-title">Personal Projects</h2>\n'
            f'    <div class="projects-grid">{items}</div>\n'
            "  </div>\n</section>"
        )

    if web.skills:
        groups = "".join(
            '        <div class="skill-group">\n'
            f"          <h3>{esc(s.category)}</h3>\n"
            '          <div class="skills">'
            + "".join(f'<span class="skill">{esc(skill)}</span>' for skill in s.skills)
            + "</div>\n"
            "        </div>"
            for s in web.skills
        )
        sections_html += (
            '\n<section id="skills">\n  <div class="container">\n'
            '    <h2 class="section-title">Technical Skills</h2>\n'
            f'    <div class="skills-grid">{groups}</div>\n'
            "  </div>\n</section>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} | {esc(personal.title)}</title>
  <meta name="description" content="{esc(personal.tagline)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>{_CSS}
  </style>
</head>
<body>

<nav>
  <div class="container">
    <a href="#hero" class="logo">{name}</a>
    <div class="links">{nav_links}</div>
  </div>
</nav>

<section id="hero">
  <div class="container">
    <h1>{name}</h1>
    <p class="subtitle">{esc(personal.title)}<br>{esc(personal.tagline)}</p>
    <div class="cta">
      {cta}
    </div>
  </div>
</section>
{sections_html}

<footer>
  <div class="container">
    <p>© {name} · Built from <a href="https://github.com/wd7512/homepage/blob/main/content/">Markdown content</a></p>
  </div>
</footer>

</body>
</html>
"""
