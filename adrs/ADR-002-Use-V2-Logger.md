# ADR-002: Use V2 Logging Wrapper

## Context
Our old `console.log` approach creates messy Splunk logs.

## Decision
All logs must use the `LogManager.info()` or `LogManager.error()` wrapper.
Do not use `print()` or `console.log()`.

## Consequences
Pull requests introducing standard print statements will be flagged.