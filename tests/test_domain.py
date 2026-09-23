"""Domain core tests: schema strictness, defaults, channel filtering."""

import pytest
from pydantic import ValidationError

from domain.models import (
    Activity,
    DomainBundle,
    Education,
    Experience,
    Personal,
    PersonalProject,
    Publication,
    ResearchProject,
    SkillCategory,
)


def personal_kwargs(**over) -> dict:
    base = {
        "name": "William Dennis",
        "title": "Machine Learning Researcher",
        "tagline": "Robust ML.",
        "email": "wwdennis.research@gmail.com",
        "linkedin": "https://uk.linkedin.com/in/williamwudennis",
        "github": "https://github.com/wd7512",
    }
    base.update(over)
    return base


def test_personal_valid_and_no_phone_field() -> None:
    p = Personal(**personal_kwargs())
    assert p.visibility == ["website", "cv"]
    assert p.website is None
    with pytest.raises(ValidationError):
        Personal(**personal_kwargs(nickname="Will"))  # type: ignore[call-arg]


def test_personal_rejects_bad_email_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Personal(**personal_kwargs(email="not-an-email"))
    with pytest.raises(ValidationError):
        Personal(**personal_kwargs(nickname="Will"))  # type: ignore[call-arg]


def test_visibility_defaults_and_validation() -> None:
    exp = Experience(
        role="Energy Modeller",
        company="Aurora",
        location="Oxford, UK",
        period="Oct 2024 – Jun 2026",
        bullets=["Forecasted demand."],
        slug="aurora",
        order=1,
    )
    assert exp.visibility == ["website", "cv"]
    assert Activity(title="Talk", date="Feb 2025", order=1).visibility == ["cv"]
    with pytest.raises(ValidationError):
        Experience(
            role="R",
            company="C",
            location="L",
            period="P",
            bullets=["B"],
            slug="s",
            order=0,  # must be >= 1
        )
    with pytest.raises(ValidationError):
        Experience(
            role="R",
            company="C",
            location="L",
            period="P",
            bullets=["B"],
            slug="s",
            # missing order
        )
    with pytest.raises(ValidationError):
        Experience(
            role="R",
            company="C",
            location="L",
            period="P",
            bullets=["B"],
            slug="s",
            order=1,
            visibility=["newsletter"],  # type: ignore[list-item]
        )


def test_kind_is_explicit_and_enforced() -> None:
    r = ResearchProject(
        title="Robust ML",
        year="2025",
        links=[{"label": "Code", "url": "https://github.com/wd7512/x"}],
        body="Framework.",
        order=1,
    )
    assert r.kind == "research"
    with pytest.raises(ValidationError):
        ResearchProject(
            title="T",
            year="2025",
            links=[{"label": "C", "url": "https://github.com/wd7512/x"}],
            body="B",
            order=1,
            kind="personal",  # type: ignore[arg-type]
        )
    p = PersonalProject(title="Snake AI", year="2021", body="Evolved nets.", order=1)
    assert p.kind == "personal" and p.link is None


def test_bullets_and_skills_must_be_non_empty() -> None:
    with pytest.raises(ValidationError):
        Experience(
            role="R",
            company="C",
            location="L",
            period="P",
            bullets=[],
            slug="s",
            order=1,
        )
    with pytest.raises(ValidationError):
        SkillCategory(category="Languages", skills=[], order=1)
    with pytest.raises(ValidationError):
        Publication(title="T", authors="A", venue="V", date="D", status="Draft", order=1)  # type: ignore[arg-type]


def test_bundle_visible_filters_by_channel() -> None:
    bundle = DomainBundle(
        experience=[
            Experience(
                role="A",
                company="C",
                location="L",
                period="P",
                bullets=["B"],
                slug="a",
                order=1,
                visibility=["website", "cv"],
            ),
            Experience(
                role="Hobby",
                company="C",
                location="L",
                period="P",
                bullets=["B"],
                slug="h",
                order=2,
                visibility=["website"],
            ),
        ],
        education=[
            Education(
                institution="U",
                degree="D",
                period="P",
                bullets=["B"],
                order=1,
                visibility=["cv"],
            )
        ],
    )
    cv = bundle.visible("cv")
    assert [e.slug for e in cv.experience] == ["a"]
    assert len(cv.education) == 1
    web = bundle.visible("website")
    assert [e.slug for e in web.experience] == ["a", "h"]
    assert web.education == []
