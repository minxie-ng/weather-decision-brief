#!/usr/bin/env python3
"""Resolve a place and retrieve decision-ready hourly weather data."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from classify_factors import ConfigurationError, classify_value, load_config


class ForecastWindowUnavailableError(RuntimeError):
    """Raised when provider data does not cover the requested window."""



GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
THRESHOLD_CONFIG = PROJECT_ROOT / "config" / "weather-thresholds.yaml"

HOURLY_VARIABLES = [
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "precipitation_probability",
    "precipitation",
    "weather_code",
    "visibility",
    "wind_speed_10m",
    "wind_gusts_10m",
]


def request_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    """Make an HTTP GET request and return parsed JSON."""
    query_string = urllib.parse.urlencode(params)
    request_url = f"{url}?{query_string}"

    try:
        with urllib.request.urlopen(request_url, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"Provider returned HTTP {error.code}: {error.reason}"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Could not reach provider: {error.reason}"
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError("Provider returned invalid JSON") from error


def geocode(place_name: str) -> list[dict[str, Any]]:
    """Return up to three matching locations."""
    payload = request_json(
        GEOCODING_URL,
        {
            "name": place_name,
            "count": 3,
            "language": "en",
            "format": "json",
        },
    )

    results = payload.get("results", [])

    return [
        {
            "name": result.get("name"),
            "admin1": result.get("admin1"),
            "country": result.get("country"),
            "country_code": result.get("country_code"),
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
            "timezone": result.get("timezone"),
        }
        for result in results
    ]


def fetch_forecast(location: dict[str, Any]) -> dict[str, Any]:
    """Retrieve hourly forecast data for a resolved location."""
    return request_json(
        FORECAST_URL,
        {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "hourly": ",".join(HOURLY_VARIABLES),
            "timezone": location["timezone"] or "auto",
            "forecast_days": 7,
        },
    )


def extract_hourly_window(
    hourly: dict[str, Any],
    activity_date: str,
    start_time: str,
    end_time: str,
) -> tuple[dict[str, list[Any]], dict[str, str]]:
    """Keep forecast rows inside the resolved local-time window."""
    try:
        start = datetime.fromisoformat(
            f"{activity_date}T{start_time}"
        )
        end = datetime.fromisoformat(
            f"{activity_date}T{end_time}"
        )
    except ValueError as error:
        raise RuntimeError(
            "Date and time must use YYYY-MM-DD and HH:MM formats."
        ) from error

    if end == start:
        raise RuntimeError(
            "Start and end times cannot be identical. "
            "Provide a clear bounded activity window."
        )

    if end < start:
        end += timedelta(days=1)

    times = hourly.get("time")

    if not isinstance(times, list):
        raise RuntimeError(
            "Forecast response does not contain hourly times."
        )

    matching_indexes: list[int] = []

    for index, timestamp in enumerate(times):
        forecast_time = datetime.fromisoformat(timestamp)

        if start <= forecast_time < end:
            matching_indexes.append(index)

    if not matching_indexes:
        raise ForecastWindowUnavailableError(
            "Forecast does not cover the requested date and time window."
        )

    extracted: dict[str, list[Any]] = {}

    for field, values in hourly.items():
        if not isinstance(values, list):
            continue

        extracted[field] = [
            values[index]
            for index in matching_indexes
            if index < len(values)
        ]

    return extracted, {
        "start": start.isoformat(timespec="minutes"),
        "end_exclusive": end.isoformat(timespec="minutes"),
    }


def numeric_pairs(
    hourly: dict[str, list[Any]],
    field: str,
) -> list[tuple[str, float]]:
    """Pair valid numeric values with their timestamps."""
    times = hourly.get("time", [])
    values = hourly.get(field, [])

    if not isinstance(times, list) or not isinstance(values, list):
        return []

    pairs: list[tuple[str, float]] = []

    for timestamp, value in zip(times, values):
        if isinstance(value, (int, float)):
            pairs.append((timestamp, float(value)))

    return pairs


def maximum_with_times(
    pairs: list[tuple[str, float]],
) -> tuple[float | None, list[str]]:
    """Return the maximum value and every timestamp sharing it."""
    if not pairs:
        return None, []

    maximum = max(value for _, value in pairs)

    peak_times = [
        timestamp
        for timestamp, value in pairs
        if value == maximum
    ]

    return maximum, peak_times


def minimum_with_times(
    pairs: list[tuple[str, float]],
) -> tuple[float | None, list[str]]:
    """Return the minimum value and every timestamp sharing it."""
    if not pairs:
        return None, []

    minimum = min(value for _, value in pairs)

    worst_times = [
        timestamp
        for timestamp, value in pairs
        if value == minimum
    ]

    return minimum, worst_times


def classify_or_unavailable(
    value: float | None,
    config: dict[str, Any],
    factor_name: str,
) -> str:
    """Classify a numeric value or mark missing data unavailable."""
    if value is None:
        return "unavailable"

    factor_config = config.get(factor_name)

    if not isinstance(factor_config, dict):
        raise RuntimeError(
            f"Missing threshold configuration for {factor_name}."
        )

    levels = factor_config.get("levels")

    if not isinstance(levels, dict):
        raise RuntimeError(
            f"Invalid threshold levels for {factor_name}."
        )

    return classify_value(value, levels)


def summarise_hourly_window(
    hourly: dict[str, list[Any]],
    threshold_config: dict[str, Any],
) -> dict[str, Any]:
    """Convert hourly rows into classified weather summaries."""
    rain_probability_pairs = numeric_pairs(
        hourly,
        "precipitation_probability",
    )
    precipitation_pairs = numeric_pairs(
        hourly,
        "precipitation",
    )
    apparent_temperature_pairs = numeric_pairs(
        hourly,
        "apparent_temperature",
    )
    wind_speed_pairs = numeric_pairs(
        hourly,
        "wind_speed_10m",
    )
    wind_gust_pairs = numeric_pairs(
        hourly,
        "wind_gusts_10m",
    )
    visibility_pairs = numeric_pairs(
        hourly,
        "visibility",
    )

    max_rain_probability, rain_peak_times = maximum_with_times(
        rain_probability_pairs
    )

    max_hourly_precipitation, precipitation_peak_times = (
        maximum_with_times(precipitation_pairs)
    )

    max_apparent_temperature, heat_peak_times = maximum_with_times(
        apparent_temperature_pairs
    )

    max_wind_speed, wind_peak_times = maximum_with_times(
        wind_speed_pairs
    )

    max_wind_gust, gust_peak_times = maximum_with_times(
        wind_gust_pairs
    )

    minimum_visibility, visibility_worst_times = minimum_with_times(
        visibility_pairs
    )

    total_precipitation = (
        round(
            sum(value for _, value in precipitation_pairs),
            2,
        )
        if precipitation_pairs
        else None
    )

    return {
        "sample_count": len(hourly.get("time", [])),
        "rain_probability": {
            "maximum_percent": max_rain_probability,
            "severity": classify_or_unavailable(
                max_rain_probability,
                threshold_config,
                "rain_probability_percent",
            ),
            "peak_times": rain_peak_times,
        },
        "precipitation": {
            "total_mm": total_precipitation,
            "total_severity": classify_or_unavailable(
                total_precipitation,
                threshold_config,
                "precipitation_total_mm",
            ),
            "maximum_hourly_mm": max_hourly_precipitation,
            "peak_times": precipitation_peak_times,
        },
        "apparent_temperature": {
            "maximum_c": max_apparent_temperature,
            "severity": classify_or_unavailable(
                max_apparent_temperature,
                threshold_config,
                "apparent_temperature_c",
            ),
            "peak_times": heat_peak_times,
        },
        "wind": {
            "maximum_speed_kmh": max_wind_speed,
            "speed_severity": classify_or_unavailable(
                max_wind_speed,
                threshold_config,
                "wind_speed_kmh",
            ),
            "speed_peak_times": wind_peak_times,
            "maximum_gust_kmh": max_wind_gust,
            "gust_severity": classify_or_unavailable(
                max_wind_gust,
                threshold_config,
                "wind_gusts_kmh",
            ),
            "gust_peak_times": gust_peak_times,
        },
        "visibility": {
            "minimum_m": minimum_visibility,
            "severity": classify_or_unavailable(
                minimum_visibility,
                threshold_config,
                "visibility_m",
            ),
            "worst_times": visibility_worst_times,
        },
    }


def print_json(data: dict[str, Any]) -> None:
    """Print machine-readable JSON."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve a place and retrieve its hourly forecast."
    )

    parser.add_argument(
        "location",
        help='Place name, such as "Bukit Timah"',
    )

    parser.add_argument(
        "--select",
        type=int,
        choices=(1, 2, 3),
        help="Choose a numbered geocoding candidate.",
    )

    parser.add_argument(
        "--date",
        help="Activity date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--start",
        help="Activity start time in HH:MM format.",
    )

    parser.add_argument(
        "--end",
        help="Activity end time in HH:MM format. End is exclusive.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    window_arguments = [args.date, args.start, args.end]

    if any(window_arguments) and not all(window_arguments):
        print_json(
            {
                "status": "invalid_time_window",
                "message": (
                    "--date, --start, and --end "
                    "must be provided together."
                ),
            }
        )
        return 5

    try:
        threshold_config = load_config(THRESHOLD_CONFIG)
        candidates = geocode(args.location)

        if not candidates:
            print_json(
                {
                    "status": "location_not_found",
                    "query": args.location,
                    "message": "No matching location was found.",
                }
            )
            return 2

        if args.select is None and len(candidates) > 1:
            print_json(
                {
                    "status": "location_ambiguous",
                    "query": args.location,
                    "message": (
                        "Choose one candidate and rerun "
                        "with --select NUMBER."
                    ),
                    "candidates": [
                        {"number": index, **candidate}
                        for index, candidate in enumerate(
                            candidates,
                            start=1,
                        )
                    ],
                }
            )
            return 3

        selected_index = (args.select or 1) - 1

        if selected_index >= len(candidates):
            print_json(
                {
                    "status": "invalid_selection",
                    "query": args.location,
                    "available_candidates": len(candidates),
                }
            )
            return 4

        selected_location = candidates[selected_index]
        forecast = fetch_forecast(selected_location)

        hourly_data = forecast.get("hourly")

        if not isinstance(hourly_data, dict):
            raise RuntimeError(
                "Provider response does not contain hourly data."
            )

        selected_hourly = hourly_data
        resolved_window = None
        window_summary = None

        if all(window_arguments):
            selected_hourly, resolved_window = extract_hourly_window(
                hourly=hourly_data,
                activity_date=args.date,
                start_time=args.start,
                end_time=args.end,
            )

            window_summary = summarise_hourly_window(
                hourly=selected_hourly,
                threshold_config=threshold_config,
            )

        print_json(
            {
                "status": "success",
                "query": args.location,
                "resolved_location": selected_location,
                "forecast": {
                    "latitude": forecast.get("latitude"),
                    "longitude": forecast.get("longitude"),
                    "timezone": forecast.get("timezone"),
                    "timezone_abbreviation": forecast.get(
                        "timezone_abbreviation"
                    ),
                    "utc_offset_seconds": forecast.get(
                        "utc_offset_seconds"
                    ),
                    "hourly_units": forecast.get("hourly_units"),
                    "requested_window": resolved_window,
                    "window_summary": window_summary,
                    "hourly": selected_hourly,
                },
            }
        )
        return 0

    except ForecastWindowUnavailableError as error:
        print_json(
            {
                "status": "forecast_window_unavailable",
                "query": args.location,
                "message": str(error),
            }
        )

    except ConfigurationError as error:
        print_json(
            {
                "status": "configuration_error",
                "query": args.location,
                "message": str(error),
            }
        )

    except RuntimeError as error:
        print_json(
            {
                "status": "processing_error",
                "query": args.location,
                "message": str(error),
            }
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
