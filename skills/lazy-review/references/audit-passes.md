# Choosing audit passes

Read this in Phase 1, when proposing the plan.

The default set is `code-review`, `improve-code` and `improve-tests`. In the 15
reviews that saved per-pass reports, those three produced most of what reached a
payload (about 38, 27 and 19 posted comments). The `audit:*` passes beside them
added almost nothing: `exception-flow-analysis` reported nothing in 7 runs,
`code-quality-metrics-standards` one finding that was not posted, and every
finding from `testing-implementation` duplicated `improve-tests`. `when-in-rome`
mostly duplicated `improve-code`, and `humanizer` earned its place only where it
caught docs that had become false, not on style.

So propose an `audit:*` pass only when the diff carries the specific risk in the
table below and the default three would not cover it, and say what it is
expected to find that they would not. `audit:initial-security-analysis` is the
one worth proposing whenever code is reachable from a request or handles
credentials. Propose `when-in-rome` for a contributor new to the repo or an
upstream repo, and `humanizer` when the diff adds or rewrites prose docs.

| what the diff contains | pass worth proposing |
|---|---|
| library/shared code, big functions, god objects | `audit:code-quality-metrics-standards` |
| near-duplicate scripts or copy-paste siblings | `audit:code-duplication-detection` |
| new abstractions, class hierarchies, plugin shapes | `audit:solid-principles`, `audit:design-pattern-implementation` |
| error paths, retries, fallbacks, silent defaults | `audit:error-handling-resilience` |
| naming churn, unclear identifiers | `audit:readability-and-naming` |
| anything reachable from a request, or handling credentials | `audit:initial-security-analysis` first, then the narrow security passes |

Say what you are *not* running, and why.

Every `audit:*` pass is marked `disable-model-invocation: true`, so the Skill tool
refuses it. Say so in the plan. Once the user approves one, its agent reads
`/Users/jesse.grabowski/.claude/skills/audit/skills/<name>/SKILL.md` and follows it
in full. Each approved pass, audit or skill, gets its own agent (SKILL.md, Phase 4).

Each pass's report is a working artifact. It goes in the review folder, never in
the review -- these reports run far longer than anything the author should
receive. The review is the distillation.
