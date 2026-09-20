"""Exercise exported units, fit-file schema and actionable CLI failures."""

import json
import subprocess
import sys

import numpy as np
import pytest

from pn_junction import DiodeParameters, voltage_at_current
from pn_junction.cli import main


def test_simulate_exports_profiles_and_units(tmp_path, capsys):
    target = tmp_path / "nested" / "junction.csv"
    assert main(["simulate", "--output", str(target)]) == 0
    summary = json.loads(capsys.readouterr().out)
    profiles = np.genfromtxt(target, delimiter=",", names=True)
    assert summary["nodes"] == profiles.size == 801
    assert profiles["potential_V"][-1] == pytest.approx(summary["built_in_voltage_V"])
    assert profiles.dtype.names[0] == "position_m"


def test_fit_csv_exports_parameters_and_errors(tmp_path, capsys):
    current = np.geomspace(1e-9, 0.02, 60)
    source = tmp_path / "observations.csv"
    np.savetxt(
        source,
        np.column_stack(
            [
                current,
                voltage_at_current(current, DiodeParameters()),
                np.full_like(current, 0.001),
            ]
        ),
        delimiter=",",
        comments="",
        header="current_A,voltage_V,sigma_voltage_V",
    )
    output = tmp_path / "fit.json"
    assert main(["fit", str(source), "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result == json.loads(capsys.readouterr().out)
    assert result["parameters"]["series_resistance_ohm"] == pytest.approx(5)
    assert len(result["standard_errors"]) == 3


@pytest.mark.parametrize(
    "content",
    [
        "I,V\n1,2\n",
        "current_A,voltage_V,sigma_voltage_V\n",
        "current_A,voltage_V,sigma_voltage_V\n1,oops,0.1\n",
    ],
)
def test_invalid_csv_reports_error(tmp_path, capsys, content):
    source = tmp_path / "bad.csv"
    source.write_text(content)
    with pytest.raises(SystemExit) as stopped:
        main(["fit", str(source), "--output", str(tmp_path / "out.json")])
    assert stopped.value.code == 2
    assert "error:" in capsys.readouterr().err


def test_module_entrypoint_and_bad_physics(tmp_path):
    run = subprocess.run(
        [sys.executable, "-m", "pn_junction", "--version"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=True,
    )
    assert run.stdout.strip() == "0.1.0"
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pn_junction",
            "simulate",
            "--donor-cm3",
            "-1",
            "--output",
            str(tmp_path / "bad.csv"),
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    assert run.returncode == 2
    assert "donor_cm3" in run.stderr
    assert not (tmp_path / "bad.csv").exists()
