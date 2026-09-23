"""HTML adapter tests: channel filtering, CV link, escaping, no phones."""

import re

from adapters.outbound.html import render_site
from domain.models import (
    Activity,
    DomainBundle,
    Experience,
    Personal,
    PersonalProject,
)

# Phone-shaped text must never appear in rendered output. (Deliberately
# pattern-based: the real number must not be hardcoded anywhere in tests.)
PHONE_SHAPE_RE = re.compile(r"\+44|\(0\)\s?\d|07\d{3}\s?\d{3}")


def personal(**over) -> Personal:
    base = {
        "name": "William Dennis",
        "title": "Incoming PhD Researcher",
        "tagline": "Robust ML.",
        "email": "wwdennis.research@gmail.com",
        "linkedin": "https://uk.linkedin.com/in/williamwudennis",
        "github": "https://github.com/wd7512",
        "cv_pdf": "cv.pdf",
    }
    base.update(over)
    return Personal(**base)


def test_render_site_channels_and_cv_link() -> None:
    bundle = DomainBundle(
        personal=personal(),
        experience=[
            Experience(
                role="Energy Modeller",
                company="Aurora",
                location="Oxford, UK",
                period="Oct 2024 – Jun 2026",
                bullets=["Forecasted <demand>."],
                slug="aurora",
                order=1,
            )
        ],
        projects=[
            PersonalProject(
                title="Hobby",
                year="2021",
                body="Fun.",
                order=1,
                visibility=["website"],
            )
        ],
        activities=[Activity(title="Talk", date="Feb 2025", order=1)],
    )
    page = render_site(bundle)
    assert "William Dennis" in page
    assert "Incoming PhD Researcher" in page
    assert 'href="cv.pdf"' in page
    assert "Download CV (PDF)" in page
    assert "Aurora" in page
    assert "Forecasted &lt;demand&gt;." in page
    assert "Hobby" in page  # website-visible
    assert "Talk" not in page  # cv-only activity
    assert PHONE_SHAPE_RE.search(page) is None
    assert "phone" not in page.lower()


def test_render_site_without_cv_pdf_omits_link() -> None:
    bundle = DomainBundle(personal=personal(cv_pdf=None))
    assert "Download CV" not in render_site(bundle)
