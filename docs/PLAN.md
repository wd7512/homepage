# Homepage — build-ready plan

> Private working document. Goal: retire `home` (`wd7512/home`, current live
> site) and replace it with `homepage` (`wd7512/homepage`, currently private).
> Develop fully in private, then release a public version as a **single clean
> commit**. Afterwards make `home` private + archived.
>
> PII hygiene for this file: it uses placeholders (`<old-home-email>`,
> `<uni-author-email>`) instead of literal non-public addresses. Full values
> are visible in private git history only. `contacts.allowlist.yaml` is the
> only place that lists literal public-safe contacts.

## 1. Decisions locked (from review)

| # | Decision | Value |
|---|----------|-------|
| 1 | Surviving repo | `homepage`; `home` retires to private + archived |
| 2 | History scrub timing | Deferred to later roadmap step (pre-public), not this slice |
| 3 | First slice | Unify data model (hexagonal core), not website styling |
| 4 | Source of truth | Keep Markdown + YAML frontmatter (`content/**/*.md`) |
| 5 | Divergence | Shared core + `visibility: [website, cv]` flags (strict 1:1 rejected) |
| 6 | Migration order | Define Pydantic schema first, then port content |
| 7 | Schema tech | Pydantic v2 |
| 8 | Schema scope | Mirror `home/types.ts` + `Activities` entity + explicit research/personal split |
| 9 | Hex layout | `src/domain + adapters` (full separation, §3) |
| 10 | Research vs personal | Explicit `kind: research \| personal` (replaces `links`-presence inference) |
| 11 | Loader strictness | Fail fast (`extra=forbid`, unknown/bad values break build) |
| 12 | LaTeX adapter | Markdown-to-TeX helper + minimal template (no hand-edited `.tex` drift) |
| 13 | HTML adapter | Deferred (keep `home` live until homepage proves replacement) |
| 14 | Schema proof | Both unit tests + validator dry-run over ported content |
| 15 | After schema | LaTeX helper + local PDF (still private) |
| 16 | Contacts | `contacts.allowlist.yaml` whitelist + `scripts/check_contacts.py` gate (§5) |
| 17 | Public release | Private dev → single squashed public commit (orphan branch or new repo) |

## 2. Current state (private, read-only findings)

* `homepage/main` (3 commits): `b2d6906` adds `example_cv.tex` (161 lines),
  `3913fcb` fixes contact email, `8066571` adds `William_Dennis_CV_4_0.pdf`
  binary. No build system, no CI, no `.gitignore`.
* Contamination (expected, scrub deferred): `b2d6906` patch contains
  `<old-home-email>`; all 3 commits carry `<uni-author-email>` as
  author/committer; a non-allowlisted phone number + research email appear in
  every revision. `scripts/check_contacts.py --mode history` currently **fails**
  — that is the correct pre-scrub signal (phone is intentionally not
  allowlisted and must be removed from content before public release).
* `home` reference implementation: `content/*.md` + `build.py` (476 lines,
  HTML string-concat) → `dist/index.html` → `gh-pages` via
  `.github/workflows/deploy.yml`. `types.ts` defines the domain
  (`Experience/Education/Project/Publication/SkillCategory`) but is unused by
  Python. `tests/test_build.py` covers frontmatter parsing + section presence.
  `content/config.yaml` disables `personal_projects`.
* Site-vs-CV drift (validator must surface all of these): header contacts
  (email fixed in HEAD, LinkedIn slug differs between `home/content` and CV);
  experience count 4 vs 6 (CV adds NUS internship + part-time researcher;
  Aurora end date `Present` vs bounded; Milbotix dates differ; JPM 4 bullets
  vs 1); education 2 vs 3 (CV adds incoming PhD, MSc 3 vs 5 bullets);
  research/projects/publications structural split + status conflicts (LNAI
  Published vs pending, signal-quality not-submitted vs submitted, 2 vs 3
  publications, `rl-health-interventions`/JITAI absent from site);
  skills framing differs; CV-only Activities (4 talks); site-only hobby
  projects (chess/snake/pi-temp/ai-trader/steam-market) needing
  `visibility: [website]` or removal for a professional CV.

## 3. Hexagonal architecture

```
homepage/
  contacts.allowlist.yaml
  content/
    personal.md
    experience/*.md
    education/*.md
    research/*.md        # NEW: split out of projects/
    projects/*.md
    publications/*.md
    skills/*.md
    activities/*.md      # NEW: conferences/talks (default visibility [cv])
  src/
    domain/models.py     # Pydantic v2 entities (§4)
    ports/__init__.py    # load/render port protocols
    adapters/inbound/markdown_loader.py   # parse_md + validate, fail-fast
    adapters/outbound/latex.py            # md→TeX helper + cv.tex.j2
    adapters/outbound/html.py             # STUB this slice (deferred)
  scripts/
    check_contacts.py    # allowlist gate (this commit)
    validate.py          # LATER: dry-run loader over content/
  tests/
    test_domain.py       # LATER
    test_loader.py       # LATER
  docs/PLAN.md           # this file
```

* Core (`src/domain`) depends on nothing. Adapters depend inward.
* Inbound adapter reads Markdown; outbound adapters render HTML / LaTeX.
  No file-format logic inside domain models.

## 4. Domain schema (Pydantic v2, strict)

Common: every entity gets `visibility: list[Literal["website","cv"]]`
(default `["website","cv"]`; `activities` default `["cv"]`). Loader sets
`extra="forbid"`.

* `Personal`: `name, title, tagline, email: EmailStr, linkedin: HttpUrl, github: HttpUrl, website?: HttpUrl` (no phone field — phone is never public)
* `Experience`: `role, company, location, period, bullets: list[str] (min_length=1), visibility, slug`
* `Education`: `institution, degree, details?, period, bullets, visibility`
* `ResearchProject`: `title, tags: list[str], year: str, links: list[{label,url}], body: str, kind: Literal["research"] = "research", visibility`
* `PersonalProject`: `title, tags, year, link?: HttpUrl, body, kind: Literal["personal"] = "personal", visibility`
* `Publication`: `title, authors, venue, date, status: Literal["Published","Pending","Submitted"], link?: HttpUrl, visibility`
* `SkillCategory`: `category, skills: list[str] (min 1), visibility`
* `Activity`: `title, venue?, date: str, details?: str, visibility = ["cv"]`

Validation rules: unknown fields fail; bad `visibility`/`kind` fails;
empty bullet lists fail; `research/` files must have `kind: research`
(and vice versa). Error message includes `file:line + field`.

## 5. Contacts whitelist + leak gate (implemented this commit)

* `contacts.allowlist.yaml` — canonical public emails (exact match) / profile
  URLs + `allow_patterns` (e.g. `*@users.noreply.github.com`). Phones list is
  intentionally empty: any phone-like string fails. `<old-home-email>` and
  `<uni-author-email>` are deliberately absent → flagged as leaks.
* `scripts/check_contacts.py` (stdlib only):
  `python3 scripts/check_contacts.py [--mode tree|history|all]`
  scans working-tree text files (skips `.git/`, binaries, `*.pdf`/LaTeX
  artefacts) plus `git log --all -p` patch text and `%ae/%ce` identities,
  using email / UK-phone / LinkedIn / GitHub regexes, and exits 1 with a
  `location [kind] value` list on any non-whitelisted hit.
* Expected states: `--mode tree` passes once hobby/PII content is flagged
  correctly; `--mode history` **fails until the pre-public squash** (proof
  the gate works). CI (later) runs tree gate on every push, history gate
  before any public-release job.

## 6. Migration + LaTeX adapter (next slices, not this commit)

1. Port `home/content/**` verbatim onto a private branch; split
   `projects/{robust-ml,signal-quality,moonboard-analysis}.md` → `research/`;
   add `kind` + `visibility` frontmatter; add `activities/*.md` from CV §Activities.
2. Implement `markdown_loader.py` + `scripts/validate.py`; fix every
   validator conflict from §2 (dates, LNAI status, LinkedIn canonical —
   currently CV slug in allowlist, confirm before public).
3. Implement `adapters/outbound/latex.py`: `escape_latex()`,
   `md_bullets_to_latex()`, `cv.tex.j2` → `dist/cv.tex`; local compile only
   (`tectonic`/texlive); `dist/cv.pdf` + aux files gitignored; scrub PDF
   `/Author` metadata. Stop committing `William_Dennis_CV_4_0.pdf`-style
   binaries; delete the current binary at squash time.
4. HTML stays stubbed; `home` remains the live site.

## 7. Private → single-commit public release (when directed)

1. Freeze clean tree: `check_contacts.py --mode tree` green (requires phone
   removal from `example_cv.tex`/content); confirm LinkedIn canonical;
   remove PDF binary + build artefacts.
2. Squash: `git checkout --orphan public-v1`, stage allowlisted tree only
   (`docs/PLAN.md` may be excluded if redaction policy requires),
   single commit with canonical author (research email vs noreply — TBC),
   `git branch -M main && git push -f origin main && git gc --prune=now`.
   Alternative: push same tree to a fresh public repo, keep this repo as
   private dev. Either is fine — never push old SHAs to the public remote.
3. Verify: `git log --format=fuller` shows 1 commit with clean identity;
   `git log --all -S <old-home-email>` / `-S <uni-id>` empty;
   `git grep -I -n` for email/phone patterns matches allowlist only.
4. Flip GitHub repo to Public. Then, separately: make `home` private →
   Archive, update links/redirects (`wd7512.github.io/home/` is printed on
   distributed CVs — plan a redirect note).

## 8. Done criteria for the schema-first milestone

* `uv run pytest` green (`test_domain`, `test_loader`: valid/invalid
  frontmatter, `visibility`/`kind` enforcement, unknown-field rejection).
* `uv run python scripts/validate.py` fails on current drift with a
  file-level report, passes after §6 fixes.
* `check_contacts.py --mode tree` green; `--mode history` failing is
  accepted until §7.
* `dist/cv.tex` renders from domain with correct LaTeX escaping; no
  hand-maintained `.tex` drift.

## 9. Open items (one at a time, next: canonical author)

* Single-commit author: research email vs `users.noreply`?
* LinkedIn canonical slug (allowlist currently holds CV variant).
* Public squash includes `docs/` or code-only?
* `wd7512.github.io/home/` redirect / custom domain?
