"""Hexagonal core: public-profile domain entities (Pydantic v2, strict).

Single source of truth for every outbound adapter (website, LaTeX/PDF).
No I/O here — the inbound Markdown loader and outbound renderers live in
src/adapters/ and depend inward on these models.

Conventions (see docs/PLAN.md):
  - `extra="forbid"`: unknown frontmatter fields fail fast.
  - Every entity carries `visibility: [website, cv]` (Activities default cv-only).
  - Research vs personal projects are explicit via `kind`, never inferred.
  - No phone field anywhere: phones are never public (allowlist is empty).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

Visibility = Literal["website", "cv"]
VisibilityList = Annotated[list[Visibility], Field(min_length=1)]

# EmailStr would pull in the email-validator package; a constrained string
# keeps the core dependency-free beyond pydantic itself.
ContactEmail = Annotated[str, Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]
NonEmpty = Annotated[str, Field(min_length=1)]


class StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class VisibilityMixin(StrictBase):
    visibility: VisibilityList = ["website", "cv"]


class OrderedMixin(VisibilityMixin):
    """Display position within its section (1 = first). Required and explicit."""

    order: Annotated[int, Field(ge=1)]


class Personal(VisibilityMixin):
    name: NonEmpty
    title: NonEmpty
    tagline: NonEmpty
    email: ContactEmail
    linkedin: HttpUrl
    github: HttpUrl
    website: HttpUrl | None = None
    # Relative path (repo-root) of the built CV PDF, e.g. "cv.pdf".
    # Rendered by the future website adapter as a download link.
    cv_pdf: NonEmpty | None = None
    # Optional researcher-profile links rendered in the site/CV header.
    orcid: HttpUrl | None = None
    scholar: HttpUrl | None = None
    # Public-facing research narrative. `research_statement` is rendered on
    # the website; `research_interests` is a compact CV line.
    research_statement: NonEmpty | None = None
    research_interests: NonEmpty | None = None


class Experience(OrderedMixin):
    role: NonEmpty
    company: NonEmpty
    location: NonEmpty
    period: NonEmpty
    bullets: Annotated[list[NonEmpty], Field(min_length=1)]
    slug: NonEmpty


class Education(OrderedMixin):
    institution: NonEmpty
    degree: NonEmpty
    details: str | None = None
    period: NonEmpty
    bullets: Annotated[list[NonEmpty], Field(min_length=1)]


class LinkItem(StrictBase):
    label: NonEmpty
    url: HttpUrl


class ResearchProject(OrderedMixin):
    title: NonEmpty
    tags: list[NonEmpty] = []
    year: NonEmpty
    # May be empty (e.g. manuscript prepared but not yet public).
    links: list[LinkItem] = []
    body: NonEmpty
    kind: Literal["research"] = "research"
    # Optional curated ordering for the CV. Falls back to `order`.
    cv_order: Annotated[int, Field(ge=1)] | None = None


class PersonalProject(OrderedMixin):
    title: NonEmpty
    tags: list[NonEmpty] = []
    year: NonEmpty
    links: list[LinkItem] = []
    body: NonEmpty
    kind: Literal["personal"] = "personal"
    # Optional curated ordering for the CV. Falls back to `order`.
    cv_order: Annotated[int, Field(ge=1)] | None = None


class Publication(OrderedMixin):
    title: NonEmpty
    authors: NonEmpty
    venue: NonEmpty
    date: NonEmpty
    status: Literal["Published", "Pending", "Submitted"]
    link: HttpUrl | None = None
    # Name to emphasise in the author list (usually the profile owner).
    highlight_author: NonEmpty | None = None


class SkillCategory(OrderedMixin):
    category: NonEmpty
    skills: Annotated[list[NonEmpty], Field(min_length=1)]


class Activity(StrictBase):
    order: Annotated[int, Field(ge=1)]
    title: NonEmpty
    venue: str | None = None
    date: NonEmpty
    details: str | None = None
    visibility: VisibilityList = ["cv"]


class DomainBundle(StrictBase):
    """Everything the outbound adapters need for one build."""

    personal: Personal | None = None
    experience: list[Experience] = []
    education: list[Education] = []
    research: list[ResearchProject] = []
    projects: list[PersonalProject] = []
    publications: list[Publication] = []
    skills: list[SkillCategory] = []
    activities: list[Activity] = []

    def visible(self, channel: Visibility) -> DomainBundle:
        """Return a sorted copy containing only entries visible on `channel`.

        Website entries use `order`; CV entries use `cv_order` when present,
        falling back to `order`. This lets the public portfolio and the
        curated CV present the same files in different sequences.
        """

        def key(item: object) -> int:
            if channel == "cv":
                cv_order = getattr(item, "cv_order", None)
                if cv_order is not None:
                    return cv_order
            return item.order  # type: ignore[attr-defined]

        def select(items: list) -> list:
            return sorted((i for i in items if channel in i.visibility), key=key)

        return DomainBundle(
            personal=self.personal,
            experience=select(self.experience),
            education=select(self.education),
            research=select(self.research),
            projects=select(self.projects),
            publications=select(self.publications),
            skills=select(self.skills),
            activities=select(self.activities),
        )
