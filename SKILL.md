---
name: weather-decision-brief
description: Use when a user needs to decide whether or how to proceed with a planned activity based on forecast weather, including commuting, hiking, running, cycling, and outdoor events. Produces a proceed, adjust, postpone, or insufficient_information recommendation. Do not use for general weather reports without a decision.
---

# Weather Decision Brief

## Overview

The `weather-decision-brief` skill helps users decide whether and how to proceed with a planned outdoor activity at a specific location and time.

It retrieves forecast data, applies deterministic weather classification, evaluates the result against an activity profile and any personal constraints, validates a structured decision, and then produces a practical user-facing brief.

The V1 skill supports:

- commuting;
- hiking;
- running;
- cycling;
- outdoor events.

Unsupported activities use a reduced-confidence `general_outdoor` fallback.

## When to Use

Use this skill when the user is asking for a weather-based decision about a planned activity.

Examples:

- Should I hike at Bukit Timah tomorrow morning?
- Is it sensible to cycle to work this evening?
- Should we postpone our outdoor event?
- Can I commute without rain protection?

Do not use this skill when the user only wants a general weather report without an activity decision.

## Required Inputs

Before retrieving forecast data, resolve:

1. activity;
2. location;
3. date;
4. bounded start and end time.

Personal constraints are optional. Examples include:

- injury or limited mobility;
- sensitivity to heat or cold;
- low fitness or endurance;
- limited access to shelter;
- equipment constraints.

When no personal constraints are provided, use a general-user baseline and state that assumption.

## Input Resolution

Use the location supplied in the current request.

When no location is supplied:

1. use an explicitly configured default location and disclose it; or
2. ask the user for the location.

Do not silently infer or guess the user’s location.

When the user gives a vague period such as morning, afternoon, or evening without a bounded time window, ask for the intended start and end time.

Resolve all required inputs before retrieving forecast data.

## Dependency Handling

This skill requires the packages listed in `requirements.txt`.

If a required Python package is missing:

1. explain which dependency is missing;
2. show the exact installation command;
3. ask for explicit permission before installing anything;
4. if permission is granted, run:

```bash
python3 -m pip install -r requirements.txt
```

5. retry the failed step once.

Never install dependencies silently.

## Forecast Retrieval

Use `scripts/fetch_forecast.py` to resolve the location and retrieve hourly forecast data from Open-Meteo.

Example:

```bash
python3 scripts/fetch_forecast.py "Singapore" "2026-07-26" "08:00" "11:00"
```

Handle these statuses explicitly:

- `success`;
- `location_ambiguous`;
- `location_not_found`;
- `invalid_selection`;
- `invalid_time_window`;
- `forecast_window_unavailable`;
- `processing_error`;
- `configuration_error`.

Do not repeatedly retrieve the same forecast unless the earlier result failed or the resolved inputs changed.

Do not perform additional web research or introduce another forecast provider unless required information is unavailable from the configured V1 pipeline. Any supplementary source must be clearly disclosed and must not be presented as part of the deterministic Open-Meteo result.

## Procedure

1. Identify the activity, location, date, and bounded time window.
2. Ask only for required information that is missing or ambiguous.
3. Identify any optional personal constraints supplied by the user.
4. Retrieve forecast data once for the resolved location and time window.
5. Confirm that the forecast data covers the requested period.
6. Run deterministic weather classification.
7. Prepare the stable decision-input package.
8. Generate one structured decision using the activity profile and supplied context.
9. Return one verdict:
   - `proceed`;
   - `adjust`;
   - `postpone`;
   - `insufficient_information`.
10. Validate the structured decision.
11. Perform a semantic-consistency review.
12. Produce the user-facing brief.

## Activity Profiles

### Commuting

Consider:

- precipitation;
- thunderstorms;
- temperature and heat exposure;
- strong wind;
- visibility;
- duration of outdoor exposure;
- access to shelter or alternative transport.

### Hiking

Consider:

- precipitation before and during the activity;
- thunderstorms and lightning;
- heat and humidity;
- wind;
- visibility;
- trail-surface risks;
- duration and exposure;
- personal mobility or fitness constraints when provided.

### Running

Consider:

- precipitation;
- thunderstorms and lightning;
- heat and apparent temperature;
- humidity;
- wind;
- visibility;
- planned intensity and duration;
- personal heat tolerance or fitness constraints when provided.

### Cycling

Consider:

- precipitation;
- thunderstorms and lightning;
- wind and gusts;
- visibility;
- wet-road or surface risk;
- heat exposure;
- trip duration;
- access to an alternative route or transport.

### Outdoor Events

Consider:

- precipitation timing and duration;
- thunderstorms and lightning;
- wind and gusts;
- heat exposure;
- visibility;
- shelter availability;
- setup and teardown exposure;
- crowd or equipment sensitivity.

## Decision Generation and Validation

Use the prepared decision-input package to produce a structured decision before writing any human-readable brief.

The structured decision must follow `config/decision-schema.yaml` and contain:

- activity;
- profile support and activity profile;
- resolved location, timezone, date, and time window;
- verdict;
- confidence;
- key factors;
- reasoning;
- suggested actions;
- assumptions;
- limitations.

Use only these verdicts:

- `proceed`;
- `adjust`;
- `postpone`;
- `insufficient_information`.

Do not change deterministic weather severities supplied in the decision-input package.

Combine the following contextually:

- classified weather evidence;
- factor timing and duration;
- activity-profile guidance;
- exposure level;
- personal constraints;
- assumptions and limitations.

Only explicitly configured hard-stop conditions may automatically override the contextual decision.

After producing the structured JSON, validate it with:

```bash
python3 scripts/validate_decision.py PATH_TO_DECISION_JSON
```

## Unsupported Activity Behaviour

Unsupported activities must use:

- `profile_support: best_effort`;
- `activity_profile: general_outdoor`;
- reduced confidence.

When `profile_support` is `best_effort`:

- explicitly state near the beginning of the final brief that the activity is not supported by a dedicated V1 profile;
- describe the recommendation as a limited weather-only assessment, not a complete activity-safety decision;
- name any material missing factors relevant to the activity, such as tides, waves, currents, route conditions, or operator restrictions;
- do not imply that missing factors were checked;
- do not assign `high` confidence;
- advise the user to consult the relevant official source, venue, or operator before proceeding.

For marine or water activities such as kayaking, weather data alone is insufficient for a complete go/no-go decision. Clearly state that tides, waves, currents, marine warnings, and operator restrictions are outside the V1 pipeline.

Omitting the unsupported-profile disclosure is a material limitation and makes the final brief invalid.

## Semantic Consistency Review

After structural validation succeeds, review the decision for semantic consistency before producing the user-facing brief.

Check that:

- the verdict is supported by the key factors and reasoning;
- the reasoning does not contradict deterministic severities;
- suggested actions are appropriate for the verdict;
- assumptions and limitations are not presented as verified facts;
- unsupported profiles do not receive unjustifiably high confidence;
- a `best_effort` decision includes the required unsupported-profile disclosure;
- the brief does not introduce conclusions absent from the structured decision.

If a contradiction is found, revise the structured decision and run structural validation again.

Structural validity does not guarantee semantic consistency.

## Human-Readable Brief

Generate the user-facing brief only after the structured decision passes validation.

Keep the brief concise and decision-oriented.

Use this order:

1. verdict;
2. one-sentence recommendation;
3. two to four main reasons;
4. practical actions;
5. material assumptions and limitations.

Avoid repeating the same recommendation across multiple sections.

The brief must:

- begin with the validated verdict;
- summarise the most important reasoning;
- include the suggested actions;
- state material assumptions and limitations;
- remain consistent with the structured decision.

Do not introduce new weather facts, severities, actions, sources, or conclusions that are absent from the validated structured decision.

If the brief contradicts the structured verdict or omits a material limitation, treat the output as invalid and repair it.

## Output Format

Return:

- activity;
- resolved location;
- resolved date and time window;
- timezone;
- verdict;
- confidence;
- main weather factors;
- reasoning;
- suggested actions;
- assumptions and limitations.

The recommendation must be practical and should not merely repeat the forecast.

## Failure Behaviour

Return `insufficient_information` when:

- required inputs remain unresolved;
- the requested period is outside the available forecast horizon;
- the provider response is unavailable or invalid;
- the forecast does not cover the requested time window;
- there is not enough reliable information to make a responsible recommendation.

Do not invent missing weather data.

## Boundaries

The V1 skill supports commuting, hiking, running, cycling, and outdoor events.

Unsupported activities use the `general_outdoor` fallback profile with reduced confidence and mandatory limitation disclosure.

Do not provide medical clearance or guarantee safety.

Do not claim that official alerts, marine conditions, venue restrictions, route conditions, tides, waves, or currents were checked when they were not.

Do not expand the V1 activity scope or add new data providers without an explicit design decision.
