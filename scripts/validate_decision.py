#!/usr/bin/env python3
"""Validate a Weather Decision Brief result against its YAML schema."""

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
DEFAULT_SCHEMA = PROJECT_ROOT / "config" / "decision-schema.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file as a dictionary."""
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError as error:
        raise RuntimeError(f"File not found: {path}") from error
    except yaml.YAMLError as error:
        raise RuntimeError(f"Invalid YAML: {error}") from error

    if not isinstance(data, dict):
        raise RuntimeError("Schema must contain a YAML object.")

    return data


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON decision file."""
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as error:
        raise RuntimeError(f"File not found: {path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid JSON: {error}") from error

    if not isinstance(data, dict):
        raise RuntimeError("Decision output must contain a JSON object.")

    return data


def validate_decision(
    decision: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    """Return a list of validation errors."""
    errors: list[str] = []

    required_fields = schema.get("required_fields", [])

    for field in required_fields:
        if field not in decision:
            errors.append(f"Missing required field: {field}")

    verdict = decision.get("verdict")
    allowed_verdicts = schema.get("allowed_verdicts", [])

    if verdict is not None and verdict not in allowed_verdicts:
        errors.append(f"Invalid verdict: {verdict}")

    confidence = decision.get("confidence")
    allowed_confidence = schema.get("allowed_confidence", [])

    if confidence is not None and confidence not in allowed_confidence:
        errors.append(f"Invalid confidence: {confidence}")

    profile_support = decision.get("profile_support")
    allowed_profile_support = schema.get(
        "allowed_profile_support",
        [],
    )

    if (
        profile_support is not None
        and profile_support not in allowed_profile_support
    ):
        errors.append(
            f"Invalid profile_support: {profile_support}"
        )

    field_rules = schema.get("field_rules", {})

    for field_name, rules in field_rules.items():
        if field_name not in decision:
            continue

        expected_type = rules.get("type")

        if expected_type == "list" and not isinstance(
            decision[field_name],
            list,
        ):
            errors.append(
                f"Field must be a list: {field_name}"
            )

    time_window = decision.get("time_window")

    if isinstance(time_window, dict):
        required_time_fields = (
            field_rules
            .get("time_window", {})
            .get("required_fields", [])
        )

        for field in required_time_fields:
            if field not in time_window:
                errors.append(
                    f"Missing time_window field: {field}"
                )
    elif time_window is not None:
        errors.append("Field must be an object: time_window")

    return errors


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a weather decision JSON file."
    )
    parser.add_argument(
        "decision_file",
        type=Path,
        help="Path to the decision JSON file.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help="Path to decision-schema.yaml.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    try:
        schema = load_yaml(args.schema)
        decision = load_json(args.decision_file)
        errors = validate_decision(decision, schema)

        if errors:
            print(
                json.dumps(
                    {
                        "status": "invalid",
                        "errors": errors,
                    },
                    indent=2,
                )
            )
            return 1

        print(
            json.dumps(
                {
                    "status": "valid",
                    "message": (
                        "Decision output matches the required schema."
                    ),
                },
                indent=2,
            )
        )
        return 0

    except RuntimeError as error:
        print(
            json.dumps(
                {
                    "status": "validation_error",
                    "message": str(error),
                },
                indent=2,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
