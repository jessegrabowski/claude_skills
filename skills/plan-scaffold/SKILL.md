---
name: plan-scaffold
description: >-
  Decompose a substantial piece of work into a written plan -- steps, then PRs, then commits -- saved as a
  linked, progress-tracked note folder in the Obsidian vault. INVOKED ON REQUEST ONLY: load it when the
  user asks for it by name or with /plan-scaffold, wherever that appears in their message -- start, middle,
  end, or as a passing aside; a mention is a request. Otherwise do not self-select it: a request to plan a
  feature, sequence work, break something into PRs, write a roadmap, or enter plan mode is not on its own
  a reason to load this skill, however closely the wording matches. Handle that work directly.
---

# Plan scaffold

Work that spans more than a sitting fails in a characteristic way: it becomes an undifferentiated blob. It can't be reviewed, can't be paused, can't be resumed after a week away, and can't be handed to anyone else. The failure is structural rather than a matter of effort, so the fix is structural too -- impose a decomposition with a natural stopping point at every level, and write it down before any code exists.

This skill produces that document and stops. What the plan is *for* -- a feature, a migration, a refactor, a research program, a package built from nothing -- changes the content entirely but changes the structure not at all. The structure is the skill.

Two commitments shape everything below:

1. **The decomposition is load-bearing.** step -> PR -> commit is not three words for "list". Each level answers a different question and carries its own sizing constraint, and a plan that blurs them provides no stopping points. The plan itself is the whole document set, not a fourth level above them.
2. **The plan lives in the vault, not the repo.** Plans outlive branches and often outlive the repo's interest in them. Keeping them in one place means they can be read side by side, compared, and mined for what a previous plan got right and wrong.

## Input

$ARGUMENTS

Expected: a plan name and enough of the work to decompose. **If an approved plan already exists earlier in the conversation -- including one just approved out of plan mode -- that plan *is* the content**, and this skill only arranges it into the house format. Re-planning it is not your job. A free description of the work with no plan behind it means planning comes first; see *If there is no approved plan yet*.

## Writing for the vault, not for a terminal

**Never hard-wrap prose in these notes.** One paragraph is one long line, however many characters it runs to, and the editor soft-wraps it. This is the opposite of the convention for source code and docstrings, and the difference is not stylistic: Obsidian renders these notes in a resizable pane, so hard line breaks fight the reader's window width instead of respecting it, and they turn every later edit into a manual reflow of the whole paragraph. Plans get edited constantly as steps complete, so a hard-wrapped plan is permanently ugly.

**US spellings throughout** -- behavior, standardize, analyze, program, license. British forms creeping into plan prose is a persistent tic worth watching for, especially in words like "parameterize" and "characterization" that show up constantly in this kind of document.

Concretely: no newline inside a sentence or a paragraph. Blank lines between paragraphs, list items, and headings -- yes, those are structure. Line breaks placed to hit some column count -- never. This applies to every `.md` file the skill writes, including table cells and bullet points, both of which break badly when split.

## The decomposition

| level | answers | sizing constraint |
|---|---|---|
| **step** | what is true after this that wasn't before | ends somewhere shippable -- the work could stop here and leave things better |
| **PR** | what can one human review in one sitting without losing the thread | one theme, ideally under ~400 changed lines; never mixes mechanical churn with logic changes |
| **commit** | what is the single logical change | one idea; reverting it leaves a coherent repo |

Each level's constraint doubles as a sizing test, and it cuts both ways -- a boundary can be wrong by being too big *or* by being too small. Judge by these signals, not by line or file counts:

| level | too big -- split when | too small -- absorb when |
|---|---|---|
| **step** | You can name a midpoint where the repo is already coherent and the goal partly delivered. That midpoint is a step boundary. | It leaves the repo incoherent on its own, or isn't a milestone -- it's a *PR inside* the adjacent step. |
| **PR** | The reviewer can't hold it in one sitting, it spans unrelated subsystems, or its one-line scope needs an "and". Split at the "and". | It can't be reviewed without reading its sibling -- same PR. |
| **commit** | The subject line needs an "and", or it mixes a refactor with a behavior change. | The tree doesn't build, or its tests don't pass, without the next commit -- squash them. |

A useful check while decomposing: can you write the commit's subject line right now, in under 60 characters, without the word "and"? If not, it's more than one commit. The same trick works one level up -- if the PR's title needs an "and", it's two PRs.

**PR and commit boundaries are the load-bearing ones**: a human reviews one and bisects the other, so getting them wrong has a cost outside the plan. Step boundaries are an organizing device for the plan itself -- place them wherever they make the work legible, and don't agonize over a step that could reasonably split two ways.

Two invariants ride on top and belong in every plan:

- **The test suite is green at every commit.** Not at every PR -- every commit. A commit that leaves the suite red can't be bisected through and can't be reverted cleanly, which forfeits most of what the decomposition bought.
- **Every change arrives with its tests.** Tests are not a step at the end. The commit that changes behavior and the commit that tests that behavior are the same commit. Where a step *is* about test infrastructure, say so explicitly.

Both need a baseline that actually holds. If there is no suite yet, or it's currently failing, then establishing one is step 1 and the invariant starts there -- say that in the plan rather than asserting something untrue from commit one.

## Non-negotiables

- **Never fabricate.** Populate every section from the approved plan, the conversation, and what you actually read in the repo. Never invent approaches, measurements, decisions, or risks the user never made -- padding a plan with plausible-looking content is the primary failure mode of this skill, and it is worse than a short plan because it reads as settled. When something is genuinely unknown, either ask or defer it; see below for which.
- **This creates docs only.** No source edits, no commits, no branches. The skill ends when the folder is written.
- **Defer to the project's own plan rules for decomposition.** If the repo's `CLAUDE.md` has a plan-generation section, it is the authority on *how the work breaks into commits*. This skill governs the file layout, the vault conventions, and the three-level scoping; the two compose.
- **Companion docs are optional, never the step skeleton.** A plan may warrant a `reference-<slug>.md` design note or an investigation write-up beside the step files. Create those *only* when there is real research to park, link them from the OVERVIEW as a clearly-separated group, and never stamp out empty ones.

## Unknowns: ask, or defer with `FILL`

Two kinds of unknown, handled differently. The test is whether the answer changes the *shape* of the folder.

**Ask -- before writing any file.** Use `AskUserQuestion`, and batch every open structural question into as few calls as possible rather than interrogating one at a time. When planning first, ask while still in plan mode, not after approval. These can't be deferred, because guessing wrong means rewriting the set rather than editing a line:

- the step list and their order
- how a step's work divides into PRs, and a PR's into commits, when the plan doesn't say
- the plan name or target folder, when it isn't derivable
- which of two readings of the work you meant, when they'd produce different steps

Offer the concrete alternatives you're weighing as the options -- a decomposition the user can pick from beats an open "how should I split this?".

**Defer with `<!-- FILL: ... -->`.** Leaf facts that slot into a finished skeleton without moving anything: a measurement, a hash, a test name, a file path, a decision the user hasn't made yet. Don't stall the scaffolding on these -- write the placeholder and report it. Asking a batch of trivia the user would rather fill in themselves is its own failure.

If you're unsure which kind you have, ask what happens when the answer arrives: a new heading or a re-ordered step list means ask; a filled-in blank means `FILL`.

## If there is no approved plan yet

This skill formats an *approved* plan; it does not invent one. When invoked without one, plan first, then scaffold:

1. `EnterPlanMode`, and settle the decomposition there: survey the ground (below), apply the sizing signals, and batch the structural questions into `AskUserQuestion` while still in plan mode.
2. Present the plan and call `ExitPlanMode` for approval. Don't separately ask whether the plan is acceptable -- that is what the approval is.
3. On approval, scaffold from the approved plan. Plan mode is read-only, so nothing under the vault folder can be written before this point.

## Process

### 1. Locate the vault and name the plan

The plan folder goes at `<vault>/<project>/<plan-name>/`. Find the vault by looking for a `.obsidian` directory (commonly under `~/Documents/`); if there's genuine ambiguity or none is found, ask rather than guessing -- writing a plan into the wrong tree is worse than a question.

`<project>` is the repo or project name, and reusing an existing project folder is the point: if `<vault>/<project>/` already exists, read its `README.md` first. It records what has already been investigated here, and the plan should build on that rather than rediscover it.

`<plan-name>` is a short kebab-case slug for *this* transformation -- `refactor`, `hsgp-rewrite`, `polars-migration`, `multi-country-support`. Fix obvious typos, confirming if ambiguous. **If that folder already exists, stop and ask** whether this is a continuation or a genuinely new plan; never overwrite one.

### 2. Survey the ground before proposing

The plan's value lies almost entirely in the accuracy of its opening diagnosis, so do the reading first. What's worth surveying depends on the work, but these questions apply broadly:

- **What already exists that this builds on or has to live with.** For new work, the existing abstractions it should extend rather than duplicate. For work on existing code, what's right and must be preserved -- a plan that lists only sins gives no guidance about what to keep, and the parts that work are usually the parts worth standardizing on.
- **What the real obstacles are**, sorted by kind rather than listed flat. Correctness problems, reviewability problems, and reproducibility problems get addressed in different orders, and unknowns are a fourth kind: things nobody can plan around until someone tries them.
- **The state of verification.** What tests exist, whether they pass right now, how long they take, what they actually cover. This determines whether the green-at-every-commit invariant has a baseline or has to build one first.
- **Tooling and CI.** Linter, formatter, type checker, pre-commit, CI: present, configured, enforced? Work built on an unstable mechanical layer produces diffs nobody can read.
- **Prior attempts.** If there's an abandoned branch, a stalled PR, or an earlier plan in the vault, read it. It records what the user wanted and where it got hard, and it often contains real work worth salvaging commit by commit rather than discarding.
- **Constraints that aren't technical.** Team review conventions, merge strategy, release cadence, anything licensed or manually obtained. These shape the PR boundaries as much as the code does.

If the user has stated coding standards -- in `CLAUDE.md`, a style guide, or just in conversation -- read them now, and name the specific ones the plan will apply. "Apply my standards" only becomes actionable once the plan says which and where.

### 3. Get sign-off on the shape before writing files

Present the proposed step list -- titles plus a one-line rationale each -- along with the ordering argument, and let the user react. This is cheap to change now and expensive to change once six markdown files cross-reference each other. When you arrived here through plan mode, `ExitPlanMode` approval already served this purpose; don't ask twice.

Ordering is a claim, not a formality, so make the argument explicit in the OVERVIEW. The general principle: **whatever makes later work verifiable comes first, and whatever is hardest to reverse comes last.** How that cashes out varies -- sometimes it's tooling and formatting before any logic change, sometimes it's a walking skeleton before any feature, sometimes it's the risky spike first precisely because everything downstream depends on what it teaches. Where the order is a genuine judgment call rather than a dependency, say so; a reader deserves to know which parts of the sequence are load-bearing.

Flag any step you think is under-specified or risky rather than papering over it. A plan that admits "step 5 depends on what we learn in step 3" is more useful than one that fabricates confidence.

### 4. Write the folder

```
<vault>/<project>/<plan-name>/
├── OVERVIEW.md          master plan, links to every step
├── step-01-<slug>.md
├── step-02-<slug>.md
└── ...
```

Use the templates in `references/templates.md` -- read that file before writing. Then update `<vault>/<project>/README.md` with a section linking the new plan, creating the README if the project folder is new.

Before finishing, re-read the actual files and check the wrapping rule held. Hard-wrapping is a strong habit and tends to creep back in around the middle of a long document, so verify against the files rather than from memory.

### 5. Hand it back

Say where it landed, walk the step sequence in a few sentences, list every outstanding `<!-- FILL: ... -->` placeholder so the user knows what remains, and name the one or two decisions you're least sure about. Don't start executing unless asked.

## Linking and metadata

Obsidian wikilinks (`[[step-01-foundations]]`), not markdown paths -- links inside a plan folder resolve by note name, so keep note names unique enough to be unambiguous across the vault. Every step file links back to `[[OVERVIEW]]` and forward to its successor, so a reader who arrives at a step from search can always find the frame around it.

`OVERVIEW.md` carries YAML frontmatter (see the template). This is what makes plans comparable to each other later: status and tags are queryable across plans, and a plan whose frontmatter says `status: abandoned` with a reason teaches more than one that simply stopped being edited. Keep the tag vocabulary small and reuse tags between plans -- a tag used once answers nothing.

## Progress tracking

Every step file ends with a commit table -- one row per planned commit, grouped by PR:

| PR | commit | change | tests | status |
|---|---|---|---|---|
| #1 | 1 | Add `ruff` config to `pyproject.toml` | n/a -- config only | ☐ |
| #1 | 2 | Apply `ruff format` across `src/` | suite green, unchanged | ☐ |
| #2 | 3 | Add `Grid.from_shape` constructor | new `test_grid_from_shape` | ☐ |

This table is what a reader checks progress against, so it has to be honest about tests. A `tests` cell reading "n/a -- config only" is fine and informative; a blank one means nobody thought about it. Status uses `☐` / `☑`, with `~~strikethrough~~` and a short note for anything dropped -- a plan that records what was abandoned and why is worth more later than one quietly edited to look prescient.

A commit is checked only when its tests pass and the full suite stays green. PR-level lines carry `reviewed` and `merged` alongside their verification check, so those attach to a specific PR rather than to the step as a whole.

Estimating commit counts precisely for distant steps isn't possible, and pretending otherwise makes the table a lie. For steps beyond the near horizon, write the rows you can defend and add an explicit note that the step gets expanded when it's reached.
