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
    assert p.kind == "personal" and p.links == []


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


def test_profile_fields_and_channel_order() -> None:
    p = Personal(
        **personal_kwargs(
            orcid="https://orcid.org/0009-0005-4769-3136",
            scholar="https://scholar.google.com/citations?hl=en&user=MKqzBNYAAAAJ",
            research_statement="Statement.",
            research_interests="Interests.",
        )
    )
    assert str(p.orcid).endswith("0009-0005-4769-3136")
    assert p.research_statement == "Statement."
    assert p.research_interests == "Interests."

    r1 = ResearchProject(title="Web first", year="2026", body="B", order=1, cv_order=2)
    r2 = ResearchProject(title="CV first", year="2026", body="B", order=2, cv_order=1)
    p1 = PersonalProject(title="Web first", year="2026", body="B", order=1, cv_order=2)
    p2 = PersonalProject(title="CV first", year="2026", body="B", order=2, cv_order=1)
    bundle = DomainBundle(research=[r1, r2], projects=[p1, p2])

    assert [x.title for x in bundle.visible("website").research] == ["Web first", "CV first"]
    assert [x.title for x in bundle.visible("cv").research] == ["CV first", "Web first"]
    assert [x.title for x in bundle.visible("website").projects] == ["Web first", "CV first"]
    assert [x.title for x in bundle.visible("cv").projects] == ["CV first", "Web first"]


def test_publication_highlight_author() -> None:
    pub = Publication(
        title="T",
        authors="A, William Dennis, B",
        venue="V",
        date="2025",
        status="Published",
        order=1,
        highlight_author="William Dennis",
    )
    assert pub.highlight_author == "William Dennis"
