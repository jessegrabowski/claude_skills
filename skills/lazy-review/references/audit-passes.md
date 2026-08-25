# Choosing audit passes

Read this in Phase 1, when proposing the plan.

`/audit:<name>` passes are narrow and deep. Pick by what the diff actually
contains rather than running a sweep -- a plan that proposes eight passes on a
40-file diff is a plan nobody reads.

| what the diff contains | pass worth proposing |
|---|---|
| library/shared code, big functions, god objects | `audit:code-quality-metrics-standards` |
| near-duplicate scripts or copy-paste siblings | `audit:code-duplication-detection` |
| new abstractions, class hierarchies, plugin shapes | `audit:solid-principles`, `audit:design-pattern-implementation` |
| error paths, retries, fallbacks, silent defaults | `audit:error-handling-resilience`, `audit:exception-flow-analysis` |
| new tests, or conspicuously none | `audit:testing-implementation` |
| naming churn, unclear identifiers | `audit:readability-and-naming` |
| anything reachable from a request, or handling credentials | `audit:initial-security-analysis` first, then the narrow security passes |

Alongside those, say whether you plan to run `improve-code` (tiered worklist
against stated conventions) and `improve-tests` (test-quality audit). On a
research or analysis PR those two usually find more than the security passes do.

Say what you are *not* running, and why.

Each pass's report is a working artifact. It goes in the review folder, never in
the review -- these reports run far longer than anything the author should
receive. The review is the distillation.
