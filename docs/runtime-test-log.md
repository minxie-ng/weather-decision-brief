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
