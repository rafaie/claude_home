# {{STORY_ID}} — {{TITLE}}

**Epic:** {{EPIC_ID or none}} · **Area:** {{area}} · **Priority:** {{P1 | P2 | P3}} · **Depends on:** {{story IDs or none}}

## Story
As a {{who}}, I want {{what}}, so that {{why}}.

## Acceptance Criteria
- [ ] **AC-1** — Given {{context}}, when {{action}}, then {{observable outcome}}.

## Definition of Ready
- [ ] Story statement names who benefits and the observable outcome
- [ ] Every AC has an ID and a Given/When/Then that can be tested automatically
- [ ] At least one AC covers an error path or boundary
- [ ] Dependencies are Done or explicitly non-blocking
- [ ] Out of scope is listed
- [ ] No open question blocks implementation
- [ ] Fits one focused session (2–6 ACs, ≤ ~5 tasks)

## Definition of Done
- [ ] All ACs pass in automated tests that reference their AC IDs
- [ ] Full checks pass (format, lint, types, tests)
- [ ] Smoke test passes with artifacts
- [ ] Independent review gate passes (0 open high/medium, pinned to the final code commit)
- [ ] Docs updated if user-facing behavior changed

## Constraints
- {{constraint, or "none"}}

## Out of Scope
- {{explicit exclusion, or "none"}}

## Open Questions
- {{anything unresolved — remove section if empty}}

## Decisions
- {{architectural decisions made during implementation — leave empty initially}}
