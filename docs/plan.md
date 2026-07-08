# Migration Plan — TomTom Multinet to Orbis

## Goal

Build a repeatable pipeline that converts state, county, and zip code boundary data from TomTom Multinet format into Orbis, so that Orbis stays in sync as TomTom releases updated Multinet data.

## Starting point

Neither the Multinet source data/schema nor the Orbis target schema is in hand yet, and TomTom Multinet is commercially licensed — there is no public sample to download.
Rather than block on procurement, Milestones 2 and 3 were bootstrapped against a **synthetic placeholder schema** (see `src/migration/schema.py`) so pipeline code, tests, and fixtures could be built now.
Every placeholder field name must be revisited once a real Multinet sample and the real Orbis schema are obtained — treat the current schema as a stand-in shape, not a source of truth.

## Milestones

### 1. Data and schema acquisition

- Obtain a TomTom Multinet sample extract covering at least one full state (so county and zip layers nest correctly inside it) — likely via TomTom directly or an authorized reseller (e.g. ADCi), since this is licensed data.
- Obtain or write down the Orbis target schema: table/column names, geometry type and SRID, required vs. optional fields, and how Orbis expects boundary vintage/versioning to be represented.
- Identify how Orbis ingests data today (direct DB load, file import, API) — this determines the shape of the pipeline's load step.
- Confirm licensing/access terms for redistributing or storing Multinet data inside this repo's fixtures.
- **Status: blocked on procurement.** Development proceeds against the placeholder schema below in the meantime.

### 2. Environment and project scaffolding — done (placeholder schema)

- `pyproject.toml`, `.venv` (Python 3.12), with GeoPandas, Shapely, pandas, pyogrio, pytest, pytest-mock pinned.
- Project layout: `src/migration/` (`schema.py`, `extract.py`, `transform.py`, `validate.py`), `tests/`, `tests/fixtures/`.
- Synthetic fixtures for state/county/zip boundaries (nested Texas → Hays/Travis County → 78640/78704) exercise the extract → transform → validate path end to end; 7 tests passing.
- **Once real Multinet/Orbis schemas arrive**: replace `schema.py`'s placeholder field names and fixtures with the real ones, and re-verify every assumption baked into `extract.py`/`transform.py` against them.

### 3. Schema discovery and mapping

- Document the Multinet layers and fields relevant to state, county, and zip boundaries (geometry type, CRS, identifying codes such as FIPS/ZCTA, name fields, hierarchy/nesting fields).
- Document the Orbis equivalents field-by-field.
- Produce a mapping table (source field/type → target field/type, including any transform: reprojection, code lookups, unit conversions) for each of the three boundary types. This becomes the source of truth the transform code implements against.
- Flag any Orbis fields that have no Multinet source (need defaults or derivation) and any Multinet fields with no Orbis home (dropped, and why).

### 4. Extract stage

- Read Multinet boundary layers (state, county, zip) via GDAL/OGR into GeoPandas frames.
- Normalize CRS to a single known projection for internal processing; assert the CRS explicitly rather than assuming it.
- Fail loudly on missing layers, unreadable files, or unexpected schema drift from what Milestone 3 documented.

### 5. Transform stage

- Implement the field mapping from Milestone 3 for each boundary type.
- Validate geometry (validity, no self-intersections, expected ring orientation) and repair or reject invalid geometries per an explicit policy — never silently pass through invalid geometry.
- Preserve source-to-target lineage (e.g. a Multinet source ID column) so records can be traced and re-runs can be reconciled.

### 6. Validation stage

- Row-count reconciliation between source and output per boundary type.
- Spot-check topology: county boundaries nest inside their state, zip boundaries don't wildly exceed county extents (a sanity check, not full topological validation).
- Produce a validation report (counts, dropped records with reasons, geometry issues found) as a pipeline artifact, not just log lines.

### 7. Load stage

- Implement the write path into Orbis per whatever ingestion method Milestone 1 identifies.
- Make loads idempotent: re-running the pipeline against the same Multinet vintage produces the same Orbis state, not duplicates.
- Support incremental updates: when TomTom ships a new Multinet vintage, the pipeline should apply only the changed boundaries rather than requiring a full reload, if Orbis's ingestion method supports it.

### 8. Operationalization

- Decide and document how re-runs are triggered (manual invocation vs. scheduled) when new Multinet data arrives.
- Decide how boundary vintages are tracked so Orbis records which Multinet release they came from.
- Write the runbook: how to run the pipeline, how to read the validation report, how to roll back a bad load.

### 9. Documentation

- `README.md`: setup, how to run the pipeline end to end, where fixtures/sample data live.
- `docs/architecture.md`: data flow diagram (extract → transform → validate → load), the schema mapping tables from Milestone 3, and CRS handling decisions.

## Research findings on Orbis (2026-07-08)

TomTom's own developer portal (`developer.tomtom.com`) blocks automated fetches (403), so nothing below comes from reading TomTom's docs directly — only from public search snippets of TomTom/Overture pages, cross-checked against Overture Maps Foundation's own documentation.
Confirmed facts:

- Orbis is TomTom's own next-generation map platform, not a separate third-party system. It's built by fusing OpenStreetMap, Overture Maps, and TomTom's own data.
- Orbis's administrative boundaries are structured on the **Overture Maps Foundation "divisions" schema** (`division` / `division_area` / `division_boundary` feature types), not a Multinet-style flat table.
- Overture divisions use **GERS IDs** — persistent 128-bit identifiers assigned and maintained by Overture itself across data releases. This pipeline cannot mint GERS IDs; it can only receive them back from an Orbis lookup/match.
- Overture divisions carry a numeric **`admin_level`** hierarchy field (0, 1, 2…), added in Overture's February 2026 release.
- Orbis supports sample/bulk downloads in GeoParquet, PBF (protocol buffer / vector tiles), and Esri File Geodatabase (FGDB) formats.
- TomTom publishes per-API Multinet-to-Orbis migration guides (Routing, Geocoding, Traffic, Navigation SDKs), confirming this is a recognized, documented transition many customers are going through — but those guides are about API parameter changes, not a boundary-data schema mapping.

Explicitly **not confirmed** (treat as unverified even though plausible-sounding versions of these have circulated):

- Exact Multinet table/column names (e.g. `MN_Admin_Area`, `ADMIN_ID`, `ORDER02`) — Multinet's real spec is commercially licensed; nothing public confirms these names.
- Exact Overture/Orbis `subtype` enum values for county vs. zip/postal-code-equivalent divisions.
- Whether Orbis offers granular regional bulk downloads (e.g. a single-state extract).
- Whether US zip-equivalent divisions in Orbis follow ZCTA (Census) boundaries or postal delivery boundaries.

`src/migration/schema.py` has been updated to reflect the confirmed facts (`gers_id`, `admin_level`, `multinet_source_id` for lineage since we don't generate GERS IDs ourselves) while keeping Multinet-side fields and the exact `admin_level` values per boundary type explicitly marked as placeholders.

## Open architectural question

Because Orbis is TomTom's own authoritative dataset (not a database this project writes into), "migrate Multinet data to Orbis" most likely means one of:

1. **Re-source**: switch whatever internal/downstream system currently consumes Multinet-derived boundaries to instead consume the equivalent Orbis divisions data (via GeoParquet/FGDB download or vector tiles), keeping our own internal schema.
2. **Crosswalk**: keep existing Multinet-derived records/IDs in place, and produce a mapping from each Multinet boundary to its corresponding Orbis GERS ID (via spatial + attribute matching), so downstream references can be updated without a full re-extract.

The current pipeline code (`extract.py` → `transform.py` → `validate.py`) is written generically enough to fit either direction, but the **load stage** (Milestone 7) and the real shape of the "match" step depend on which of these it actually is. This needs to be resolved before Milestone 7 is built.

## Open questions to resolve during Milestone 1

- Which of the two directions above is this project actually doing (re-source vs. crosswalk)?
- Which Orbis ingestion/consumption path are we targeting (GeoParquet/FGDB bulk download, vector tiles, an API)?
- Does Orbis require a specific SRID, or does it accept multiple?
- How does Orbis represent zip codes — ZCTA (Census) boundaries or actual postal delivery zip boundaries? Multinet and Orbis may not agree on this by default.
- What's the update cadence for Multinet/Orbis releases, and does that dictate how "repeatable" the pipeline needs to be (fully automated vs. manually triggered per release)?
