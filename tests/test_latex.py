"""LaTeX adapter tests: escaping, bullets, channel filtering, no phones."""

import re

from adapters.outbound.latex import escape_latex, md_bullets_to_latex, render_cv
from domain.models import (
    Activity,
    DomainBundle,
    Experience,
    Personal,
    PersonalProject,
    SkillCategory,
)

# Phone-shaped text must never appear in rendered output. (Deliberately
# pattern-based: the real number must not be hardcoded anywhere in tests.)
PHONE_SHAPE_RE = re.compile(r"\+44|\(0\)\s?\d|07\d{3}\s?\d{3}")


def personal() -> Personal:
    return Personal(
        name="William Dennis",
        title="Machine Learning Researcher",
        tagline="Robust ML.",
        email="wwdennis.research@gmail.com",
        linkedin="https://uk.linkedin.com/in/williamwudennis",
        github="https://github.com/wd7512",
        website="https://wd7512.github.io/home/",
    )


def test_escape_latex_specials() -> None:
    assert escape_latex("a&b%c$d#e_f{g}h~i^j\\k") == (
        r"a\&b\%c\$d\#e\_f\{g\}h\textasciitilde{}i\textasciircumflex{}j"
        r"\textbackslash{}k"
    )


def test_bullets_empty_and_escaped() -> None:
    assert md_bullets_to_latex([]) == ""
    tex = md_bullets_to_latex(["50% faster & robust", "Error <3bpm"])
    assert tex.startswith("\\begin{itemize}")
    assert r"\item 50\% faster \& robust" in tex
    assert r"\item Error \textless{}3bpm" in tex
    assert tex.endswith("\\end{itemize}")


def test_render_cv_filters_channels_and_has_no_phone() -> None:
    bundle = DomainBundle(
        personal=personal(),
        experience=[
            Experience(
                role="Energy Modeller",
                company="Aurora",
                location="Oxford, UK",
                period="Oct 2024 – Jun 2026",
                bullets=["Forecasted 100% of demand."],
                slug="aurora",
                order=1,
            )
        ],
        projects=[
            PersonalProject(
                title="Steam Market Trading",
                year="2020-2023",
                body="Trading.",
                order=1,
                visibility=["website"],
            )
        ],
        skills=[SkillCategory(category="Languages", skills=["Python", "C#"], order=1)],
        activities=[Activity(title="Talk", venue="Conf", date="Feb 2025", order=1)],
    )
    tex = render_cv(bundle)
    assert "William Dennis" in tex
    assert "wwdennis.research@gmail.com" in tex
    assert "Aurora" in tex
    assert r"100\% of demand" in tex
    assert "Steam Market" not in tex  # website-only
    assert "Talk" in tex  # cv-visible activity
    assert "C\\#" in tex
    assert PHONE_SHAPE_RE.search(tex) is None
    assert "phone" not in tex.lower()
