# Homepage — current plan

Single-source personal site and CV. Content lives in Markdown + YAML
frontmatter; the domain model validates it; adapters render the website and
LaTeX CV.

## Layout

```
content/
  personal.md
  experience/*.md
  education/*.md
  research/*.md
  projects/*.md
  publications/*.md
  skills/*.md
  activities/*.md
src/
  domain/models.py                 # Pydantic v2 entities
  adapters/inbound/markdown_loader.py
  adapters/outbound/html.py
  adapters/outbound/latex.py
scripts/
  build_site.py
  build_cv.py
  validate.py
  check_contacts.py
tests/
```

## Content model

- `research/` entries must use `kind: research`.
- `projects/` entries must use `kind: personal`.
- Every entry has `visibility: [website, cv]` (default) or a subset.
- `activities/` default to `visibility: [cv]`.
- `links:` is a list of `{label, url}` on research and personal projects.
- `order` controls website order.
- `cv_order` is optional and controls curated CV order; it falls back to
  `order` when absent.
- `publications[].highlight_author` bolds the profile owner's name in the
  rendered author list.
- `personal.research_statement` renders at the top of the website Research
  section.
- `personal.research_interests` renders as a short CV line.
- Unknown fields fail validation (`extra="forbid"`).

## Current content split

- **Website research:** AI harness evaluation, SLM bias testing, JITAI,
  multi-agent RL for energy markets, robust ML, PPG signal quality.
- **CV research:** robust ML, JITAI, SLM bias testing, PPG signal quality.
- **Website personal projects:** OpenFrontBench, Moonboard-Analysis,
  Chess AI, RL Trader, Evolutionary Snake AI, Steam Market Trading.
- **CV selected technical projects:** Moonboard-Analysis, OpenFrontBench,
  RL Trader.
- **Publications:** LNAI 2026, ICAART 2025, SmartSocks 2025.
- **Activities:** CV-only.

## Build and verify

```bash
uv sync --group dev
uv run pytest -q
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run python scripts/validate.py --content content
python3 scripts/check_contacts.py --mode tree
uv run python scripts/build_site.py --content content --out dist/index.html
uv run python scripts/build_cv.py --content content --out dist/cv.tex --pdf
```

`dist/` is gitignored and rebuilt by CI. `cv.pdf` at the repo root is the
tracked CV download target.

## Deploy

Pushing to `main` runs `.github/workflows/deploy.yml`, which rebuilds the
site and CV, scans outputs for leaked contact data, and deploys `dist/` to
GitHub Pages. `.github/workflows/ci.yml` runs lint, tests, validation, the
working-tree contact gate, and a CV build on every push/PR.

## Privacy

- No phone field exists in the domain.
- `contacts.allowlist.yaml` is the single source of truth for public
  emails, profile URLs, and phone numbers.
- The history gate is run locally before any public-history rewrite; CI
  runs the working-tree gate.
