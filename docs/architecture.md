# Architecture

## Core Design Principle

> Use deterministic code for facts and consistency; use the LLM for contextual judgment.

The Weather Decision Brief separates responsibilities according to what each component handles reliably.

## Responsibility Split

### LLM

The LLM handles natural-language interpretation, activity mapping, contextual judgment, semantic review, and user-facing communication.

### Python

Python handles geocoding, forecast retrieval, time-window resolution, calculations, severity classification, decision preparation, validation, and explicit errors.

### YAML

YAML stores configurable thresholds, activity profiles, and decision requirements.

## Decision Pipeline

Natural-language request
→ LLM extracts structured inputs
→ Python retrieves and classifies weather evidence
→ Python packages consistent decision context
→ LLM performs contextual judgment
→ Python validates the structured decision
→ LLM checks semantic consistency
→ LLM communicates the result

## Why This Separation Matters

LLMs are useful for ambiguity and contextual trade-offs, but deterministic code is more reliable for calculations, contracts, and repeatable processing.

The same weather condition can lead to different decisions depending on the activity, duration, exposure, timing, shelter, alternatives, and personal constraints.

The weather classification stays deterministic. The practical recommendation requires contextual judgment.
