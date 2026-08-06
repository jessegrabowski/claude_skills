# Templates

Shapes to fill, not forms to submit. Cut a section that has nothing real in it -- an empty "Risks" heading is worse than no heading, because it reads as "no risks" rather than "not thought about". Add sections a particular plan needs.

Prose in these documents is for a reader six months out who has forgotten everything, including the person who wrote it. Write the *why*, and be concrete: name files, functions, and test names rather than gesturing at "the data layer".

**Fill every section from what you actually know** -- the approved plan, the conversation, the repo you read. Never invent a measurement, a rejected alternative, or a risk to make a section look complete; a fabricated plan reads as settled and is worse than a thin one. Where a leaf fact is genuinely unknown, leave `<!-- FILL: what's missing -->` in place and report it, rather than guessing or stalling.

**These templates are written unwrapped on purpose -- every paragraph is a single line.** Match that. A newline belongs between paragraphs and list items, never inside a sentence, because Obsidian soft-wraps to the reader's pane and hard breaks make every subsequent edit a manual reflow.

---

## OVERVIEW.md

````markdown
---
project: <repo name>
plan: <plan-name>
repo: <path or URL>
branch: <branch the work happens on, or "TBD">
started: <YYYY-MM-DD>
status: active        # active | paused | done | abandoned
tags: [<small, reused vocabulary -- e.g. migration, testing, tooling, performance, api-design>]
---

# <Plan title>

**TL;DR -- <one or two sentences: what this transforms, into what, and the single biggest reason it's worth doing.>**

## Starting point

<The honest diagnosis. What exists that this builds on or has to live with, what stands in the way, and which kind each obstacle is -- correctness, reviewability, reproducibility, or genuine unknown. Concrete: file names, actual test counts and runtimes, real numbers. For work on an existing codebase this is where what's-right goes alongside what's-wrong; for something built from scratch it's the surrounding constraints and the prior art being adopted.>

## What "done" looks like

<The end state, described so it can be checked rather than felt. Prefer statements someone could run: a command that passes, a grep that returns nothing, a capability a new user has on day one.>

## Invariants

- The test suite is green at every commit.
- Every behavior change arrives in the same commit as its tests.
- <Anything project-specific this plan promises not to break: public API stays stable, no new dependencies, notebooks keep running, performance doesn't regress.>

## Steps

| # | step | what exists after | PRs |
|---|---|---|---|
| 1 | [[step-01-<slug>]] | <the capability gained> | 2 |
| 2 | [[step-02-<slug>]] | <...> | 1 |

## Why this order

<The argument for the sequence. Which steps unblock which, why the ordering makes later work verifiable and defers what's hardest to reverse, and where it's a genuine judgment call rather than a dependency.>

## Open questions

<Decisions deferred, and what would resolve each. If a later step depends on something learned earlier, say so here rather than fabricating detail in that step's file.>

## Progress

| step | status | notes |
|---|---|---|
| [[step-01-<slug>]] | ☐ | |
| [[step-02-<slug>]] | ☐ | |
````

---

## step-NN-\<slug\>.md

````markdown
# Step N -- <title>

<- [[OVERVIEW]] | next: [[step-0N+1-<slug>]]

**TL;DR -- <what this step does, and what is true afterwards that wasn't before.>**

## Why

<The problem this step solves and the cost of not solving it. Argue the position rather than restating the title.>

## Approach

<How it gets done: which files, which patterns, which tools. Name the alternatives that were rejected and why -- the next person will reconsider them otherwise.>

## Tests

<What the test story is for this step. New tests being written, existing tests being changed and why that's safe, coverage the step is expected to move. If the step is mostly mechanical, say how green-at-every-commit is verified -- which command, run when.>

## PRs

### PR 1 -- <title>

<One paragraph of scope: what's in, and explicitly what's out. Rough diff size, and any review hazard worth warning about -- a large generated diff, a rename that hides a logic change, a file that needs careful reading.>

### PR 2 -- <title>

<...>

## Commits

| PR | commit | change | tests | status |
|---|---|---|---|---|
| 1 | 1 | <subject line, imperative, <60 chars> | <new/changed tests, or "n/a -- <why>"> | ☐ |
| 1 | 2 | <...> | <...> | ☐ |
| 2 | 3 | <...> | <...> | ☐ |

## Risks

<What could go wrong, and the mitigation or rollback. Cut this section if the step is genuinely low-risk -- don't manufacture risks to fill it.>
````

---

## Project README.md entry

The project README is the vault's index for the repo. Add the plan to it; create the file with a title and this section if the project folder is new.

```markdown
## Plans

- [[<plan-name>/OVERVIEW]] -- <one line: what it transforms and current status>
```

If the project folder already has topic notes (investigations, benchmarks, references), link the relevant ones from the step files that build on them. Reusing an existing investigation is the reason plans live in the vault at all.

---

## Companion documents (only when warranted)

A plan may carry a `reference-<slug>.md` design note or investigation write-up beside its step files, when there is real research the design rests on and parking it inline would bloat a step. There is no template for these -- they are whatever the research needs. Two rules: link them from the OVERVIEW as a clearly-separated group, distinct from the step list, and never create one speculatively. An empty reference doc is the fabrication failure in another shape.
