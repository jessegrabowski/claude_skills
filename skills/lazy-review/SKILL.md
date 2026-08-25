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
and an instruction to cite `file:line` for every claim.

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
plausible, not traced). A suspected finding gets verified before the review, or
it gets dropped. It does not get downgraded into a question -- a question is for
what the code cannot answer, not for a hunch you ran out of time to check.

Sort findings by what they cost:

1. **Changes numbers without crashing.** Silent wrong answers in code someone
   will act on. These are the blockers, and they are why the review exists.
2. **Blocks a fix.** Untestable code, an unimportable module, a 1000-line
   function -- things that make the blockers hard to fix.
3. **Shape.** Files that belong in another PR, committed data, scope creep. Often
   the largest line-count reduction available and the easiest to agree on.
4. **Conventions.** Stated rules broken, at counted sites.

## Phase 6: draft the review

### Which findings become comments

A comment earns its place if the author has to edit a line because of it. Not
"would find useful", not "should know about" -- has to edit. That is a quality
gate, and it is the only gate. There is no comment budget.

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

Lead with the thing that changes the size of the job -- usually the base branch.
Then the blockers as a numbered list, each one line, each ending in its comment
ID. One line means one line: the mechanism, the chain, and the fix are all in the
comment that ID points at, and restating them here writes the review twice and
makes the list unskimmable in the one place it needs to be skimmed. Then the ask
-- what you want the author to do, concretely. For a big PR that is almost always
a split, so give the split as a table of PRs with line counts.

The body is where the length you saved on the comments comes back if you let it.
Anything a comment already carries stays out of it: no repeating a mechanism, no
second copy of a fix, no inventory of what you checked and cleared. If the author
would learn it by opening the comment, it does not belong here.

One sentence on what is working earns its place, because a review that lists only
faults reads as though the whole thing was judged uncharitably and gets
discounted accordingly. One sentence, not a paragraph, and only things you
actually verified.

No headings. No "Summary / Findings / Recommendations" scaffolding. No paragraph
explaining what a good PR would look like.

### Each comment

One sentence saying what to change. A second only when the first does not parse
without it. A code snippet in place of prose whenever the fix is code, and a
measured number whenever you have one. Many comments are one clause and a line
number, and those are the good ones.

Past about forty words, the excess is almost never the finding -- it is one of
the items in the list below, and the list is the thing to check rather than a
word count. Trim there and the comment lands where it should on its own.

Lead with the action as a plain sentence. The failure mode to avoid is a bolded
imperative prefix on every comment -- `**Validate the cached registry.**` reads
as a machine template by the third one, and thirty of them read as a form letter.
Say what to do in an ordinary sentence and stop.

What does not belong in a comment:

- Praise, or a preamble crediting the author before the finding. If the code is
  fine, there is no comment.
- Anything you chased and cleared. It cost you time; it costs the author nothing
  to never hear about it.
- The story of how you found it.
- Your reasoning about severity, or how many other places you checked.
- Restating what the diff plainly shows.
- Unfalsifiable adjectives -- "cleaner", "more robust", "better structured".
  Name the failure or cut the comment.
- Signposting instead of stating -- "worth a look", "keep an eye on", "the
  interesting bit". Name the consequence directly.

A question is a legitimate comment when the code cannot answer it. Ask it
directly, say what turns on the answer, and give the command that settles it.

### Voice

American English. Short declarative sentences. Contractions are fine. Write like
you are telling a colleague what to fix, not filing a report.

Never soften a real consequence with jokey framing, and never hedge a finding you
verified. If a comment is important enough to post, say it straight.

## Phase 7: submit

**Show the full draft and get explicit authorization before posting.** A review
notifies the author immediately and a `REQUEST_CHANGES` blocks their merge. "Post
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
