---
name: audit
description: Router for the focused analysis passes — security, design, reliability, and code quality. Use when the user wants a targeted audit but hasn't named which one ("audit this for security", "check the error handling", "is this design sound"), or wants to know which passes exist. Each pass is also invocable directly as /audit:<name>.
---

# audit

The individual passes under this plugin do the work; this skill picks the right one. Each is invocable directly as `/audit:<name>` when the user already knows what they want — routing through here is for when they don't.

These are *focused* passes, deliberately narrower than the review entry points. `code-review` gives a whole-diff verdict, `improve-code` gives a tiered worklist it can apply. A pass here goes deep on one axis across whatever scope it's given, and reports.

## Choosing a pass

Read what the user actually asked for and pick the narrowest pass that covers it. Run several when the request spans axes; say which you're running and why. If the request is genuinely broad ("review this"), that's `code-review` or `improve-code`, not this — say so rather than fanning out across a dozen passes.

**Security**

| pass | covers |
|---|---|
| `initial-security-analysis` | first-pass attack surface and risk map — **start here** when the request is "audit security" with no narrower target |
| `input-validation` | injection and malformed-input handling |
| `authentication-flow-review` | login, sessions, tokens, credentials |
| `authorization-implementation` | access control, privilege and escalation paths |
| `session-cookie-security` | cookie flags, expiration, fixation, storage |
| `secrets-management-audit` | hardcoded secrets, key handling, rotation |
| `database-security` | injection, access control, encryption, data exposure |
| `api-and-infrastructure` | endpoints, headers, transport, deployment config |
| `file-handling-business-logic` | uploads, path traversal, type validation, storage |
| `business-logic-vulnerabilities` | workflow bypasses, race conditions, abuse paths |
| `logging-monitoring` | security visibility, sensitive-data leakage, audit trail |
| `comprehensive-security-report` | aggregates the above into one prioritized report — **run last**, and only after the passes it summarizes |

**Design**

| pass | covers |
|---|---|
| `initial-software-design-analysis` | first-pass architecture and structure review |
| `solid-principles` | the five SOLID principles, with concrete fixes |
| `design-pattern-implementation` | patterns used, misused, or missing |
| `code-duplication-detection` | duplicate and near-duplicate code, consolidation |

**Reliability**

| pass | covers |
|---|---|
| `error-handling-resilience` | error-handling coverage and propagation |
| `exception-flow-analysis` | how errors flow through critical paths; swallowed failures |
| `resilience-fault-tolerance` | failure modes, retries, timeouts, graceful degradation |

**Quality**

| pass | covers |
|---|---|
| `readability-and-naming` | identifiers, clarity, structure |
| `code-quality-metrics-standards` | complexity and adherence to quality standards |
| `testing-implementation` | coverage gaps, weak assertions, untested paths |

For a dedicated test-quality audit prefer `improve-tests`, which goes deeper than `testing-implementation` and can apply its findings.

## Running one

Hand the pass the scope the user gave — files, a module, a diff, or the working changes. Every pass reports; none of them edit. When a finding needs applying, route it to `improve-code`, and say so rather than editing here.
