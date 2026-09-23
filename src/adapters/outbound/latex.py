"""Outbound adapter: domain bundle -> LaTeX CV (stdlib rendering).

Renders the ``cv`` channel of a :class:`DomainBundle` to a self-contained
``.tex`` document. Plain-Python string composition (no Jinja dependency);
Markdown bodies are treated as plain text with bullet lists — the only
Markdown the content model supports. Never emits phone numbers: the domain
has no phone field.
"""

from __future__ import annotations

import re

from domain.models import DomainBundle

_REPLACEMENTS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciircumflex{}",
    "<": r"\textless{}",
    ">": r"\textgreater{}",
}
_ESCAPE_RE = re.compile(r"([\\&%$#_{}~^<>])")


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters in running text (not URLs).

    Single regex pass so replacement text (which itself contains braces)
    is never re-escaped.
    """
    return _ESCAPE_RE.sub(lambda m: _REPLACEMENTS[m.group(1)], text)


def md_bullets_to_latex(bullets: list[str]) -> str:
    """Render bullet strings as an itemize environment ("" when empty)."""
    if not bullets:
        return ""
    items = "\n".join(f"  \\item {escape_latex(b)}" for b in bullets)
    return f"\\begin{{itemize}}\n{items}\n\\end{{itemize}}"


def _entry(head: str, right: str, sub: str, body_tex: str) -> str:
    parts = [f"\\entry{{{head}}}{{{right}}}"]
    if sub:
        parts.append(f"{{\\textit{{{sub}}}}}")
    if body_tex:
        parts.append(body_tex)
    return "\n".join(parts)


def render_cv(bundle: DomainBundle) -> str:
    """Render the cv-visible slice of the bundle to a .tex document."""
    cv = bundle.visible("cv")
    personal = cv.personal
    if personal is None:
        raise ValueError("content/personal.md is required to render the CV")

    header_links = [
        f"\\href{{mailto:{personal.email}}}{{{escape_latex(str(personal.email))}}}",
        f"\\href{{{personal.linkedin}}}{{LinkedIn}}",
        f"\\href{{{personal.github}}}{{GitHub}}",
    ]
    if personal.website:
        header_links.append(f"\\href{{{personal.website}}}{{Website}}")
    header = r" \textbar ".join(header_links)

    sections: list[str] = []
    if cv.experience:
        items = "\n\n".join(
            _entry(
                f"{escape_latex(e.role)} --- {escape_latex(e.company)}",
                escape_latex(e.period),
                escape_latex(e.location),
                md_bullets_to_latex(e.bullets),
            )
            for e in cv.experience
        )
        sections.append(f"\\section*{{Experience}}\n\n{items}")
    if cv.education:
        items = "\n\n".join(
            _entry(
                f"{escape_latex(e.institution)} --- {escape_latex(e.degree)}",
                escape_latex(e.period),
                escape_latex(e.details or ""),
                md_bullets_to_latex(e.bullets),
            )
            for e in cv.education
        )
        sections.append(f"\\section*{{Education}}\n\n{items}")
    if cv.research:
        blocks = []
        for r in cv.research:
            links = r" \textbar ".join(
                f"\\href{{{link.url}}}{{{escape_latex(link.label)}}}" for link in r.links
            )
            body = escape_latex(r.body)
            if links:
                body += f"\n\n{links}"
            blocks.append(_entry(escape_latex(r.title), escape_latex(r.year), "", body))
        sections.append("\\section*{Research}\n\n" + "\n\n".join(blocks))
    if cv.publications:
        items = "\n".join(
            f"  \\item {escape_latex(p.authors)}. "
            f"\\textit{{{escape_latex(p.title)}.}} "
            f"{escape_latex(p.venue)}, {escape_latex(p.date)}. "
            f"{escape_latex(p.status)}." + (f"~\\url{{{p.link}}}" if p.link else "")
            for p in cv.publications
        )
        sections.append(
            f"\\section*{{Publications}}\n\n\\begin{{enumerate}}\n{items}\n\\end{{enumerate}}"
        )
    if cv.skills:
        items = "\n".join(
            f"  \\item \\textbf{{{escape_latex(s.category)}:}} "
            + ", ".join(escape_latex(skill) for skill in s.skills)
            for s in cv.skills
        )
        sections.append(
            f"\\section*{{Technical Skills}}\n\n\\begin{{itemize}}\n{items}\n\\end{{itemize}}"
        )
    if cv.activities:
        items = "\n".join(
            f"  \\item {escape_latex(a.title)}"
            + (f" --- {escape_latex(a.venue)}" if a.venue else "")
            + f", {escape_latex(a.date)}."
            for a in cv.activities
        )
        sections.append(
            f"\\section*{{Activities}}\n\n\\begin{{itemize}}\n{items}\n\\end{{itemize}}"
        )

    body = "\n\n".join(sections)
    # PDF metadata carries only the public name/title (no paths, no emails).
    meta = (
        f"\\hypersetup{{colorlinks=true, linkcolor=linkblue, urlcolor=linkblue,\n"
        f"  pdftitle={{{escape_latex(personal.name)} --- {escape_latex(personal.title)}}},\n"
        f"  pdfauthor={{{escape_latex(personal.name)}}}}}"
    )
    return f"""\\documentclass[10pt,a4paper]{{article}}

\\usepackage[margin=0.75in]{{geometry}}
\\usepackage{{enumitem}}
\\usepackage{{titlesec}}
\\usepackage{{xcolor}}
\\usepackage{{textcomp}}
\\usepackage{{hyperref}}
\\usepackage{{microtype}}

\\definecolor{{linkblue}}{{HTML}}{{0645AD}}
{meta}

\\titleformat{{\\section}}{{\\large\\bfseries}}{{}} {{0em}} {{}}[\\titlerule]
\\titlespacing*{{\\section}}{{0pt}}{{8pt}}{{4pt}}

\\setlength{{\\parindent}}{{0pt}}
\\setlength{{\\parskip}}{{2pt}}
\\setlist[itemize]{{leftmargin=1.2em, itemsep=1pt, topsep=2pt}}
\\setlist[enumerate]{{leftmargin=1.4em, itemsep=2pt, topsep=2pt}}

\\newcommand{{\\entry}}[3]{{%
  \\textbf{{#1}}\\hfill #2\\par
  \\ifx&#3&\\else\\textit{{#3}}\\par\\fi
}}

\\pagestyle{{empty}}

% Generated from content/ by the homepage LaTeX adapter. Do not hand-edit.
% PDF metadata: set pdftitle/pdfauthor at compile time (see build_cv.py).

\\begin{{document}}

\\begin{{center}}
{{\\LARGE \\textbf{{{escape_latex(personal.name)}}}}}\\\\[2pt]
{escape_latex(personal.title)}\\\\[2pt]
{header}
\\end{{center}}

\\vspace{{1pt}}

{body}

\\end{{document}}
"""
