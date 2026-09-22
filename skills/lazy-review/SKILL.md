---
name: lazy-review
description: >-
  Reviews a large or messy pull request end to end -- surveys it, runs the audit
  passes worth running, then posts a lean GitHub review with validated inline
  comments. Use for "review #210", a pasted PR URL, "can you look at this PR",
  "this PR is a mess", "what's wrong with this branch", "is this mergeable", or
  "help me salvage this".
disable-model-invocation: true
---

# lazy-review

Review a PR the author will actually act on. Same philosophy as `lazy-pr` and
`lazy-issue`: less is more. Every comment names one thing to do. The diff is the
context; the comment is a pointer to the fix.

A big PR tempts you into writing an essay, because you did a lot of work to find
what you found. Resist it. The author does not need your investigation, your
reasoning, or your reassurance -- they need the shortest possible list of things
to change. Work that cleared verification is invisible in the output. That is
what verification is for.

## Input

$ARGUMENTS

Arguments narrow the job. Handle these before planning:

- A PR number, URL, or branch -- the target. With none, use the current branch's PR.
- A named concern ("focus on the numerics", "just the data hygiene", "is it safe
  to merge") -- treat as the review's lens and weight the plan toward it.
- A named audit pass (`--audit code-quality-metrics-standards`) -- run it, skip
  proposing alternatives for that axis.
- `--depth quick` -- blockers only, skip phases 3 and 4, one artifact note.
- `--no-post` -- stop after the payload; do not offer to submit.

## Phase 0: establish the real scope

Do this before reading a single line of code. It routinely changes the size of
the job.

```bash
gh pr view <n> --json title,body,baseRefName,headRefOid,author,additions,deletions,changedFiles
git merge-base --is-ancestor origin/<other-open-branch> HEAD && echo "STACKED"
```

Check whether another open PR's branch is an ancestor of this one. A PR declaring
`main` as its base while sitting on top of an unmerged branch re-presents that
branch's work as its own, and you will otherwise review thousands of lines twice
and attribute them to the wrong author. When you find it, the real diff is
`origin/<ancestor>..HEAD`, that becomes your scope, and retargeting the base is
the first thing you ask for.

List the open PRs (`gh pr list --state open`) and test the plausible ancestors.
This costs one command and is the highest-value thing in the whole skill.

Then record the numbers that matter: real files changed, real insertions, bytes
added to the repo (`git diff --name-only <base>..HEAD | while read f; do [ -f "$f" ] && stat -f%z "$f"; done`),
and the commit log with authors. Large binary or generated files hiding in a diff
are a finding on their own.

## Phase 1: plan, and get sign-off

Survey the diff enough to propose a plan -- file inventory, what the PR claims to
do, and where the risk concentrates. Then propose which passes to run and why,
and wait.

The point of the plan is that the user knows things you cannot see: which files
are production-adjacent, whose work is genuinely new, what they already distrust.
Two minutes of their input reshapes the next hour.

Read `references/audit-passes.md` for which passes fit what you found.

## Phase 2: explore in parallel

Fan out read-only explore agents, one per coherent area, in a single batch. Give
each agent the real scope from Phase 0, the specific questions you want answered,
and an instruction to cite `file:line` for every claim. Those citations are for
your verification and your notes. They do not go into comments.

Ask each agent for the things you cannot cheaply get yourself:

- Duplication *across* files -- which functions are near-copies, named explicitly
- Data sources: repeatable and queryable, or frozen fixtures with hardcoded paths
- Whether new code reuses the real machinery or reimplements it locally
- For modified files: whether a change alters behavior for existing callers, with
  the callers grepped and named

Two rules. Agents locate and report; they do not review -- the judgment is yours.
And when an agent reports something load-bearing that it flags as unverified,
verify it yourself before it reaches the review. An agent's "this looks like it
might" becomes your "confirmed" only after you have read the chain.

While they run, do the mechanical work in Phase 3 rather than waiting.

## Phase 3: mechanical passes, attributed to the diff

Run the project's own tools, pinned to the versions the project pins. A finding a
linter would catch is not a review comment, so the value here is establishing
what is *clean* -- which tells you the messiness is elsewhere and stops you
reporting noise.

```bash
git diff --name-only <base>..HEAD | grep '\.py$' > /tmp/scope.txt
cat /tmp/scope.txt | tr '\n' '\0' | xargs -0 uvx ruff@<pinned> check
```

Attribute type-checker output to lines the PR added. A strict checker on a large
legacy file emits hundreds of pre-existing diagnostics; reporting those as
findings against the diff destroys your credibility in one shot. Get the added
line numbers from `git diff -U0` and intersect. "255 errors, 0 on added lines" is
a real and useful result, and the opposite conclusion from "255 errors".

Do the same for anything else the repo enforces: a convention sweep (module
docstrings, banned imports, non-ASCII where the project is ASCII-only), an import
smoke test on new modules, and the test suite for a baseline. Note skipped tests
-- a test silently skipped for a year is a finding.

## Phase 4: the chosen passes

Run what the user approved. Feed each pass the real scope and the concern from
`$ARGUMENTS`.

## Phase 5: consolidate

Write artifacts as you go; `references/artifacts.md` has the folder, the note
layout, and the payload format the posting script reads.

Tag every finding **confirmed** (you read the chain) or **suspected** (mechanism
plausible, not traced). The chain is recorded in `02_findings.md` and nowhere
else. A comment never demonstrates that you read it. A suspected finding gets
verified before the review, or it gets dropped. It does not get downgraded into a question -- a question is for
what the code cannot answer, not for a hunch you ran out of time to check.

Sort findings by what they cost:

1. **Changes numbers without crashing.** Silent wrong answers in code someone
   will act on. These are the blockers, and they are why the review exists.
2. **Blocks a fix.** Untestable code, an unimportable module, a 1000-line
   function -- things that make the blockers hard to fix.
3. **Shape.** Files that belong in another PR, committed data, scope creep. Often
   the largest line-count reduction available and the easiest to agree on.
4. **Conventions.** Stated rules broken. Count the sites in the notes. The
   comment names the rule and the site it sits on.

## Phase 6: draft the review

### Which findings become comments

A comment earns its place if it needs a response from the author -- an edit, or
an answer. "Why local import?" earns its place even though it names no edit,
because the author has to say something and the thread stays open until they do.
What does not earn its place is a fact the author cannot act on and does not have
to answer. There is no comment budget.

Resist the urge to add one, because two facts about the medium make a count
ceiling actively harmful. An inline comment is anchored: the author meets it
beside the code while reading that file, not as item 26 of a list, so one more
anchored comment costs them almost nothing. And every comment is a resolvable
thread, which makes the set a tracked worklist -- body prose is not tracked, has
no resolve button, and notifies nobody.

So a finding that names a site goes at that site. Writing "35 stale `Usage:`
lines across six files" into the body instead of posting them where they are
makes the author go find what you already had line numbers for, and nothing
records whether they did. Five stale references are five edits and therefore five
comments; the first carries the explanation and the rest are one line pointing at
it. A six-word comment on the right line is the cheapest useful thing this skill
produces, and thirty of those are a worklist, not a form letter.

What the gate does exclude is a finding whose action is a judgment rather than an
edit. "Split this into five PRs" and "move these 3,154 lines to their own PR" are
asks; they go in the body. If you find yourself moving an anchored finding into
the body to shorten the list, you are trading the author's attention for your own
sense of tidiness.

The length problem is real, but it lives inside comments, not in their number.
Thirty comments that each name a line to change is a worklist; ten that each
carry a paragraph of reasoning is an essay.

Finding little on a large PR is still a result. A clean 3,000-line diff earns a
two-comment review, and four phases that turned up nothing is what verification
looks like when the code is good. The pull to justify the machinery by producing
findings is strongest exactly when there is least to report.

### The body

Two to four sentences of prose. No headings, no bold, no numbered list, and no
`path:line` references -- the comments carry those, and duplicating them writes
the review twice.

Lead with the one thing too big to anchor: a base branch that needs retargeting,
a split, an architecture concern. One item, in prose, with its reasoning. This is
the only place reasoning belongs. If the ask is a different API shape, sketch it
in a code block. For a big PR the ask is almost always a split, so give the split
as a table of PRs with line counts.

Then the state of the review if it is not complete: which files were covered and
which were not. A review that silently stops halfway is worse than one that says
so.

One sentence on what is working, only if you verified it and only stated as a
fact -- "the mlx suite passes locally", "the MvNormal factorizations check out
numerically". Not an assessment of the work or the author.

Everything a comment already carries stays out.

### Each comment

A comment is short. In the reviews this skill is modeled on, the median is
fifteen words and a third are under ten. Those are targets, not trivia: if your
drafted set has a median near twenty-five and only one or two fragments in it,
the comments are carrying explanation the author did not ask for, and the set
will read as an essay however many findings are real.

A bare fragment is a complete comment: "remove", "module level", "pass a Mode",
"unc -> unconstrained", "same as `cohorts.py:110`".

Before you show the draft, do a cutting pass. Take each comment and ask what the
shortest version is that still names the edit. Most lose their first clause,
because the first clause usually restates where the reader already is.

The cutting pass shortens comments. It never merges them, and the count only goes
up during it. Rolling five sites into one comment that lists five paths looks like
tightening and is the opposite: the author now has one thread for five edits, four
of the five are not anchored where the work happens, and nothing tracks which ones
got done. When a finding recurs, the first site carries the reason and every other
site gets its own comment of about five words pointing back -- "duplicate
`_file_sha256`, same as `production_contract.py:948`". Those pointers are most of
how a review reaches a third of its comments under ten words, and they are the
cheapest useful thing here.

So the target comes out of the shape of the set, not out of compression. If the
draft has no comments under ten words, the usual cause is repeats that got merged,
not prose that needs trimming. A comment that genuinely resists cutting is either a
real mechanism finding, which is fine and rare, or a teaching comment, which needs
clearance.

Three shapes carry almost everything. The imperative is the least common of them.

**The edit.** What to change, plus at most one sentence of reason. The reason
exists only when the author would push back without it.

> slice bounds come back as 0-d mx arrays here, so `x[1:4, idx]` still raises. cast the slice components to int

**The question.** Post it when the author should justify a choice, even when the
diff contains the answer. Three to eight words is normal. No preamble, and no
statement of what turns on the answer unless that is genuinely unobvious.

> Why local import?

> Is this check possible to fail?

> is this a test of pymc?

> Do we need a whole new file for this?

A question is not a softened instruction and never a finding you failed to
verify. A suspected finding gets verified or dropped. Turning it into a question
is the single most likely way this skill degrades, because a question costs
nothing to write and looks like diligence.

**The suggestion block.** When the fix is a literal token swap, paste it. Add a
sentence only when the swap does not explain itself.

````
```suggestion
    torch_dtype = getattr(torch, op.dtype)
```
````

Mark severity explicitly. `nit:` for style, "not a blocker" for a real point that
should not hold the merge. This is not hedging. It tells the author which of
thirty comments to argue with, and omitting it makes every comment read as a
demand.

Defer scope out loud when the fix is real but does not belong in this PR: "leave
for a follow-up PR", "open a TODO", "do it here for this test, new PR for the
rest". Name what the follow-up covers.

One comment names one thing. A second thing wrong on the same line is a second
comment on that line, never a "Separately, ..." tacked onto the first. A finding
that recurs gets one comment carrying the reason and one line at each other site
pointing back by `path:line`: "`edge_sources.py` is gone, same as
`cohorts.py:110`." Never point at another comment by its `C` id, because the
author cannot see those.

A number belongs in a comment only when the number is the edit: the wrong value
next to the right one, or the count of sites the author has to touch. A
complexity score, a row count you verified against, or a percentage that shows
how bad it is stays in the notes.

Cite a location other than the anchored line only when the fix is at that other
location. The one-line pointer above is the case. A path cited to show where the
consequence lands is the chain, and the chain stays out.

What does not belong in a comment:

- Praise, or a preamble crediting the author before the finding. If the code is
  fine, there is no comment.
- Anything you chased and cleared. "Order holds on the pinned version, checked"
  is cleared work. It cost you time; it costs the author nothing to never hear
  about it.
- The story of how you found it.
- Your reasoning about severity, or how many other places you checked.
- An answer to an objection the author has not made. If you are rebutting the
  code comment beside the line, you are arguing in advance. State the edit.
- The rulebook. Say the rule. Never "CLAUDE.md rules this out" or "CLAUDE.md
  mandates American English". The author knows where the rules live.
- Restating what the diff plainly shows.
- Unfalsifiable adjectives dressed as verdicts -- "cleaner", "more robust",
  "better structured". Name the failure, or mark it `nit:` and name the concrete
  alternative.
- Signposting instead of stating -- "worth a look", "keep an eye on", "the
  interesting bit". Name the edit directly. This is not the same as marking
  severity, which is required.

### Comments that need clearance

Two kinds of comment do not get posted without the user reading them first. Draft
them, hold them in a separate block when you show the review, and post only what
comes back approved.

**Teaching comments.** Anything longer than about three sentences that explains a
mechanism to the author rather than naming an edit. These are sometimes exactly
right for a first-time contributor. They are also where a model is most likely to
explain something wrong at length, or explain something the author already knows.
Default to the short form and offer the long one beside it.

**Taste.** A finding whose whole content is that a name, a layout, or an API shape
is worse than an alternative, with no failure behind it. State it impersonally and
concretely -- "`unc` is too abbreviated, `unconstrained`" -- and group these
together when you show the draft. Some are worth posting and some are the model
inventing an opinion, and only the user can tell which.

Everything else follows the normal Phase 7 authorization.


### Examples

The shapes, from real reviews.

**Edit with reason:**

> slice bounds come back as 0-d mx arrays here, so `x[1:4, idx]` still raises. cast the slice components to int (AdvancedSubtensor above has the same bug, factor out a helper and use it in both)

**Edit, no reason needed:**

> collapse the four new tests into one parametrized over inc/set and index form, like `test_mlx_AdvancedIncSubtensor1_duplicate_indices` below

**Fragment:**

> drop this comment, it's a changelog. `# mirrors AdvancedIncSubtensor.perform` is plenty

**Question:**

> Why local import?

**Nit:**

> nit: `_set_data` is too close to `pm.set_data`, which changes the actual model data. `_set_data_info`?

**Deferral:**

> not a blocker, this duplicates `pytensor_ml/optim/base.py`. worth a follow-up to use that instead

**Pointer to a repeated finding:**

> `edge_sources.py` is gone, same as `cohorts.py:110`

### Shortening an over-long finding

The work that found a thing is not the comment. These are real first drafts and
what they should have been.

> **Make this opt-in and loud, or restore the real query.** `delta_bp=0.0` here reaches `linprog/result.py:42`, where `eqty_allocation = -allocation_sod / 1000 * delta_bp` becomes identically 0, taking `eqty_pos_pnl` and `gmv_eqty_allocation_sod` with it -- the LP engine's whole equity hedge leg. `long_dur_lp.py`, added in this PR, reaches it via `long_liquid_book.load_universe:78`, so any LP number in the memo has no equity hedge and doesn't disclose it. The comment says "only `backtest/linprog/result.py` reads `delta_bp`" -- that file is the consumer. Fix: `opscore: Literal["query", "disabled"] = "query"`, `RuntimeWarning` on the disabled branch. If `opscore_straights_results` no longer resolves `delta_bp`, that's an upstream schema fix, not a silent literal. Note the table-name fix at `data_utils.py:1739` now has zero live callers, so it's unverified.

> Make the `delta_bp` stub opt-in and warn when it's on, or restore the query. Stubbing it to zero removes the LP engine's equity hedge, and `long_dur_lp.py` reaches this path.

> Index the multiplier off the `_tenor_bucket` column rather than off `tb`. `tb` was computed at line 163 from the pre-join frame; `w` here is post-join, and polars documents `maintain_order` as defaulting to `'none'`. Order does hold on the pinned 1.42.1 (checked, 0/200,000 rows mismatched), so today's numbers are fine; a polars bump permutes the level correction with nothing raising. `_tenor_bucket` survives the join until line 195, so it's a one-line swap. The test can't catch this either -- `test_liq_tc.py:140` says "only bucket 1 is exercised by this panel". Worth a second test row in another bucket. Separately, `.drop("_mult", strict=False)` on line 187 is a no-op.

That is three comments:

> Index the multiplier off `_tenor_bucket`, not `tb`. `tb` came from the pre-join frame and polars doesn't guarantee join order.

> Add a test row in a second tenor bucket. With one bucket every row shares a multiplier, so a permutation is invisible.

> `.drop("_mult")` is a no-op. `pl.col(out_col) * mult` keeps the left operand's name, so `_mult` is never a column.

> **Extract this block and test it.** 55 lines of new numerical logic, no test, inside a method measured at 1,154 lines and cyclomatic complexity **175** (up from 163; the class went E35 to E38). The PR quotes "+40.5 bps headline" from this path and `git diff --stat -- src/systematic_credit/tests/` for the range is empty. Move it to `mip/sizing.py` as `base_cap_vector(...)`, returning `(None, {})` for `equal_weight`. Diff to `run` becomes three lines, `run` drops back to ~163.

> Move this block to `mip/sizing.py` and test it there. It's 55 lines of new numerics with no test, and it can't be tested inside `run`.


### Voice

Impersonal and direct. The comment states what is true about the code, not what
the reviewer feels about it.

No `I`, `me`, or `my`. No `we` or `our` speaking for the project -- you have no
standing to say what the project can afford, what it is moving away from, or what
it wishes it had done differently. Where a finding turns on a project decision,
say the decision is needed and stop: "this duplicates `pytensor_ml.optim.base`,
needs a call on which one wins."

No humor, no asides, no personality. No praise, no apology, and no commentary on
the review itself beyond stating where it is incomplete.

Sentence case. Terminal periods optional on fragments. Contractions are fine.

Name code by its identifier, in backticks -- about 40% of comments carry one.
Never substitute a description you coined for a name that exists. No figurative
verbs for what code does. Code does not walk into, reach, bite, sit in a state,
or land in a parquet. It calls, reads, returns, drops, and raises.

American English, and ASCII only. A short comment tempts you into a symbol that
saves three characters and costs the author a font -- write `sum`, not the sigma
glyph, and the same for `>=`, `<=`, `!=`, `->`, `x` for multiplication, `alpha`,
`sigma^2`. Quote a non-ASCII identifier only when that is genuinely its spelling
in the code. `--` for an em dash, used sparingly.

Never soften a real consequence, and never hedge a finding you verified. If a
comment is important enough to post, say it straight.


## Phase 7: submit

**Show the full draft and get explicit authorization before posting.** A review
notifies the author immediately and a `REQUEST_CHANGES` blocks their merge. Show
the teaching comments and the taste comments as their own block, separate from
the rest, and drop any the user does not clear. "Post
the review" in the original request is not standing permission -- show the body,
the comment count, and the event, then wait for a clear go-ahead. This holds even
when you are confident the draft is right.

Anchors must be validated before posting, and a 502 from this endpoint does not
mean the review failed -- retrying blind double-posts every comment. Both are
handled by `scripts/review_payload.py`; `references/posting.md` has the commands
and the two traps. The commonest validation failure is a path shortened to its
basename somewhere in the notes and copied forward; anchors are repo-relative.

## Choosing the event

`REQUEST_CHANGES` when a confirmed finding changes numbers, loses data, or breaks
a caller. `COMMENT` when the findings are shape and conventions -- real work, but
nothing that makes the PR wrong. `APPROVE` is not this skill's job; if the PR is
fine, say so in chat.

Never review your own PR -- GitHub rejects it. Check the author first.
