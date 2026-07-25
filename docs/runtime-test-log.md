# Runtime Test Log

## Test 1 — Natural Routing: Hiking Decision

**Date:** 25 July 2026
**Runtime:** Hermes Agent via Telegram
**Skill:** Weather Decision Brief
**Prompt:**

> I plan to hike at MacRitchie Reservoir tomorrow from 8:00 AM to 11:00 AM. Should I go, and what weather risks should I prepare for?

### Result

* Hermes produced a clear **Adjust** verdict.
* It correctly identified the hiking activity, location, date and time window.
* It gave actionable risks and mitigations.
* The response was useful but overly verbose and repetitive.
* Response time was approximately 3–4 minutes, which is too slow for routine conversational use.
* The answer referenced NEA data in addition to Open-Meteo.
* It is not yet confirmed whether Hermes invoked the installed skill or independently browsed and reasoned about the request.

### Status

**Partial pass**

* Decision usefulness: Pass
* Natural routing: Pass — Hermes opened weather-decision-brief and executed its scripts.
* Response format: Needs improvement
* Latency: Fail
* V1 data-source fidelity: Needs investigation

### Trace Evidence

The Telegram execution trace confirmed that Hermes:

- opened `weather-decision-brief`;
- executed `fetch_forecast.py`;
- read `decision-schema.yaml`;
- wrote a decision JSON file;
- executed `validate_decision.py`.

Hermes also performed additional NEA web research and repeated forecast retrieval, which likely contributed to the 3–4 minute latency.

### Next Investigation

Determine why Hermes repeated forecast retrieval and whether the additional NEA web search should be prevented or explicitly allowed by the skill instructions.

## Test 2 — Negative Routing: General Weather Query

**Date:** 25 July 2026
**Runtime:** Hermes Agent via Telegram
**Prompt:**

> What will the weather be like in Singapore tomorrow?

### Result

- Hermes answered with a general weather forecast.
- Hermes did not open `weather-decision-brief`.
- No skill scripts were executed.
- No activity verdict was forced.
- Hermes used normal web research instead.

### Status

**Pass**

- Negative routing: Pass
- Trigger precision: Pass
- False activation: Not observed

## Test 3 Attempt 1 — Missing Information

**Status:** Invalid test

Hermes reused the previous MacRitchie location and 8:00–11:00 AM time window from conversation history. The prompt was therefore not evaluated as a genuinely incomplete request.

## Test 3 — Missing Required Information

**Date:** 25 July 2026
**Runtime:** Hermes Agent via Telegram
**Prompt:**

> Should I go hiking tomorrow?

### Result

- Hermes opened `weather-decision-brief`.
- It identified that location and time window were missing.
- It asked for both required details.
- It did not run the full forecast and decision pipeline prematurely.
- The phrase “Probably” was slightly premature before sufficient information was available.
- Hermes suggested Hangzhou based on user context; this may be helpful personally but should not become a general default.

### Status

**Pass**

- Skill routing: Pass
- Missing-field detection: Pass
- Clarification behaviour: Pass
- Premature assumptions: Minor style issue

## Test 4 Retest — Unsupported Activity: Kayaking

### Result

- Hermes activated `weather-decision-brief`.
- It described the result as a weather-only assessment.
- It disclosed missing tides, waves, currents, marine warnings, lightning alerts, and operator restrictions.
- It advised checking the kayak operator.
- It did not assign high confidence.
- However, the unsupported V1 status was not stated near the beginning of the response.
- The limitation appeared only at the end.
- The trace still showed repeated forecast retrieval.

### Status

**Partial pass**

- Unsupported-profile recognition: Pass
- Missing-factor disclosure: Pass
- Confidence calibration: Pass
- Operator guidance: Pass
- Early disclosure placement: Needs improvement
- Latency and repeated retrieval: Fail

## Test 5 — Supported Activity: Cycling

**Date:** 25 July 2026
**Runtime:** Hermes Agent via Telegram
**Prompt:**

> I want to cycle from Bishan to Marina Bay tomorrow from 7:00 AM to 8:00 AM. Should I go?

### Result

- Hermes activated the weather decision workflow.
- It retrieved forecasts for both Bishan and Marina Bay.
- The two forecast calls were justified because the request involved an origin and destination.
- It generated and validated a structured decision.
- It returned an actionable `Adjust` verdict.
- The advice was relevant to cycling, including wet-road risk, braking distance, visibility gear and transport fallback.
- Response time was approximately one minute.
- The recommendation was repeated slightly in the opening and conclusion.

### Status

**Pass**

- Supported-profile routing: Pass
- Cycling-profile relevance: Pass
- Multi-location handling: Pass
- Structural validation: Pass
- Response style: Pass with minor repetition
- Latency: Acceptable, but still worth improving

## Test 6 — Ambiguous Location

**Date:** 25 July 2026
**Runtime:** Hermes Agent via Telegram
**Prompt:**

> I want to run in Springfield tomorrow from 6:00 AM to 7:00 AM. Should I go?

### Result

- Hermes detected that “Springfield” referred to multiple possible locations.
- It presented several likely matches.
- It asked the user to clarify before retrieving forecast data.
- It did not silently select a location or generate a premature verdict.
- Quick-reply buttons improved the clarification experience.

### Status

**Pass**

- Ambiguity detection: Pass
- Clarification behaviour: Pass
- Premature forecast retrieval: Not observed
- User experience: Strong
