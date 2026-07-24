---

name: weather-decision-brief
description: Use when a user needs to decide whether or how to proceed with a planned activity based on forecast weather, including commuting, hiking, running, cycling, and outdoor events. Produces a proceed, adjust, postpone, or insufficient-information recommendation. Do not use for general weather reports without a decision.
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Weather Decision Brief

## Overview

The `weather-decision-brief` skill helps users decide whether and how to proceed with a planned activity at a specific location and time.

It retrieves relevant forecast data and evaluates weather factors against the activity’s needs and any personal constraints the user provides.

Instead of only summarising the weather, it returns a practical `proceed`, `adjust`, `postpone`, or `insufficient_information` recommendation with reasons and suggested actions.

The first working version supports commuting and hiking.

## When to Use

Use this skill when the user is asking for a decision about a planned activity based on upcoming weather.

Examples:

* Should I hike at Bukit Timah tomorrow?
* Is it safe to cycle to work this evening?
* Should we postpone our outdoor event?
* Can I commute without bringing rain protection?

Do not use this skill when the user only wants a general weather report without an activity decision.

## Required Inputs

Before retrieving forecast data, resolve:

1. Activity
2. Location
3. Date
4. Bounded start and end time

Personal constraints are optional. Examples include:

* injury or limited mobility;
* sensitivity to heat or cold;
* low fitness or endurance;
* limited access to shelter;
* equipment constraints.

When no personal constraints are provided, assess the request using a general-user baseline and state that assumption.

## Input Resolution

Use the location supplied in the current request.

When no location is supplied:

1. Use an explicitly configured default location and disclose that it was used.
2. Otherwise, ask the user for the location.

Do not silently infer or guess the user’s location.

When the user gives a vague period such as morning, afternoon, or evening without a bounded time window, ask for the intended start and end time.

Resolve all required inputs before retrieving forecast data.

## Forecast Retrieval

Use `scripts/fetch_forecast.py` to resolve a place name and retrieve hourly forecast data from Open-Meteo.

Example:

```bash
python3 scripts/fetch_forecast.py "Singapore"

## Procedure

1. Identify the activity, location, date, and bounded time window.
2. Ask only for required information that is missing or ambiguous.
3. Identify any optional personal constraints supplied by the user.
4. Retrieve forecast data for the resolved location and time window.
5. Confirm that the forecast data covers the requested period.
6. Evaluate the relevant weather conditions for the activity.
7. Return one verdict:

   * `proceed`
   * `adjust`
   * `postpone`
   * `insufficient_information`
8. Explain the main reasons for the verdict.
9. Provide practical suggested actions.
10. State relevant assumptions, missing alert coverage, or forecast limitations.

## Activity Profiles

### Commuting

Consider:

* precipitation;
* thunderstorms;
* temperature and heat exposure;
* strong wind;
* visibility;
* duration of outdoor exposure;
* access to shelter or alternative transport.

### Hiking

Consider:

* precipitation before and during the activity;
* thunderstorms and lightning;
* heat and humidity;
* wind;
* visibility;
* trail surface risks;
* duration and exposure;
* personal mobility or fitness constraints when provided.

## Output Format

Return:

* activity;
* resolved location;
* resolved date and time window;
* timezone;
* verdict;
* main weather factors;
* reasoning;
* suggested actions;
* assumptions and limitations.

The recommendation must be practical and should not merely repeat the forecast.

## Failure Behaviour

Return `insufficient_information` when:

* required inputs remain unresolved;
* the requested period is outside the available forecast horizon;
* the provider response is unavailable or invalid;
* the forecast does not cover the requested time window;
* there is not enough reliable information to make a responsible recommendation.

Do not invent missing weather data.

## Boundaries

The first working version supports commuting and hiking.

Running, cycling, and outdoor events remain part of the intended V1 scope but are not yet implemented in this version.

Do not provide medical clearance or guarantee safety.

Do not claim that official weather alerts were checked when alert coverage was unavailable.

