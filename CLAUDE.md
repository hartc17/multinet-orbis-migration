# Claude Code Instructions — Multinet to Orbis Migration

## Project overview

This project migrates boundary data from TomTom Multinet format to Orbis.
The data in scope is state, county, and zip code boundary polygons.
The core job is reading Multinet source data, transforming it to match Orbis's schema and geometry conventions, validating the result, and loading it into Orbis.

## Project conventions

- **Python 3.12**, venv at `.venv/`. Always activate with `source .venv/bin/activate`.
- **Run tests** with `pytest` from the project root. All tests must pass before committing.
- **Geospatial stack**: GDAL/OGR for format conversion, Shapely for geometry operations, GeoPandas/pandas for tabular and attribute-level transforms. Don't hand-roll geometry parsing or projection math that these libraries already provide.
- **Boundary identity is sacred**: never merge, split, or simplify a state/county/zip polygon unless the migration step explicitly calls for it. Attribute and topology mismatches between source and target must fail loudly, not get silently coerced.
- **Coordinate reference systems are explicit everywhere** — a function that takes or returns geometry names its CRS in the signature or an accompanying type alias; never pass a bare geometry and assume the caller knows the projection.

## General principles

- Never use the em dash "-". Use plain dash "-" instead.
- When writing commit messages, NEVER auto-add your agent name as co-author.
- Never manually modify CHANGELOG.md files or any files that are marked as auto-generated.
- When writing or substantially editing long Markdown files, put each full sentence on its own line.
  Preserve normal Markdown structure, but avoid wrapping multiple sentences onto one physical line.
- When making technical decisions, do not give much weight to development cost.
  Instead, prefer quality, simplicity, robustness, scalability, and long term maintainability.
- When doing bug fixes, always start with reproducing the bug as closely aligned with the real migration pipeline as possible, using real or representative source data and the real transform steps.
  This makes sure you find the real problem so your fix will actually solve it.
- Apply a high standard to engineering excellence: lint, test failures, and test flakiness.
  If you see one, even if it is not caused by what you are working on right now, still get it fixed.

## Data quality

- **Validate at every boundary crossing** — when data moves between Multinet's schema and Orbis's schema, assert the invariants that must hold (geometry validity, expected FIPS/zip code formats, non-null required attributes) rather than trusting the source blindly.
- **No silent data loss** — if a transform step drops records (unmatched IDs, invalid geometry, failed reprojection), it must log or report what was dropped and why, not just filter silently.
- **Idempotent transforms** — running the same migration step twice on the same input produces the same output. Avoid transforms that mutate shared state or append without deduplication.
- **No dead code** — remove unused functions, imports, and variables rather than commenting them out. If something might be needed later, that's what git history is for.
- **No speculative abstractions** — don't generalize a transform until there are at least three concrete cases (e.g. state, county, and zip all need it). Three similar functions is better than a premature shared abstraction that doesn't fit the fourth case.
- **Type annotations on all function signatures** — use Python 3.12 union syntax (`X | None`) not `Optional[X]`.

## Testing

- **Every new module gets a test file** — no untested public functions.
- **Tests must not hit the network or a real database** — use small synthetic Multinet/Orbis fixture files; mock any live service calls.
- **Test the behaviour, not the implementation** — assert on output geometry/attributes and side effects (records written, records flagged), not on internal call sequences.
- **Fixture files live in `tests/fixtures/`** — synthetic boundary polygons and sample schema rows used across multiple test files go there, not duplicated per file.
- **Name tests as `test_<thing>_<condition>_<expected>`** — e.g. `test_reproject_county_boundary_invalid_crs_raises`.

## Git

- **Never commit with `--no-verify`** — if a hook fails, fix the underlying issue.
- **Never force-push `main`**.
- **Never commit directly to `main`** — always create a feature branch, push it, and open a PR.
  The user will review and merge in GitHub.
- **One logical change per commit** — don't bundle unrelated fixes. If docs updates accompany a feature, include them in the same commit.
- **Always run `pytest` immediately before committing** — not just "it worked when I tested it."
- **After any set of changes**: create a branch (`claude/<short-slug>`), commit, push, and open a PR.
  Stop there — do not merge.

## Dependencies

- Pin new dependencies in `pyproject.toml` with a minimum version (`>=`) before using them.
- Install into the venv (`source .venv/bin/activate && pip install -e ".[dev]"`) and verify the import works before writing code that depends on it.
- Don't add a dependency for something that's in the standard library or already available via an existing dep.

## Documentation rule

After any significant migration step or pipeline change ships, update `README.md` (setup, usage, pipeline stages) and any architecture doc under `docs/` (data flow, schema mapping, CRS handling) before committing.
Check every doc for stale references. Do not leave forward-looking language in docs after the thing has been built.
