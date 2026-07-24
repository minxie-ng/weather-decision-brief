#!/usr/bin/env python3
"""Regression tests for deterministic Weather Decision Brief components."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))

from fetch_forecast import extract_hourly_window

PYTHON = sys.executable


def run_script(*arguments: str) -> dict:
    """Run a project script and parse its JSON output."""
    result = subprocess.run(
        [PYTHON, *arguments],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if not result.stdout.strip():
        raise AssertionError(
            f"Script produced no JSON output.\n"
            f"Return code: {result.returncode}\n"
            f"stderr: {result.stderr}"
        )

    return json.loads(result.stdout)


class PrepareDecisionTests(unittest.TestCase):
    def test_rejects_failed_forecast_status(self) -> None:
        payload = {
            "status": "location_not_found",
            "message": "No matching location was found.",
        }

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
        ) as file:
            json.dump(payload, file)
            path = file.name

        output = run_script(
            "scripts/prepare_decision.py",
            "--activity",
            "hiking",
            "--forecast-file",
            path,
        )

        self.assertEqual(output["status"], "decision_input_error")
        self.assertIn("status 'success'", output["message"])

    def test_rejects_missing_forecast_object(self) -> None:
        payload = {
            "status": "success",
            "resolved_location": {
                "name": "Bukit Timah",
                "timezone": "Asia/Singapore",
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
        ) as file:
            json.dump(payload, file)
            path = file.name

        output = run_script(
            "scripts/prepare_decision.py",
            "--activity",
            "hiking",
            "--forecast-file",
            path,
        )

        self.assertEqual(output["status"], "decision_input_error")
        self.assertEqual(output["message"], "Forecast object is missing.")

    def test_unsupported_activity_uses_fallback(self) -> None:
        output = run_script(
            "scripts/prepare_decision.py",
            "--activity",
            "kayaking",
            "--forecast-file",
            "tests/fixtures/sample-hiking-forecast.json",
        )

        self.assertEqual(output["status"], "decision_input_ready")
        self.assertEqual(output["activity"], "kayaking")
        self.assertEqual(output["profile_support"], "best_effort")
        self.assertEqual(output["activity_profile"], "general_outdoor")

    def test_v1_activity_profiles_are_supported(self) -> None:
        for activity in (
            "hiking",
            "commuting",
            "running",
            "cycling",
            "outdoor_events",
        ):
            with self.subTest(activity=activity):
                output = run_script(
                    "scripts/prepare_decision.py",
                    "--activity",
                    activity,
                    "--forecast-file",
                    "tests/fixtures/sample-hiking-forecast.json",
                )

                self.assertEqual(output["status"], "decision_input_ready")
                self.assertEqual(output["activity"], activity)
                self.assertEqual(output["profile_support"], "supported")
                self.assertEqual(output["activity_profile"], activity)

    def test_common_activity_aliases_resolve_to_supported_profiles(self) -> None:
        cases = {
            "jogging": "running",
            "bike ride": "cycling",
            "outdoor event": "outdoor_events",
        }

        for requested_activity, expected_profile in cases.items():
            with self.subTest(activity=requested_activity):
                output = run_script(
                    "scripts/prepare_decision.py",
                    "--activity",
                    requested_activity,
                    "--forecast-file",
                    "tests/fixtures/sample-hiking-forecast.json",
                )

                self.assertEqual(output["status"], "decision_input_ready")
                self.assertEqual(output["activity"], requested_activity)
                self.assertEqual(output["profile_support"], "supported")
                self.assertEqual(
                    output["activity_profile"],
                    expected_profile,
                )


class ForecastWindowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hourly = {
            "time": [
                "2026-07-26T08:00",
                "2026-07-26T09:00",
                "2026-07-26T10:00",
                "2026-07-26T23:00",
                "2026-07-27T00:00",
                "2026-07-27T01:00",
                "2026-07-27T02:00",
            ],
            "temperature_2m": [28, 29, 30, 27, 26, 26, 25],
        }

    def test_same_day_window(self) -> None:
        extracted, window = extract_hourly_window(
            self.hourly,
            "2026-07-26",
            "08:00",
            "11:00",
        )

        self.assertEqual(
            extracted["time"],
            [
                "2026-07-26T08:00",
                "2026-07-26T09:00",
                "2026-07-26T10:00",
            ],
        )
        self.assertEqual(window["start"], "2026-07-26T08:00")
        self.assertEqual(
            window["end_exclusive"],
            "2026-07-26T11:00",
        )

    def test_cross_midnight_window(self) -> None:
        extracted, window = extract_hourly_window(
            self.hourly,
            "2026-07-26",
            "23:00",
            "02:00",
        )

        self.assertEqual(
            extracted["time"],
            [
                "2026-07-26T23:00",
                "2026-07-27T00:00",
                "2026-07-27T01:00",
            ],
        )
        self.assertEqual(window["start"], "2026-07-26T23:00")
        self.assertEqual(
            window["end_exclusive"],
            "2026-07-27T02:00",
        )

    def test_identical_times_are_rejected(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            "cannot be identical",
        ):
            extract_hourly_window(
                self.hourly,
                "2026-07-26",
                "08:00",
                "08:00",
            )


class DecisionValidatorTests(unittest.TestCase):
    def test_valid_decision_passes(self) -> None:
        output = run_script(
            "scripts/validate_decision.py",
            "examples/hiking-decision-output.json",
        )

        self.assertEqual(output["status"], "valid")

    def test_invalid_verdict_fails(self) -> None:
        source = json.loads(
            (PROJECT_ROOT / "examples/hiking-decision-output.json").read_text()
        )
        source["verdict"] = "maybe"

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
        ) as file:
            json.dump(source, file)
            path = file.name

        output = run_script(
            "scripts/validate_decision.py",
            path,
        )

        self.assertEqual(output["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
