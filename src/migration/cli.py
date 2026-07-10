import argparse
from pathlib import Path

from migration.pipeline import run_crosswalk_pipeline
from migration.schema import CROSSWALK_BOUNDARY_TYPES


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multinet-orbis-crosswalk",
        description="Build a Multinet-to-Orbis GERS ID crosswalk for one boundary type.",
    )
    parser.add_argument("--multinet", type=Path, required=True, help="Path to a Multinet boundary source file.")
    parser.add_argument("--orbis", type=Path, required=True, help="Path to an Orbis divisions extract.")
    parser.add_argument("--boundary-type", choices=CROSSWALK_BOUNDARY_TYPES, required=True)
    parser.add_argument(
        "--source-vintage", required=True, help="Vintage/version label for this run, e.g. 2026-06."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write the crosswalk CSV and validation report JSON into.",
    )
    parser.add_argument(
        "--fips-check",
        action="store_true",
        help="Also run the Wikidata FIPS cross-check (requires network access to wikidata.org).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    result = run_crosswalk_pipeline(
        multinet_path=args.multinet,
        orbis_path=args.orbis,
        boundary_type=args.boundary_type,
        source_vintage=args.source_vintage,
        output_dir=args.output_dir,
        run_fips_check=args.fips_check,
    )

    print(f"Wrote crosswalk: {result.crosswalk_path}")
    print(f"Wrote validation report: {result.report_path}")
    print(
        f"{result.crosswalk_report.matched_count}/{result.crosswalk_report.source_count} matched "
        f"({len(result.crosswalk_report.unmatched_ids)} unmatched, "
        f"{len(result.crosswalk_report.duplicate_gers_ids)} duplicate gers_ids)"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
