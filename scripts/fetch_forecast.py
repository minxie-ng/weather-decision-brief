#!/usr/bin/env python3
"""Resolve a place name and retrieve hourly weather from Open-Meteo."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

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
        raise RuntimeError(f"Could not reach provider: {error.reason}") from error
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


def print_json(data: dict[str, Any]) -> None:
    """Print machine-readable JSON."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve a place and retrieve its hourly forecast."
    )
    parser.add_argument("location", help='Place name, such as "Bukit Timah"')
    parser.add_argument(
        "--select",
        type=int,
        choices=(1, 2, 3),
        help="Choose a numbered geocoding candidate.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    try:
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
                    "message": "Choose one candidate and rerun with --select NUMBER.",
                    "candidates": [
                        {"number": index, **candidate}
                        for index, candidate in enumerate(candidates, start=1)
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

        print_json(
            {
                "status": "success",
                "query": args.location,
                "resolved_location": selected_location,
                "forecast": {
                    "latitude": forecast.get("latitude"),
                    "longitude": forecast.get("longitude"),
                    "timezone": forecast.get("timezone"),
                    "timezone_abbreviation": forecast.get("timezone_abbreviation"),
                    "utc_offset_seconds": forecast.get("utc_offset_seconds"),
                    "hourly_units": forecast.get("hourly_units"),
                    "hourly": forecast.get("hourly"),
                },
            }
        )
        return 0

    except RuntimeError as error:
        print_json(
            {
                "status": "provider_error",
                "query": args.location,
                "message": str(error),
            }
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
