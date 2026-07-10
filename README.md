# multinet-orbis-migration

Builds a crosswalk from state and county boundary records derived from TomTom Multinet to their corresponding TomTom Orbis GERS IDs.
Zip code is currently out of scope — Orbis's divisions schema (Overture Maps Foundation-based) has no confirmed zip/postal-code equivalent. See [`docs/plan.md`](docs/plan.md) for details.

See [`docs/plan.md`](docs/plan.md) for the migration plan and current milestone status.

## Setup

Requires Python 3.12.

```
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
```

Run the test suite from the project root:

```
pytest
```

## Usage

The pipeline is exposed as the `multinet-orbis-crosswalk` console script (installed by `pip install -e .`).
It reads one Multinet source file and one Orbis divisions extract for a single boundary type, matches them, validates the result, and writes two artifacts to `--output-dir`: a `<boundary_type>_crosswalk.csv` and a `<boundary_type>_validation_report.json`.

```
multinet-orbis-crosswalk \
  --multinet path/to/multinet_county.geojson \
  --orbis path/to/orbis_county.geojson \
  --boundary-type county \
  --source-vintage 2026-06 \
  --output-dir out/
```

Add `--fips-check` to also run the secondary Wikidata FIPS cross-check (`migration.fips_check.cross_check_fips`).
This makes a live network call to `wikidata.org` per matched county, so only use it where that's reachable.

You can try this against the repo's own test fixtures, which carry real Overture geometry and GERS IDs for Texas, Hays County, and Travis County:

```
multinet-orbis-crosswalk \
  --multinet tests/fixtures/multinet_county.geojson \
  --orbis tests/fixtures/orbis_county.geojson \
  --boundary-type county \
  --source-vintage 2026-06 \
  --output-dir /tmp/mo_smoke
```

Invalid source geometry (on either the Multinet or Orbis side) raises `migration.pipeline.InvalidSourceGeometryError` and aborts the run before any output is written — that failure mode is a data-integrity gate, not the same thing as an unmatched record.
Unmatched Multinet boundaries and duplicate `gers_id` claims do not currently block the run; they are written into the validation report for review.
The policy for whether those should block a run instead is still an open decision — see `docs/plan.md`, Milestone 5.
