"""Loader tests: Markdown frontmatter -> domain, fail-fast behaviour."""

from pathlib import Path

import pytest

from adapters.inbound.markdown_loader import ContentError, bullets, load, parse_md


def write(path: Path, text: str) -> Path:
    path.write_text(text)
    return path


@pytest.fixture
def content(tmp_path: Path) -> Path:
    root = tmp_path / "content"
    (root / "experience").mkdir(parents=True)
    (root / "research").mkdir()
    write(
        root / "personal.md",
        "---\nname: William Dennis\ntitle: ML Researcher\ntagline: Robust ML.\n"
        "email: wwdennis.research@gmail.com\n"
        "linkedin: https://uk.linkedin.com/in/williamwudennis\n"
        "github: https://github.com/wd7512\n---\n",
    )
    write(
        root / "experience" / "aurora.md",
        "---\nrole: Energy Modeller\ncompany: Aurora\nlocation: Oxford, UK\n"
        "period: Oct 2024 – Jun 2026\norder: 2\n---\n\n- Forecasted demand.\n- Built tools.\n",
    )
    write(
        root / "experience" / "earlier.md",
        "---\nrole: Intern\ncompany: OldCo\nlocation: London, UK\n"
        "period: Jul 2021 – Jul 2022\norder: 1\n---\n\n- Did things.\n",
    )
    write(
        root / "research" / "robust-ml.md",
        "---\ntitle: Robust ML\ntags: [PyTorch]\nyear: '2025'\nkind: research\norder: 1\n"
        "links:\n  - label: Code\n    url: https://github.com/wd7512/x\n---\n\nBody.\n",
    )
    return root


def test_load_sorts_sections_by_order(content: Path) -> None:
    bundle = load(content)
    assert [e.slug for e in bundle.experience] == ["earlier", "aurora"]


def test_load_valid_tree(content: Path) -> None:
    bundle = load(content)
    assert bundle.personal is not None and bundle.personal.name == "William Dennis"
    assert len(bundle.experience) == 2
    assert bundle.experience[1].slug == "aurora"
    assert bundle.experience[1].bullets == ["Forecasted demand.", "Built tools."]
    assert bundle.research[0].kind == "research"
    assert bundle.visible("cv").experience[1].role == "Energy Modeller"


def test_missing_frontmatter_fails(tmp_path: Path) -> None:
    f = write(tmp_path / "x.md", "Just body, no frontmatter.")
    with pytest.raises(ContentError, match="frontmatter"):
        parse_md(f)


def test_invalid_yaml_fails(tmp_path: Path) -> None:
    f = write(tmp_path / "x.md", "---\ntitle: [unclosed\n---\n\nBody.")
    with pytest.raises(ContentError, match="YAML"):
        parse_md(f)


def test_unknown_field_fails(content: Path) -> None:
    write(
        content / "experience" / "bad.md",
        "---\nrole: R\ncompany: C\nlocation: L\nperiod: P\nnickname: Will\n---\n\n- B.\n",
    )
    with pytest.raises(ContentError, match="bad.md"):
        load(content)


def test_bad_visibility_and_empty_bullets_fail(content: Path) -> None:
    write(
        content / "experience" / "bad.md",
        "---\nrole: R\ncompany: C\nlocation: L\nperiod: P\nvisibility: [newsletter]\n---\n\n- B.\n",
    )
    with pytest.raises(ContentError):
        load(content)
    (content / "experience" / "bad.md").write_text(
        "---\nrole: R\ncompany: C\nlocation: L\nperiod: P\n---\n\nNo bullets here.\n"
    )
    with pytest.raises(ContentError):
        load(content)


def test_kind_must_match_directory(content: Path) -> None:
    write(
        content / "research" / "wrong.md",
        "---\ntitle: T\ntags: []\nyear: '2025'\nkind: personal\nlink: https://github.com/wd7512\n"
        "---\n\nBody.\n",
    )
    with pytest.raises(ContentError, match="must have kind"):
        load(content)


def test_bullets_helper_ignores_non_bullet_lines() -> None:
    assert bullets("Intro line.\n- One.\n  - nested\n- Two.\n") == ["One.", "Two."]


def test_unquoted_yaml_year_loads_as_string(content: Path) -> None:
    write(
        content / "research" / "dated.md",
        "---\ntitle: T\ntags: []\nyear: 2025\nkind: research\nlinks: []\norder: 9\n---\n\nBody.\n",
    )
    bundle = load(content)
    years = {r.title: r.year for r in bundle.research}
    assert years["T"] == "2025"
