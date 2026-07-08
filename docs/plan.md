# Migration Plan — TomTom Multinet to Orbis Crosswalk

## Goal

Build a repeatable pipeline that produces a **crosswalk** from existing TomTom Multinet-derived state, county, and zip code boundary records to their corresponding TomTom Orbis GERS IDs.
This is not a data load into Orbis (Orbis is TomTom's own authoritative dataset, not a database we write into) — it's a mapping so that systems currently keyed on Multinet's internal IDs can resolve the same real-world boundary in Orbis, and stay in sync as both datasets are updated over time.

## Starting point

Neither a real Multinet sample nor real Orbis divisions data is in hand yet (see Research findings below for why). Rather than block on procurement, the pipeline was bootstrapped against a **placeholder schema** for both sides (see `src/migration/schema.py`) so pipeline code, tests, and fixtures could be built now.
Every placeholder field name must be revisited once real Multinet and Orbis samples are obtained — treat the current schema as a stand-in shape, not a source of truth.

## Pipeline shape

1. **Extract Multinet** (`extract.read_multinet_boundaries`) — read a Multinet boundary file for one boundary type, assert required columns and CRS.
2. **Extract Orbis** (`extract.read_orbis_divisions`) — read an Orbis divisions extract for the same boundary type, assert required columns (`gers_id`, `name`, `admin_level`, geometry) and CRS.
3. **Match** (`match.match_to_orbis`) — for each Multinet boundary, compute its centroid (in an equal-area projection, not raw WGS84 degrees) and find the Orbis division whose polygon contains it. Produces one crosswalk row per Multinet boundary: `multinet_source_id`, `boundary_type`, `gers_id` (`None` if no Orbis polygon contains the centroid), `match_method` (`"spatial"` or `"unmatched"`), `source_vintage`.
4. **Validate** (`validate.validate_geometry`, `validate.validate_crosswalk`) — flag invalid source geometry before matching, and flag unmatched Multinet boundaries or Orbis IDs claimed by more than one Multinet boundary after matching. No silent data loss: every Multinet record either gets a `gers_id` or shows up in the unmatched list.

10 tests passing against placeholder-schema fixtures (Texas → Hays/Travis County → 78640/78704, all with real Census-derived geometry — see below — plus a deliberately unmatched zip to exercise the unmatched path).

## Milestones

### 1. Data and schema acquisition — blocked on procurement

- Obtain a TomTom Multinet sample extract covering at least one full state (so county and zip layers nest correctly) — likely via TomTom directly or an authorized reseller (e.g. ADCi), since this is licensed data.
- Obtain a real Orbis divisions extract for the same area (GeoParquet, PBF, or FGDB) to confirm the real schema (`gers_id`, `admin_level`, `subtype`, and whatever code/postal fields actually exist).
- Confirm licensing/access terms for storing either dataset's fixtures inside this repo.
- Development proceeds against the placeholder schema in the meantime.

### 2. Environment and project scaffolding — done

- `pyproject.toml`, `.venv` (Python 3.12), with GeoPandas, Shapely, pandas, pyogrio, pytest, pytest-mock pinned.
- Project layout: `src/migration/` (`schema.py`, `extract.py`, `match.py`, `validate.py`), `tests/`, `tests/fixtures/`.
- Fixture geometry is real, not synthetic: TomTom Multinet has no public sample (commercially licensed) and we have no real Orbis extract either, so fixture geometry was sourced from free, public-domain US Census TIGER/Line-derived boundaries (via `PublicaMundi/MappingAPI` for the state polygon, `plotly/datasets` for county polygons, and `OpenDataDE/State-zip-code-GeoJSON` for ZCTA polygons — all themselves reformattings of public Census data, no added license restrictions) and relabeled under our placeholder Multinet/Orbis field names. This gives tests real topology instead of toy squares, while the *field names and schema shape* remain placeholders pending real samples.
- **Once real Multinet/Orbis schemas arrive**: replace `schema.py`'s placeholder field names with the real ones, and re-verify every assumption in `extract.py`/`match.py` against them. The fixture geometry itself can likely stay (it's real US boundary data), only the property/column names need to change.

### 3. Schema discovery and mapping

- Document the Multinet layers/fields relevant to state, county, and zip boundaries (geometry type, CRS, identifying codes such as FIPS/ZCTA, name fields, hierarchy/nesting fields).
- Document the real Orbis/Overture divisions schema field-by-field (confirm `admin_level` values used for US state/county/zip-equivalent, confirm `subtype`, confirm whatever code/postal field exists).
- This becomes the source of truth `match.py`'s spatial-match assumptions and any future attribute-based matching (e.g. code equality as a secondary confidence check) implement against.

### 4. Matching quality

- Current match strategy is spatial-only (centroid-within-polygon). Once real Orbis code/postal fields are confirmed, add attribute-based cross-checks (FIPS/ZCTA equality) to upgrade `match_method` confidence beyond pure spatial containment.
- Handle edge cases once real data is available: a centroid landing exactly on a shared border, multi-polygon boundaries (islands, exclaves), and Orbis divisions that split or merge relative to their Multinet counterpart across vintages.

### 5. Validation and reporting

- Extend `validate_crosswalk`'s report into a real pipeline artifact (written to disk, not just returned in-memory) once this runs outside of tests.
- Decide the policy for unmatched records: block the run, or ship a partial crosswalk with unmatched boundaries flagged for manual review.

### 6. Operationalization

- Decide how re-runs are triggered (manual invocation vs. scheduled) as new Multinet or Orbis vintages ship.
- Decide how to detect and handle a boundary whose `gers_id` mapping changes between runs (e.g. an Orbis re-conflation), so the crosswalk itself has a change history, not just a snapshot.
- Write the runbook: how to run the pipeline, how to read the validation report, how to handle unmatched records.

### 7. Documentation

- `README.md`: setup, how to run the crosswalk pipeline end to end, where fixtures/sample data live.
- `docs/architecture.md`: data flow diagram (extract Multinet + extract Orbis → match → validate → crosswalk table), the schema mapping tables from Milestone 3, and CRS handling decisions.

## Research findings on Orbis (2026-07-08)

TomTom's own developer portal (`developer.tomtom.com`) blocks automated fetches (403), so nothing below comes from reading TomTom's docs directly — only from public search snippets of TomTom/Overture pages, cross-checked against Overture Maps Foundation's own documentation.
Confirmed facts:

- Orbis is TomTom's own next-generation map platform, not a separate third-party system. It's built by fusing OpenStreetMap, Overture Maps, and TomTom's own data.
- Orbis's administrative boundaries are structured on the **Overture Maps Foundation "divisions" schema** (`division` / `division_area` / `division_boundary` feature types), not a Multinet-style flat table.
- Overture divisions use **GERS IDs** — persistent 128-bit identifiers assigned and maintained by Overture itself across data releases. This project cannot mint GERS IDs; it can only receive them back from an Orbis lookup/match, which is exactly what the crosswalk direction requires.
- Overture divisions carry a numeric **`admin_level`** hierarchy field (0, 1, 2…), added in Overture's February 2026 release.
- Orbis supports sample/bulk downloads in GeoParquet, PBF (protocol buffer / vector tiles), and Esri File Geodatabase (FGDB) formats.
- TomTom publishes per-API Multinet-to-Orbis migration guides (Routing, Geocoding, Traffic, Navigation SDKs), confirming this is a recognized, documented transition many customers are going through — but those guides are about API parameter changes, not a boundary-data schema mapping.

Explicitly **not confirmed** (treat as unverified even though plausible-sounding versions of these have circulated):

- Exact Multinet table/column names (e.g. `MN_Admin_Area`, `ADMIN_ID`, `ORDER02`) — Multinet's real spec is commercially licensed; nothing public confirms these names.
- Exact Overture/Orbis `subtype` enum values for county vs. zip/postal-code-equivalent divisions.
- Whether Orbis offers granular regional bulk downloads (e.g. a single-state extract).
- Whether US zip-equivalent divisions in Orbis follow ZCTA (Census) boundaries or postal delivery boundaries.

`src/migration/schema.py` reflects the confirmed facts (`gers_id`, `admin_level`, `multinet_source_id` for lineage since we don't generate GERS IDs ourselves) while keeping exact `admin_level` values per boundary type and any code/postal fields explicitly marked as placeholders.

## Open questions to resolve during Milestone 1

- Which Orbis extraction path are we targeting for real matching (GeoParquet/FGDB bulk download, vector tiles, an API)?
- Does Orbis require a specific SRID, or does it accept multiple?
- How does Orbis represent zip codes — ZCTA (Census) boundaries or actual postal delivery zip boundaries? Multinet and Orbis may not agree on this by default, which affects match quality at zip-code granularity specifically.
- What's the update cadence for Multinet/Orbis releases, and how should the crosswalk be re-run/versioned as both change over time?
- What should happen to unmatched records in production — hard failure, or a flagged partial result?
