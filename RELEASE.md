# Release process

How a change travels from my laptop to the children, and how I undo it if something goes wrong.

## Branches

| Branch | Purpose | Who writes to it |
|---|---|---|
| `main` | Integration: all finished work | Me (push or merged pull request) |
| `release` | **Production**: what Streamlit Cloud serves to the children | **Only the pipeline** (promote / rollback) |

## Quality gates (`.github/workflows/ci.yml`)

Every push or pull request to `main` runs:

| # | Gate | What it checks | Blocks release if |
|---|---|---|---|
| 1 | Lint & unit tests | `ruff` style/bug checks; 50+ offline tests with a fake Groq, including clicking through the real app | any test fails |
| 2 | AI quality & safety | 48 real questions through the live pipeline: space facts, off-topic, jailbreaks, unsafe requests, privacy | overall pass rate < 90% **or** safety pass rate < 95% |
| 3 | Promote | Fast-forwards `release` to the tested commit | only runs if 1 and 2 are green |

The eval report (pass rates, failures, reading level, latency) appears on the workflow's summary page and as a downloadable artifact.

## Versioning (SemVer)

- **MAJOR** (3.0.0): big changes to how the app works
- **MINOR** (2.1.0): new features (e.g. a new language)
- **PATCH** (2.0.1): fixes, prompt tweaks

## Cutting a release

1. Update `__version__` in `cosmo/__init__.py`.
2. Add a `## [x.y.z] - date` section to `CHANGELOG.md`.
3. Commit and push to `main`; wait for the pipeline to go green (the app is now live).
4. Tag it: `git tag v2.1.0 && git push origin v2.1.0`.
   The **Release** workflow checks the tag matches the code version and publishes GitHub Release notes from the changelog.

## Rollback (≈ 1 minute)

GitHub → **Actions** → **Rollback production** → **Run workflow** → enter the last good tag (e.g. `v2.0.0`) and a reason.
The `release` branch jumps back to that version and Streamlit Cloud redeploys it. Then fix forward on `main`.

## Incident checklist

1. Children see "Cosmo's radio is fuzzy" → Streamlit Cloud → Manage app → **Logs**: look for `Groq key #n failed`.
2. All keys rate-limited → wait, or add a key in Streamlit **Secrets** (no redeploy needed beyond the automatic restart).
3. A model was retired by Groq → the app already falls back; update `CHAT_MODELS` in `cosmo/prompts.py` and release a PATCH.
4. Bad answers after a change → **Rollback**, then add the failing question to `evals/cases.json` so it can never slip through again.
