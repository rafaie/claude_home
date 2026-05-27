# Smoke Test Failure Codes

Exit code reference for classifying smoke test failures.

## Startup Failures (1x)

| Exit Code | Category | Typical Cause |
|---|---|---|
| 10 | Import or startup error | Missing dependency, syntax error at import time |
| 11 | Configuration missing | Required config file or env section absent |
| 12 | Credential missing | API key or secret not set in environment |
| 13 | Entry point not found | CLI command or module path doesn't exist |
| 14 | Fixture not found | Test fixture file or directory missing |

## Output Failures (2x)

| Exit Code | Category | Typical Cause |
|---|---|---|
| 20 | Schema validation failure | Response doesn't match expected JSON schema |
| 21 | Output format mismatch | Wrong file type, encoding, or structure |
| 22 | Unexpected output content | Values present but semantically wrong |

## Resource Failures (3x)

| Exit Code | Category | Typical Cause |
|---|---|---|
| 30 | Subprocess timeout | Operation exceeded time budget |
| 31 | Budget exceeded | Token or cost limit hit |
| 32 | Rate limit hit | Too many requests to external service |

## External Failures (4x)

| Exit Code | Category | Typical Cause |
|---|---|---|
| 40 | External API error | Downstream service returned 4xx/5xx |
| 41 | Network unreachable | DNS failure, connection refused, no route |

## Assertion Failures (5x)

| Exit Code | Category | Typical Cause |
|---|---|---|
| 50 | Assertion failure | Expected condition not met |
| 51 | Missing expected artifact | Required output file not created |
| 52 | Extra unexpected artifact | Unexpected file created (side-effect leak) |

## Special Cases

| Exit Code | Category | Typical Cause |
|---|---|---|
| 60 | Flaky — intermittent | Race condition, timing, non-determinism |
| 99 | Unknown error | Unclassified failure — inspect stderr |

## Recommended Next Steps by Category

| Category | Next step |
|---|---|
| 1x startup errors | Fix environment/config, then re-run smoke |
| 2x output errors | Use the debug-loop skill — likely a logic bug |
| 3x resource errors | Check budgets/timeouts in CLAUDE.md; may need offline fallback |
| 4x external errors | Verify credentials and service availability; use offline mode if needed |
| 5x assertion errors | Use the debug-loop skill — acceptance criterion not met |
| Exit 60 flaky | Use the flaky-test-hunter skill |
| Exit 99 | Inspect stderr manually, then use the debug-loop skill |
