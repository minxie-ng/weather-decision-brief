# Live Hermes Test Script

## Purpose

Demonstrate that Weather Decision Brief can be installed, discovered, invoked, and tested reproducibly in Hermes Agent.

The demo should prove:

- natural activation for an activity decision;
- no activation for a general weather query;
- clarification of missing or ambiguous inputs;
- correct handling of a supported activity;
- clear best-effort limitations for an unsupported activity;
- structured decision validation;
- practical, concise user-facing output.

## Demo Setup

- Runtime: Hermes Agent via Telegram
- Installed skill path: `~/.hermes/skills/weather-decision-brief`
- Release: `v1.0.0`
- Primary forecast provider: Open-Meteo
- Expected duration: 5–8 minutes

## Test 1 — Natural Skill Activation

### Prompt

> I plan to hike at MacRitchie Reservoir tomorrow from 8:00 AM to 11:00 AM. Should I go, and what weather risks should I prepare for?

### Expected Behaviour

- Hermes opens `weather-decision-brief`.
- It resolves the activity, location, date, and bounded time window.
- It retrieves forecast data.
- It produces and validates a structured decision.
- It returns a practical `proceed`, `adjust`, `postpone`, or `insufficient_information` verdict.
- The final answer includes the main risks, suggested actions, assumptions, and material limitations.

### Evidence to Show

- `skill_view: "weather-decision-brief"` in the process trace;
- execution of the forecast and validation scripts;
- the final user-facing decision brief.

### Pass Criteria

The skill activates naturally without the user explicitly naming it, and the final recommendation is consistent with the validated decision.

## Test 2 — Negative Routing

### Prompt

> What will the weather be like in Singapore tomorrow?

### Expected Behaviour

- Hermes gives a normal weather forecast.
- It does not open `weather-decision-brief`.
- It does not run the decision-validation pipeline.
- It does not force a `proceed`, `adjust`, `postpone`, or `insufficient_information` verdict.

### Evidence to Show

- no `skill_view: "weather-decision-brief"` in the process trace;
- no execution of the skill’s decision scripts;
- a normal forecast-style response.

### Pass Criteria

The skill does not activate for a general weather query without an activity decision.

## Test 3 — Missing Required Inputs

### Prompt

> Should I go hiking tomorrow?

### Expected Behaviour

- Hermes opens `weather-decision-brief`.
- It identifies that the location and bounded time window are missing.
- It asks concise clarification questions.
- It does not silently infer the missing details.
- It does not retrieve forecast data or generate a verdict prematurely.

### Evidence to Show

- `skill_view: "weather-decision-brief"` in the process trace;
- clarification questions for location and time;
- no forecast or validation-script execution before clarification.

### Pass Criteria

Hermes requests the required missing information instead of guessing or reusing unrelated context.

---

## Test 4 — Ambiguous Location

### Prompt

> I want to run in Springfield tomorrow from 6:00 AM to 7:00 AM. Should I go?

### Expected Behaviour

- Hermes recognises that Springfield may refer to multiple locations.
- It presents plausible matches or asks for the state or country.
- It does not select a location silently.
- It does not generate a weather decision before resolving the ambiguity.

### Evidence to Show

- multiple location options or a clarification question;
- no premature final verdict;
- no complete decision pipeline before the location is resolved.

### Pass Criteria

The agent detects the ambiguity and waits for user clarification.

---

## Test 5 — Supported Activity Profile

### Prompt

> I want to cycle from Bishan to Marina Bay tomorrow from 7:00 AM to 8:00 AM. Should I go?

### Expected Behaviour

- Hermes activates `weather-decision-brief`.
- It uses the supported cycling profile.
- It may retrieve forecasts for both the origin and destination because they represent distinct route locations.
- It evaluates relevant cycling factors such as rain, wind, visibility, heat, and wet-road risk.
- It produces and validates a structured decision.
- It returns concise, cycling-specific actions.

### Evidence to Show

- activation of `weather-decision-brief`;
- forecast calls for relevant route locations;
- execution of `validate_decision.py`;
- cycling-specific reasoning and actions.

### Pass Criteria

The response is relevant to cycling, supported by the retrieved evidence, and consistent with the validated decision.

---

## Test 6 — Unsupported Activity Fallback

### Prompt

> I want to go kayaking at Sentosa tomorrow from 9:00 AM to 11:00 AM. Should I go?

### Expected Behaviour

- Hermes activates `weather-decision-brief`.
- It uses `profile_support: best_effort`.
- It uses the `general_outdoor` fallback rather than pretending kayaking has a dedicated V1 profile.
- It states near the beginning that this is a limited weather-only assessment.
- It names missing marine factors such as tides, waves, currents, marine warnings, and operator restrictions.
- It does not assign high confidence.
- It advises checking official marine information or the activity operator.

### Evidence to Show

- `best_effort` and `general_outdoor` in the structured decision;
- explicit unsupported-profile disclosure;
- missing marine factors listed;
- reduced confidence;
- operator or official-source guidance.

### Pass Criteria

The agent clearly limits the strength of its recommendation and does not present weather data as a complete kayaking-safety assessment.

---

## Validation Evidence

During at least one supported-activity test, show that Hermes:

1. creates a structured decision JSON;
2. follows `config/decision-schema.yaml`;
3. runs:

```bash
python3 scripts/validate_decision.py PATH_TO_DECISION_JSON
```

4. receives a successful validation result;
5. produces a user-facing brief consistent with that decision.

## Demo Closing

Conclude the demo with:

> Weather Decision Brief separates deterministic weather processing from contextual agent judgement. Python handles retrieval, classification, preparation, and structural validation, while the language model interprets the user’s activity context and explains the recommendation. Runtime tests also verify routing, clarification, supported profiles, fallback behaviour, and safety limitations.

## Known Limitations to Disclose

- Forecasts cannot guarantee safety.
- Open-Meteo is the configured V1 weather provider.
- Official alerts are not checked unless explicitly retrieved and disclosed.
- Unsupported activities receive only a best-effort general outdoor assessment.
- Marine conditions such as tides, waves, and currents are outside V1.
- Agent-runtime latency may vary.
- Compatibility has been verified with Hermes Agent but not yet with other runtimes.