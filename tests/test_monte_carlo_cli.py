import math
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


def _write_payoff(temp_dir: Path, body: str) -> Path:
    path = temp_dir / "payoff_module.py"
    path.write_text(body)
    return path


def test_cli_prices_call_option_with_custom_payoff():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        payoff_path = _write_payoff(
            tmp_path,
            """
from __future__ import annotations

def payoff(path):
    return max(path[-1] - 100.0, 0.0)
            """.strip(),
        )

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "monte_carlo_cli",
                "--spot",
                "100",
                "--rate",
                "0.05",
                "--volatility",
                "0.0",
                "--maturity",
                "1.0",
                "--steps",
                "5",
                "--paths",
                "500",
                "--payoff",
                str(payoff_path),
                "--seed",
                "42",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        expected_terminal = 100 * math.exp(0.05 * 1.0)
        expected_payoff = max(expected_terminal - 100, 0.0)
        expected_price = expected_payoff * math.exp(-0.05 * 1.0)
        assert pytest.approx(float(result.stdout.strip()), rel=0, abs=1e-6) == expected_price


def test_cli_errors_on_missing_function():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        payoff_path = _write_payoff(tmp_path, "value = 1")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "monte_carlo_cli",
                "--spot",
                "50",
                "--rate",
                "0.01",
                "--volatility",
                "0.1",
                "--maturity",
                "0.5",
                "--steps",
                "2",
                "--paths",
                "10",
                "--payoff",
                str(payoff_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        error_message = result.stderr.lower()
        assert "payoff" in error_message
        assert "not found" in error_message
