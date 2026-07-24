# Weather Decision Brief — Skill Contract v0.1

## Status

- Stage: Day 1 — Contract and Architecture
- Contract version: 0.1
- Implementation status: Not started
- Target runtime: Hermes Agent
- Portable foundation: Agent Skills principles
- Primary forecast provider for V1: Open-Meteo

---

# 1. Purpose

The Weather Decision Brief helps a user decide whether and how to proceed with a planned activity based on forecast weather conditions.

It must not merely repeat forecast data. It should convert forecast information into a practical, transparent recommendation with:

- a verdict;
- the most important weather factors;
- relevant risks;
- recommended adjustments or preparation;
- confidence;
- limitations.

Allowed top-level verdicts:

- `proceed`
- `adjust`
- `postpone`
- `insufficient_information`

---

# 2. When to Use

Use this skill when the user asks whether weather conditions are suitable for a planned activity or how weather should affect that plan.

Typical examples:

- “Should I cycle to work tomorrow at 8 AM?”
- “Can I hike at Bukit Timah tomorrow from 8–11 AM?”
- “Is it too hot to run at 2 PM?”
- “Will rain affect my commute?”
- “Can I hold an outdoor event this evening?”
- “What time today is best for this outdoor activity?”

The skill may also be used when the user asks for weather-dependent timing, preparation, modification, or postponement advice.

---

# 3. Do Not Use For

Do not use this skill for:

- a general weather report with no decision or activity;
- historical weather analysis;
- professional meteorological forecasting;
- emergency or safety guarantees;
- medical advice about heat, cold, exertion, or fitness;
- route navigation;
- route shelter analysis;
- indoor/outdoor route detection;
- automatic GPS extraction;
- live public transport;
- flood-route planning;
- radar or lightning-provider analysis;
- terrain-aware route safety;
- trail-condition claims without a reliable source;
- climate-outlook verdicts beyond the forecast horizon.

The skill may explain that a request is outside V1 scope and suggest the smallest appropriate next step.

---

# 4. Officially Supported V1 Profiles

V1 officially supports:

1. commuting;
2. hiking;
3. running;
4. cycling;
5. outdoor events.

A profile counts as supported only when it has:

- defined required inputs;
- relevant weather factors;
- structured thresholds;
- edge cases;
- passing tests.

For other activities, the skill may produce a best-effort assessment using general weather reasoning.

Unsupported activities must be labelled:

`activity_profile_status: best_effort`

The skill must not imply that a best-effort activity has been tested to the same standard as an official profile.

---

# 5. Required Inputs

The skill requires:

- activity;
- location;
- date;
- specific time or bounded time window.

## 5.1 Activity

The skill should identify the activity from the request, map it to a supported profile where appropriate, and otherwise use the best-effort fallback.

If the activity is genuinely unclear, ask one concise clarification question.

## 5.2 Location

Location may be supplied as:

- a human-readable place name; or
- latitude and longitude coordinates.

Location priority:

1. location supplied in the current request;
2. configured default location;
3. clarification from the user.

Never silently guess the user’s location.

### Ambiguous place names

When geocoding returns multiple credible matches:

1. show up to three plausible options;
2. include country or region;
3. ask the user to choose;
4. do not retrieve weather or issue a verdict until resolved.

A configured country or region may rank the options, but must not silently select one.

### Coordinates

When coordinates are supplied:

1. preserve the original coordinates in structured output;
2. attempt reverse geocoding for a readable display name;
3. continue using the coordinates if reverse geocoding fails.

## 5.3 Date and time

Vague periods such as “tomorrow morning” are insufficient for a weather decision.

The skill must ask for a more specific time or bounded time window.

If no timezone is supplied:

1. infer it from the resolved location;
2. show the inferred timezone clearly;
3. ask for confirmation only when the location spans multiple timezones or inference is uncertain.

### Cross-midnight windows

Cross-midnight time windows are supported. The resolved dates must be displayed explicitly.

---

# 6. Optional Inputs

Optional information may include:

- duration;
- experience level;
- timing flexibility;
- rain tolerance;
- heat sensitivity;
- available equipment;
- indoor or outdoor context;
- exposed or sheltered context;
- whether the activity can be shortened, delayed, or moved indoors.

Do not request every optional field by default.

If optional personal constraints are absent, proceed using a general-user baseline and clearly state that the result did not account for individual fitness, experience, equipment, or tolerance.

---

# 7. Forecast Horizon

For requests within the provider’s supported forecast horizon, perform the normal assessment.

For requests beyond the reliable forecast horizon:

1. accept the request;
2. return `insufficient_information`;
3. explain that a trustworthy day-specific forecast is not yet available;
4. suggest checking again closer to the date.

V1 must not substitute climate averages for a day-specific forecast verdict.

---

# 8. Weather Data

Use one primary forecast provider for V1.

Initial provider: Open-Meteo.

Retrieve only the forecast period relevant to the planned activity.

Potential variables include:

- precipitation probability;
- precipitation amount;
- temperature;
- apparent temperature;
- humidity;
- wind speed;
- wind gusts;
- weather condition codes;
- thunderstorm indicators where available;
- visibility where available;
- forecast timestamp;
- data freshness.

Do not invent unavailable values.

NParks, live transport, map shelter data, and other regional context providers are outside V1.

---

# 9. Decision Architecture

The decision flow is:

User request
→ resolve required inputs
→ retrieve and validate forecast data
→ select supported profile or best-effort fallback
→ classify each relevant weather factor
→ produce a combined evidence summary
→ LLM makes contextual verdict
→ validate structured output
→ generate matching human-readable brief

## 9.1 Deterministic factor classification

The deterministic layer should classify relevant factors using descriptive levels such as:

- `low`
- `moderate`
- `high`
- `severe`
- `unavailable`

Do not create a fake precise score such as `72/100`.

## 9.2 Combined judgement

Do not automatically choose the most severe individual factor as the final verdict in every case.

Instead:

1. calculate factor-level severity deterministically;
2. provide a combined evidence summary;
3. let the LLM weigh the combined conditions against activity sensitivity, timing, exposure, possible adjustments, and optional user constraints;
4. select one allowed verdict.

## 9.3 Hard safety overrides

Clearly defined hard-stop conditions or active severe official warnings may override ordinary combined reasoning.

These overrides must be explicit, testable, and not improvised by the LLM.

---

# 10. Verdict Definitions

## `proceed`

Use when conditions are generally suitable and no meaningful change is required.

## `adjust`

Use when the activity remains reasonable but one or more changes are advisable.

## `postpone`

Use when combined conditions make the plan substantially impractical or risky and realistic adjustments are insufficient.

## `insufficient_information`

Use when a reliable assessment cannot be made.

Never force another verdict when evidence is inadequate.

---

# 11. Confidence

Confidence must be derived partly from deterministic evidence.

Relevant factors include:

- forecast distance from the present;
- data completeness;
- data freshness;
- location precision;
- whether the profile is supported or best-effort;
- whether official alert coverage is available;
- unresolved limitations.

Allowed values:

- `high`
- `medium`
- `low`

The LLM may explain the confidence level, but must not independently override it.

---

# 12. Official Weather Alerts

Official alert integrations are optional by region.

When a supported official alert source is available, retrieve and surface relevant active alerts and allow explicitly defined severe alerts to override normal logic.

When no official alert source is available:

- continue with the normal forecast assessment;
- disclose that official-alert coverage was unavailable;
- do not imply that no warning exists.

---

# 13. Structured Output

The skill must first produce machine-checkable structured output containing at least:

```json
{
  "verdict": "proceed | adjust | postpone | insufficient_information",
  "activity": "string",
  "activity_profile_status": "supported | best_effort",
  "location": {
    "display_name": "string | null",
    "latitude": "number | null",
    "longitude": "number | null",
    "source": "user_place | user_coordinates | configured_default",
    "timezone": "IANA timezone"
  },
  "time_window": {
    "start": "ISO-8601 datetime",
    "end": "ISO-8601 datetime"
  },
  "weather_factors": [
    {
      "factor": "string",
      "value": "number|string|null",
      "unit": "string|null",
      "severity": "low | moderate | high | severe | unavailable"
    }
  ],
  "combined_evidence": "string",
  "key_risks": [],
  "recommended_actions": [],
  "alternative_timing": null,
  "confidence": "high | medium | low",
  "forecast_source": "string",
  "official_alert_coverage": "available | unavailable | not_checked",
  "limitations": []
}
```

Allowed verdicts are fixed for V1 unless the contract is deliberately versioned.

---

# 14. Human-Readable Brief

After the structured output is validated, produce a concise brief containing:

- verdict;
- one-sentence recommendation;
- most important weather factors;
- practical actions;
- alternative timing when useful;
- confidence or limitation.

Avoid overwhelming the user with every available metric.

## 14.1 Source of truth

The validated structured output is authoritative.

If the human-readable brief conflicts with the structured output:

1. treat the response as invalid;
2. do not show the contradictory result;
3. regenerate or repair the brief;
4. validate again.

---

# 15. LLM Responsibilities

Use LLM judgement for:

- interpreting activity and intent;
- choosing the closest supported profile;
- identifying relevant factors for unsupported activities;
- weighing combined weather evidence against activity context;
- deciding which risks matter most;
- asking concise clarification questions;
- explaining trade-offs and uncertainty;
- generating the final brief.

The LLM must not override deterministic validation failures.

---

# 16. Deterministic Responsibilities

Use structured configuration and code for:

- required-field validation;
- location format validation;
- geocoding result handling;
- date and time validation;
- timezone handling;
- cross-midnight resolution;
- forecast-horizon checks;
- weather API retrieval;
- provider failure detection;
- data freshness and completeness checks;
- profile thresholds;
- factor-level severity;
- allowed verdict validation;
- confidence inputs;
- output-schema validation;
- contradiction detection between structured output and brief.

Design rule:

> Documentation explains the rule. Configuration stores changeable values. Code enforces deterministic checks.

---

# 17. Safety and Honesty Rules

- Do not guarantee safety.
- Do not claim professional meteorological accuracy.
- Do not fabricate missing data.
- Do not hide low confidence.
- Do not infer medical fitness or personal capability.
- Do not claim trail conditions without a reliable source.
- Do not treat missing official-alert coverage as proof that no alert exists.
- Do not present a best-effort activity as fully supported.
- Clearly separate forecast facts from recommendations.
- Prefer `insufficient_information` over a misleading verdict.

---

# 18. Success Criteria

A request is successfully handled when:

- the correct activity profile or fallback is selected;
- location is resolved without silent guessing;
- date, time window, and timezone are valid;
- forecast data covers the relevant period;
- factor severity follows configured rules;
- the LLM considers combined evidence rather than one isolated factor;
- the verdict uses an allowed value;
- confidence is evidence-based;
- structured output passes validation;
- the brief matches the structured result;
- uncertainty and limitations are disclosed;
- unsupported facts are not invented.

---

# 19. Failure Behaviour

When the skill cannot complete a reliable assessment:

1. state what failed;
2. state what information or dependency is missing;
3. return `insufficient_information`;
4. suggest the smallest next action needed to continue.

---

# 20. V1 Exclusions and Future Possibilities

Not part of V1:

- climate-planning outlooks;
- NParks park or trail context;
- shelter-aware routing;
- indoor/outdoor path analysis;
- automatic device location;
- live public transport;
- multiple weather models;
- radar and lightning providers;
- global official-alert integrations;
- terrain-aware route risk.

These may be considered only after V1 is complete and tested.
