#!/usr/bin/env python3
"""Classify weather values using thresholds stored in YAML."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "weather-thresholds.yaml"


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def load_config(path: Path) -> dict[str, Any]:
    """Load and validate the YAML threshold configuration."""
    try:
        with path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except FileNotFoundError as error:
        raise ConfigurationError(f"Config file not found: {path}") from error
    except yaml.YAMLError as error:
        raise ConfigurationError(f"Invalid YAML: {error}") from error

    if not isinstance(config, dict):
        raise ConfigurationError("Threshold config must contain a YAML object.")

    return config


def classify_value(
    value: float,
    levels: dict[str, dict[str, float]],
) -> str:
    """Return the severity range containing the supplied value."""
    for severity, boundaries in levels.items():
        minimum = boundaries.get("min")
        maximum = boundaries.get("max_exclusive")

        meets_minimum = minimum is None or value >= minimum
        below_maximum = maximum is None or value < maximum

        if meets_minimum and below_maximum:
            return severity

    raise RuntimeError(f"No configured severity range contains value {value}.")


def classify_factor(
    config: dict[str, Any],
    factor_name: str,
    value: float,
) -> dict[str, Any]:
    """Classify one named weather factor."""
    factor_config = config.get(factor_name)

    if not isinstance(factor_config, dict):
        raise RuntimeError(f"Unknown factor: {factor_name}")

    levels = factor_config.get("levels")

    if not isinstance(levels, dict):
        raise RuntimeError(f"Factor has no valid levels: {factor_name}")

    return {
        "factor": factor_name,
        "value": value,
        "severity": classify_value(value, levels),
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify one weather value using YAML thresholds."
    )
    parser.add_argument(
        "factor",
        help="Factor name from weather-thresholds.yaml.",
    )
    parser.add_argument(
        "value",
        type=float,
        help="Numeric weather value to classify.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to the YAML threshold configuration.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    try:
        config = load_config(args.config)
        result = classify_factor(
            config=config,
            factor_name=args.factor,
            value=args.value,
        )

        print(json.dumps(result, indent=2))
        return 0

    except RuntimeError as error:
        print(
            json.dumps(
                {
                    "status": "classification_error",
                    "message": str(error),
                },
                indent=2,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
