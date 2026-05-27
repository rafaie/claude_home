---
name: failure-triage
description: This skill should be used when the user says "triage failures", "multiple tests failing", "figure out what's broken", "so many failures I don't know where to start", or when three or more independent failures appear simultaneously and need prioritization before debugging begins.
version: 1.0.0
---

# Failure Triage

Systematically diagnose and prioritize multiple simultaneous failures. Produces a remediation sequence so debugging effort is applied in the right order.

## Step 1: Gather Diagnostic Data

Collect all failure information before attempting any fixes:
- Run the full test suite and capture complete output
- Collect CI logs if available
- Note stack traces, error messages, and exit codes for each failure

## Step 2: Group by Common Root Cause

Look for patterns that suggest shared root causes:
- Same import error in multiple files → likely a missing dependency or broken module
- Same assertion pattern across many tests → likely a shared fixture or constant changed
- All failures in a single directory → likely a scoped change broke that area
- Random failures with no pattern → likely environmental or concurrency issue

Group failures into clusters. A cluster shares an underlying cause even if the error messages differ.

## Step 3: Classify Each Cluster

Assign each cluster to one of these categories:

| Category | Characteristics | Fix order |
|---|---|---|
| Environment | Missing deps, wrong Python version, bad env var | First |
| Dependency | Package version conflict, broken import | Second |
| Shared fixture | Fixture or constant used by many tests changed | Third |
| Reproducible defect | Deterministic logic bug, always fails | Fourth |
| Intermittent | Passes sometimes, timing or concurrency | Last |

## Step 4: Build Remediation Sequence

Create a prioritized list:
1. Fix environment and dependency issues first — these block everything else
2. Fix shared fixtures next — this may resolve many downstream failures
3. Address reproducible defects — use the debug-loop skill for each
4. Address intermittent failures last — use the flaky-test-hunter skill

Document the sequence:

```
## Triage Result

Cluster 1: <description> — category: Environment — fix: <action>
Cluster 2: <description> — category: Shared fixture — fix: <action>
Cluster 3: <description> — category: Reproducible defect — fix: debug-loop
...

Recommended order: 1 → 2 → 3 → ...
```

## Step 5: Execute

Work through the remediation sequence in order. After each fix:
- Re-run the test suite
- Verify the targeted cluster is resolved
- Check whether other clusters are also resolved (shared root causes are common)

## Handoff

Recommend the debug-loop skill for any remaining deterministic failures.
Recommend the flaky-test-hunter skill for any intermittent failures.
