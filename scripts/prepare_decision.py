#!/usr/bin/env python3
"""Prepare structured evidence for an activity-specific weather decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:
    raise SystemExit(
        "Missing dependency: PyYAML. "
        "Ask the user for permission before running: "
        "python3 -m pip install -r requirements.txt"
    )


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILES = PROJECT_ROOT / "config" / "activity-profiles.yaml"


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from a file."""
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as error:
        raise RuntimeError(f"File not found: {path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid JSON: {error}") from error

    if not isinstance(data, dict):
        raise RuntimeError("Forecast file must contain a JSON object.")

    return data


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML object from a file."""
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError as error:
        raise RuntimeError(f"File not found: {path}") from error
    except yaml.YAMLError as error:
        raise RuntimeError(f"Invalid YAML: {error}") from error

    if not isinstance(data, dict):
        raise RuntimeError("Activity profile file must contain a YAML object.")

    return data


def resolve_profile(
    activity: str,
    profile_config: dict[str, Any],
) -> dict[str, Any]:
    """Return a supported profile or the best-effort fallback."""
    profiles = profile_config.get("profiles", {})

    if not isinstance(profiles, dict):
        raise RuntimeError("Activity profiles configuration is invalid.")

    normalized_activity = activity.strip().lower()

    activity_aliases = {
        "jogging": "running",
        "run": "running",
        "bike ride": "cycling",
        "biking": "cycling",
        "cycle": "cycling",
        "outdoor event": "outdoor_events",
        "outdoor-event": "outdoor_events",
        "event outdoors": "outdoor_events",
    }

    canonical_activity = activity_aliases.get(
        normalized_activity,
        normalized_activity.replace("-", "_").replace(" ", "_"),
    )

    profile = profiles.get(canonical_activity)

    if isinstance(profile, dict):
        return {
            "requested_activity": normalized_activity,
            "profile_support": "supported",
            "activity_profile": canonical_activity,
            "profile_guidance": profile,
            "fallback_limitation": None,
        }

    fallback = profile_config.get("fallback", {})

    if not isinstance(fallback, dict):
        raise RuntimeError("Fallback activity profile is missing.")

    return {
        "requested_activity": normalized_activity,
        "profile_support": fallback.get("support", "best_effort"),
        "activity_profile": fallback.get(
            "activity_profile",
            "general_outdoor",
        ),
        "profile_guidance": fallback,
        "fallback_limitation": fallback.get(
            "limitation",
            "No dedicated activity profile exists.",
        ),
    }


def build_decision_package(
    forecast_result: dict[str, Any],
    activity: str,
    profile_config: dict[str, Any],
    personal_constraints: list[str],
) -> dict[str, Any]:
    """Combine forecast evidence and activity guidance."""
    if forecast_result.get("status") != "success":
        raise RuntimeError(
            "Forecast input must have status 'success'."
        )

    resolved_location = forecast_result.get("resolved_location")
    forecast = forecast_result.get("forecast")

    if not isinstance(resolved_location, dict):
        raise RuntimeError("Resolved location is missing.")

    if not isinstance(forecast, dict):
        raise RuntimeError("Forecast object is missing.")

    requested_window = forecast.get("requested_window")
    window_summary = forecast.get("window_summary")

    if not isinstance(requested_window, dict):
        raise RuntimeError(
            "A bounded requested window is required."
        )

    if not isinstance(window_summary, dict):
        raise RuntimeError(
            "Classified window summary is missing."
        )

    profile = resolve_profile(
        activity=activity,
        profile_config=profile_config,
    )

    assumptions: list[str] = []
    limitations: list[str] = []

    if personal_constraints:
        assumptions.append(
            "Only the personal constraints explicitly supplied were used."
        )
    else:
        assumptions.append(
            "A general-user fitness and mobility baseline was used."
        )

    if profile["fallback_limitation"]:
        limitations.append(profile["fallback_limitation"])

    limitations.append(
        "Official weather alerts and air-quality data were not checked."
    )

    return {
        "status": "decision_input_ready",
        "activity": profile["requested_activity"],
        "profile_support": profile["profile_support"],
        "activity_profile": profile["activity_profile"],
        "resolved_location": resolved_location,
        "timezone": forecast.get("timezone"),
        "date": requested_window.get("date"),
        "time_window": {
            "start": requested_window.get("start"),
            "end_exclusive": requested_window.get(
                "end_exclusive"
            ),
        },
        "weather_evidence": window_summary,
        "profile_guidance": profile["profile_guidance"],
        "personal_constraints": personal_constraints,
        "assumptions": assumptions,
        "limitations": limitations,
        "agent_task": (
            "Use the classified weather evidence, activity profile, timing, "
            "and personal constraints to produce one allowed verdict: "
            "proceed, adjust, postpone, or insufficient_information. "
            "Do not change the supplied weather severities."
        ),
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare weather evidence and activity guidance "
            "for contextual agent reasoning."
        )
    )

    parser.add_argument(
        "--activity",
        required=True,
        help="Planned activity, such as hiking or commuting.",
    )

    parser.add_argument(
        "--forecast-file",
        required=True,
        type=Path,
        help="JSON output produced by fetch_forecast.py.",
    )

    parser.add_argument(
        "--constraint",
        action="append",
        default=[],
        help=(
            "Optional personal constraint. "
            "May be supplied more than once."
        ),
    )

    parser.add_argument(
        "--profiles",
        type=Path,
        default=DEFAULT_PROFILES,
        help="Path to activity-profiles.yaml.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    try:
        forecast_result = load_json(args.forecast_file)
        profile_config = load_yaml(args.profiles)

        result = build_decision_package(
            forecast_result=forecast_result,
            activity=args.activity,
            profile_config=profile_config,
            personal_constraints=args.constraint,
        )

        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    except RuntimeError as error:
        print(
            json.dumps(
                {
                    "status": "decision_input_error",
                    "message": str(error),
                },
                indent=2,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
