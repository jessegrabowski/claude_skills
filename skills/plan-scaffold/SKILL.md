---
name: planning-scaffold
description: >-
  Scaffold a multi-step implementation plan as a document set under planning/ — an OVERVIEW.md plus one
  phase-<N>-<slug>.md per phase — enforcing the three-level Phase → PR → Commit hierarchy (planner /
  reviewer / author scope) using the phase-doc convention. INVOKED ON REQUEST ONLY: load it whenever the
  user asks for it by name or with /planning-scaffold, wherever that appears in their message — start,
  middle, end, or as a passing aside; a mention is a request. Otherwise do not self-select it: a request
  to plan a feature, design an approach, break work into phases/PRs/commits, write a plan up as a
  document, or enter plan mode is not on its own a reason to load this skill, however closely the wording
  matches the conventions above. Handle that work directly.
---

You are stamping out a planning document set — an `OVERVIEW.md` plus one `phase-<N>-<slug>.md` per phase — under `planning/<name>/`. The output is *planning scaffolding*, not code: docs populated from the approved plan and the conversation, with the standard section skeletons and empty progress checklists ready to fill as work lands.

## Input

$ARGUMENTS

Expected: a plan name and a phase outline. If there is an approved plan earlier in the conversation — including one just approved out of plan mode — that plan *is* the content, and this skill only arranges it into the house format. A free description of the work with no plan behind it means planning comes first; see *If there is no approved plan yet*.

## The three levels (the core discipline this enforces)

A plan decomposes into a strict three-level hierarchy — **Phase → PR → Commit** — each level a **distinct, enforced unit of logical scope**. This is the point of the whole system; every section below exists to make these three levels legible. Use these three names throughout; the plan itself is the whole doc set, not a fourth level.

| Level | Unit of scope | Owner / audience | Scope rule (what makes the boundary valid) |
|---|---|---|---|
| **Phase** | one doc — planning scope | the planner | Leaves the repo coherent on its own; one milestone toward the plan's goal. Phases are strictly ordered unless marked reorderable. |
| **PR** | human-reviewable scope | the reviewer | Reviewable in one sitting; self-contained; the suite stays green at its tip. **A phase contains one or more PRs.** |
| **Commit** | one grouped change — author scope | the author | One logically-scoped, fully-encapsulated change; the tree stays buildable; tests ship *with* the feature they cover, not in a trailing commit. **A PR is a sequence of commits.** |

The scaffolding must make all three levels explicit: the OVERVIEW enumerates phases and a PR summary maps PR → phase → scope; each phase doc's task table groups its commits under their PR(s). Do not collapse levels — a phase is not a PR is not a commit, even when a phase happens to be a single PR of a single commit.

## Sizing (which way a boundary is wrong)

Each level's scope rule doubles as a sizing test. Too big → split at the seam; too small → it belongs to its neighbor, one level up. Judge by these signals, not by line or file counts.

| Level | Too big — split when | Too small — absorb when |
|---|---|---|
| **Phase** | You can name a midpoint where the repo is already coherent and the goal partly delivered. That midpoint is a phase boundary. | It leaves the repo incoherent on its own, or isn't a milestone — it is a *PR inside* the adjacent phase. |
| **PR** | The reviewer can't hold it in one sitting, it spans unrelated subsystems, or its one-line scope needs an "and". Split at the "and". | It can't be reviewed without reading its sibling — same PR. |
| **Commit** | The message needs an "and", or it mixes a refactor with a behavior change. | The tree doesn't build, or its tests don't pass, without the next commit — squash them. |

PR and commit boundaries are the load-bearing ones: a human reviews one and bisects the other, so getting them wrong has a cost outside the plan. Phase boundaries are an organizing device for the plan itself — place them wherever they make the work legible, and don't agonize over a phase that could reasonably split two ways.

## Non-negotiables

- **Never fabricate.** Populate every section from the approved plan / conversation. Never invent approaches, measurements, or decisions the user never made — padding a plan with plausible-looking content is the primary failure mode here. When something is genuinely unknown, either ask or defer it; see below for which.
- **This creates docs only.** No source edits, no commits. `planning/` is typically git-excluded — check `.git/info/exclude` / `.gitignore`; if it is, say so in your report (the files are local scaffolding).
- **Defer to the project's plan rules for decomposition.** The repo's root `CLAUDE.md` `# Plan Generation` section is the authority for *how the work breaks into commits* (each independently meaningful, tests per commit). This skill governs the *file layout and the three-level scoping*; the two compose.
- **One convention: the phase-doc form below.** If `planning/` already has a set, match its exact section headers and wording where they differ in detail — but the structure is always the phase form here, never a second dialect.
- **Reference/research docs are optional companions, never the phase skeleton.** A set may carry `reference-<slug>.md` design docs or a `notes_from_the_field.md` beside the phase docs. Create those *only* when there is real research/design to park, list them in the OVERVIEW as a clearly-separated group, and **never** treat them as the per-phase template or stamp empty ones.

## Unknowns: ask, or defer with `FILL`

Two kinds of unknown, handled differently. The test is whether the answer changes the *shape* of the doc set.

**Ask — before writing the plan file or any doc.** Use `AskUserQuestion`, and batch every open structural question into as few calls as possible rather than interrogating one at a time. When planning first (see below), ask while still in plan mode — not after approval. These can't be deferred, because guessing wrong means rewriting the set rather than editing a line:
- the phase list and their order (and whether any are reorderable)
- how a phase's work divides into PRs, and a PR's into commits, when the plan doesn't say
- the plan name or target directory, when it isn't derivable
- which of two readings of the work you meant, when they'd produce different phases

Offer the concrete alternatives you're weighing as the options — a decomposition the user can pick from beats an open "how should I split this?".

**Defer with `<!-- FILL: … -->`.** Leaf facts that slot into a finished skeleton without moving anything: a measurement, a hash, a test name, a file path, a decision the user hasn't made yet. Don't stall the scaffolding on these — write the placeholder and report it. Asking a batch of trivia the user would rather fill in themselves is its own failure.

If you're unsure which kind you have, ask yourself what happens when the answer arrives: a new heading or a re-ordered phase list means ask; a filled-in blank means `FILL`.

## If there is no approved plan yet

This skill formats an *approved* plan; it does not invent one. When invoked without one — a free description of the work, no prior plan in the conversation — plan first, then scaffold:

1. `EnterPlanMode`, and settle the decomposition there: explore the repo, apply the sizing signals, and batch the structural questions above into `AskUserQuestion` while still in plan mode.
2. Write the plan to the plan file and call `ExitPlanMode` for approval. Do not ask separately whether the plan is acceptable — that is what the approval is.
3. On approval, scaffold from the approved plan. Plan mode is read-only, so no file under `planning/` can be written before this point.

When an approved plan already exists, skip straight to the workflow — it is the content, and re-planning it is not your job.

## Workflow

1. **Derive the target.** Kebab-case plan name → `planning/<name>/` (honor an explicit path). Fix obvious typos (confirm if ambiguous). If the directory exists, stop and ask before overwriting.
2. **Settle the decomposition at all three levels.** From the approved plan: the ordered phases, the PR(s) inside each phase, and the commits inside each PR. Check each unit against the sizing signals above. Any level still unclear is a structural unknown — ask now, batched, before writing anything.
3. **Write `OVERVIEW.md`** from the template: frame + boilerplate, the linked phase list, context, any prior-art/design/invariants/verification the plan warrants, the PR summary mapping PR → phase → scope, the sequencing note, the `## Progress` checklist, and the do-not-commit footer.
4. **Write each `phase-<N>-<slug>.md`** from the template: Goal, Files, Design, the Tasks table grouping commits under their PR(s), the named Tests, and the `## Progress` checklist.
5. **Report** the files created, whether `planning/` is git-excluded, and every outstanding `<!-- FILL: … -->` placeholder — so the user knows exactly what remains to complete the plan.

## Progress vocabulary

Progress checklists use `- [ ]` / `- [x]`, one line per commit (append its hash once landed) plus the PR-level verification checks and `reviewed` / `merged`. A commit is checked only when its tests pass and the full suite stays green.

## Template — `OVERVIEW.md`

```markdown
# <Plan title>: <subtitle>

<Frame paragraph: what this plan achieves and its evidence base.> Each phase below is one document; a phase groups its work into one or more pull requests of human-reviewable size, and each PR is a sequence of logically-scoped, fully encapsulated commits (the task tables spell them out).

- [phase-1-<slug>.md](phase-1-<slug>.md) — PR(s) 1[–<m>]: <one line>

<Only if research docs exist:> reference documents sit alongside the phases and carry the research the design rests on: [reference-<slug>.md](reference-<slug>.md), …

## Context
<Why this work exists; where the limitation lives in the codebase.>

## Prior art / Prior-art validation        <!-- if any: reference reading, spike results, measured facts -->

## The design: <…>
<The approach + the key decisions/conventions, prose + pseudocode.>

## Invariants (locked by tests across the phases)
1. **<name>**: <assertion the tests enforce>

## Verification (end to end)
1. <check run after the relevant phase>

## PR summary
| PR | Phase | Scope | Primary files |
|----|-------|-------|---------------|
| 1 | 1 | <scope> | <files> |

<Sequencing paragraph: dependencies / ordering / what gates the start.>

## Progress
- [ ] PR 1 — Phase 1: <scope>
- [ ] End-to-end verification

Do not commit or open PRs without an explicit request; the commit/PR grouping in each phase doc is the intended structure for when asked.
```

## Template — `phase-<N>-<slug>.md`

```markdown
# Phase <N> — <title>

Back to [OVERVIEW.md](OVERVIEW.md). Covers PR(s) <k>[–<m>]. <standalone note: what keeps the suite green on its own.>

## Goal
<What this phase accomplishes and the property it establishes for the next.>

## Files
- <path>

## Design
<prose + pseudocode; the conventions/invariants this phase must honor>

## Tasks
| PR | Commit | Task | Files | Test |
|----|--------|------|-------|------|
| <k> | <N>.1 | <task> | <files> | <test name> |
| <k> | <N>.2 | <task> | <files> | <test name> |
| <k+1> | <N>.3 | <task> | <files> | <test name> |

## Tests (`<test path>`)
- `<test_name>` — <what it pins>

## Progress
- [ ] commit <N>.1 — <task> (`<hash once landed>`)
- [ ] commit <N>.2 — <task> (`<hash once landed>`)
- [ ] PR <k>: <verification check> · reviewed · merged
- [ ] commit <N>.3 — <task> (`<hash once landed>`)
- [ ] PR <k+1>: <verification check> · reviewed · merged
```

Rows repeat per commit and the `PR` column changes at each PR boundary — a phase with a single PR simply has one group. Progress lines follow the same grouping, so `reviewed` / `merged` attach to a specific PR rather than to the phase.
