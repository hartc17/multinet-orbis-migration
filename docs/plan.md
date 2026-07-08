# Migration Plan — TomTom Multinet to Orbis Crosswalk

## Goal

Build a repeatable pipeline that produces a **crosswalk** from existing TomTom Multinet-derived state and county boundary records to their corresponding TomTom Orbis GERS IDs.
This is not a data load into Orbis (Orbis is TomTom's own authoritative dataset, not a database we write into) — it's a mapping so that systems currently keyed on Multinet's internal IDs can resolve the same real-world boundary in Orbis, and stay in sync as both datasets are updated over time.

**Zip code is currently out of scope** — see "Confirmed gap" below.

## Starting point

No real Multinet sample is in hand (commercially licensed, no public sample exists). But the Orbis side is in much better shape than originally expected: Orbis's divisions schema is built on the **Overture Maps Foundation's open data**, which is free and directly readable. `schema.py`'s Orbis-side fields (`id`, `subtype`, `admin_level`) and the fixtures are now based on **real data read directly from Overture's public dataset**, not guesses. Only the Multinet side remains a placeholder.

## Pipeline shape

1. **Extract Multinet** (`extract.read_multinet_boundaries`) — read a Multinet boundary file for one boundary type, assert required columns and CRS. *(Still placeholder field names — no real Multinet sample yet.)*
2. **Extract Orbis** (`extract.read_orbis_divisions`) — read an Orbis divisions extract for `state` or `county` (raises for `zip` — see Confirmed gap), assert required columns (`id`, `subtype`, `admin_level`, geometry) and CRS. *(Real, confirmed field names.)*
3. **Match** (`match.match_to_orbis`) — for each Multinet boundary, compute its centroid (in an equal-area projection, not raw WGS84 degrees) and find the Orbis division of the matching `admin_level` whose polygon contains it. Produces one crosswalk row per Multinet boundary: `multinet_source_id`, `boundary_type`, `gers_id` (`None` if unmatched), `match_method` (`"spatial"` or `"unmatched"`), `source_vintage`.
4. **Validate** (`validate.validate_geometry`, `validate.validate_crosswalk`) — flag invalid source geometry before matching, and flag unmatched Multinet boundaries or Orbis IDs claimed by more than one Multinet boundary after matching. No silent data loss: every Multinet record either gets a `gers_id` or shows up in the unmatched list.

12 tests passing. Fixtures use **real geometry and real GERS IDs** for Texas (region), Hays County, and Travis County, read directly from Overture's open dataset (release `2026-06-17.0`) — plus El Paso County, present on the Multinet side but deliberately omitted from the Orbis fixture, to exercise the unmatched path.

## Confirmed gap: no zip/postal-code division in Overture (and likely Orbis)

Queried Overture's real `division_area` data for the entire state of Texas directly (`admin_level >= 3`): **zero rows**. The only `subtype` values that exist anywhere in Texas are `country`, `region`, `county`, `locality`, `neighborhood`, `microhood`, `macrohood` — no postal/zip-code-equivalent division exists in this dataset at all.

Since Orbis's divisions are built on this same Overture schema, there is a real possibility Orbis has **no zip-code division to crosswalk against, structurally** — not merely an unconfirmed field name, but a potentially absent concept in this data source.

Per decision: zip is dropped from the crosswalk's scope for now (`CROSSWALK_BOUNDARY_TYPES = ("state", "county")` in `schema.py`; `read_orbis_divisions`/`match_to_orbis` raise a clear `ValueError` if called with `"zip"`). Multinet-side zip extraction remains available (`read_multinet_boundaries` still supports `"zip"`) since that half isn't blocked — only the Orbis crosswalk side is.

**To unblock zip**: confirm with an actual Orbis account/docs whether Orbis has a separate, non-Overture-divisions postal-boundary product, or whether zip-level crosswalking needs to happen through Census ZCTA / USPS data independently of Orbis, or is simply not supported.

## Milestones

### 1. Data acquisition — Multinet blocked, Orbis unblocked

- Multinet: still need a real sample extract (via TomTom directly or a reseller like ADCi) to replace `schema.py`'s placeholder Multinet field names (`ID`, `NAME`, `FIPS_CODE`, `PARENT_ID`) with real ones.
- Orbis: **unblocked**. Real divisions data is read directly from Overture's public S3 bucket (`s3://overturemaps-us-west-2/release/<version>/theme=divisions/type=division_area/`), bypassing `developer.tomtom.com` and `stac.overturemaps.org`/`labs.overturemaps.org` (both blocked by this session's network policy) by listing the bucket's `release/` prefix directly and reading the Parquet dataset via `pyarrow` with an explicit release string. See `src/migration/schema.py` for the confirmed field names.
- Still open: whether real TomTom Orbis output differs from raw Overture divisions in any way (e.g. TomTom-specific refinements, different `id` values) — this reads Overture's own data, not an actual Orbis API/export, since the latter requires an Orbis account.

### 2. Environment and project scaffolding — done

- `pyproject.toml`, `.venv` (Python 3.12), with GeoPandas, Shapely, pandas, pyogrio, pytest, pytest-mock pinned (plus `overturemaps`/`pyarrow`, used one-off to pull real fixture data — not a runtime pipeline dependency yet).
- Project layout: `src/migration/` (`schema.py`, `extract.py`, `match.py`, `validate.py`), `tests/`, `tests/fixtures/`.
- Fixture geometry and Orbis IDs are real: Texas/Hays County/Travis County/El Paso County geometry and GERS IDs pulled directly from Overture's open, ODbL-licensed dataset. Multinet-side fixtures reuse this same real geometry relabeled under placeholder Multinet field names (`ID`, `NAME`, `FIPS_CODE`, `PARENT_ID`) since Multinet itself has no public sample.
- **Once a real Multinet sample arrives**: replace `schema.py`'s placeholder Multinet field names with the real ones, and re-verify `extract.read_multinet_boundaries`'s assumptions against them. The Orbis side and its fixtures should not need to change.

### 3. Schema discovery and mapping

- Multinet: still to document (layers/fields for state, county, and zip boundaries — geometry type, CRS, identifying codes, name fields, hierarchy fields) once a real sample exists.
- Orbis: done for state/county — see `schema.py` and the Confirmed gap section above for zip.

### 4. Matching quality

- Current match strategy is spatial-only (centroid-within-polygon, filtered to the correct `admin_level`). A real Multinet sample would let us add attribute-based cross-checks (FIPS equality) to upgrade `match_method` confidence beyond pure spatial containment.
- Handle edge cases once a real Multinet sample is available: a centroid landing exactly on a shared border, multi-polygon Multinet boundaries (Overture's own Texas geometry is a 88-part `MultiPolygon` with tiny islands/exclaves — Multinet's likely is too), and Orbis divisions that split or merge relative to their Multinet counterpart across vintages.

### 5. Validation and reporting

- Extend `validate_crosswalk`'s report into a real pipeline artifact (written to disk, not just returned in-memory) once this runs outside of tests.
- Decide the policy for unmatched records: block the run, or ship a partial crosswalk with unmatched boundaries flagged for manual review.

### 6. Operationalization

- Decide how re-runs are triggered (manual invocation vs. scheduled) as new Multinet or Overture/Orbis releases ship (Overture ships roughly monthly; releases are enumerable directly from the S3 bucket's `release/` prefix without needing the blocked STAC catalog).
- Decide how to detect and handle a boundary whose `gers_id` mapping changes between runs (Overture does re-conflate features across releases), so the crosswalk itself has a change history, not just a snapshot.
- Write the runbook: how to run the pipeline, how to read the validation report, how to handle unmatched records.

### 7. Documentation

- `README.md`: setup, how to run the crosswalk pipeline end to end, where fixtures/sample data live.
- `docs/architecture.md`: data flow diagram (extract Multinet + extract Orbis → match → validate → crosswalk table), the schema mapping tables from Milestone 3, and CRS handling decisions.

## Research findings (2026-07-08)

TomTom's own developer portal (`developer.tomtom.com`) and Overture's STAC catalog domains (`stac.overturemaps.org`, `labs.overturemaps.org`) are blocked by this session's network policy (403 on CONNECT). Overture's actual data bucket (`overturemaps-us-west-2.s3.amazonaws.com`) is **not** blocked and was read directly.

Confirmed facts:

- Orbis is TomTom's own next-generation map platform, not a separate third-party system. It's built by fusing OpenStreetMap, Overture Maps, and TomTom's own data.
- Orbis's administrative boundaries are structured on the **Overture Maps Foundation "divisions" schema**, not a Multinet-style flat table.
- The real `division_area` schema (confirmed by reading it directly): `id` (a UUID string — this **is** the GERS ID, not a separately-formatted field), `geometry`, `country`, `sources` (array of `{dataset, license, record_id, update_time, ...}`), `subtype`, `admin_level`, `class`, `names` (`{primary, common, rules[...]}`), `is_land`, `is_territorial`, `region` (e.g. `"US-TX"`), `division_id`, `version`, `bbox`.
- Confirmed real `admin_level`/`subtype` values in the US: `0`/`country`, `1`/`region` (state), `2`/`county`. No zip/postal level exists (see Confirmed gap above).
- Source data license for these Overture-derived fixtures: `ODbL-1.0` (OpenStreetMap-derived), confirmed via the `sources` field on the records actually pulled.
- Orbis also supports sample/bulk downloads in GeoParquet, PBF (vector tiles), and Esri File Geodatabase (FGDB) formats, per TomTom's marketing pages.
- TomTom publishes per-API Multinet-to-Orbis migration guides (Routing, Geocoding, Traffic, Navigation SDKs), confirming this is a recognized, documented transition — but those guides are about API parameter changes, not boundary-data schema mapping.

Explicitly **not confirmed**:

- Exact Multinet table/column names (e.g. `MN_Admin_Area`, `ADMIN_ID`, `ORDER02`) — Multinet's real spec is commercially licensed; nothing public confirms these names.
- Whether TomTom's actual Orbis product output matches raw Overture divisions exactly, or applies its own refinements on top.
- Whether Orbis offers granular regional bulk downloads (e.g. a single-state extract).
- Any zip/postal-code data source on the Orbis side outside of the divisions theme.

## Open questions to resolve during Milestone 1

- Multinet: obtain a real sample to replace placeholder field names.
- Orbis/zip: is there a non-Overture-divisions postal boundary product in Orbis, or is zip-level crosswalking out of scope permanently?
- Does an actual Orbis account/export differ from directly-read Overture data in any way relevant to this crosswalk?
- What's the update cadence for Multinet/Overture releases, and how should the crosswalk be re-run/versioned as both change over time?
- What should happen to unmatched records in production — hard failure, or a flagged partial result?
