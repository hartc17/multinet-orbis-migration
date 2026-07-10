from pathlib import Path

import pytest

from migration.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_main_writes_crosswalk_and_report(tmp_path, capsys):
    exit_code = main(
        [
            "--multinet",
            str(FIXTURES / "multinet_state.geojson"),
            "--orbis",
            str(FIXTURES / "orbis_state.geojson"),
            "--boundary-type",
            "state",
            "--source-vintage",
            "2026-06",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "state_crosswalk.csv").exists()
    assert (tmp_path / "state_validation_report.json").exists()

    captured = capsys.readouterr()
    assert "Wrote crosswalk" in captured.out
    assert "1/1 matched" in captured.out


def test_main_rejects_unsupported_boundary_type(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "--multinet",
                str(FIXTURES / "multinet_zip.geojson"),
                "--orbis",
                str(FIXTURES / "multinet_zip.geojson"),
                "--boundary-type",
                "zip",
                "--source-vintage",
                "2026-06",
                "--output-dir",
                str(tmp_path),
            ]
        )

    assert exc_info.value.code == 2
