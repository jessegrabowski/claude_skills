# Templates

Shapes to fill, not forms to submit. Every section stays, because a missing heading reads as an oversight and an empty one reads as an answer -- where there is nothing, write the sentence that says so ("No reverts in the window.") and move on.

Fill every cell from what was actually queried. Never invent a PR number, a date, a review state, or a follow-through verdict; a fabricated row is indistinguishable from a real one to the team reading the PDF, which is what makes it worse than a gap.

**These templates are written unwrapped on purpose -- every paragraph is a single line.** Match that. A newline belongs between paragraphs and list items, never inside a sentence.

---

## OVERVIEW.md

````markdown
---
title: IPM <YYYY-MM-DD>
type: ipm-brief
window: <YYYY-MM-DD>..<YYYY-MM-DD>
generated: <YYYY-MM-DD>
orgs: [pymc-labs, rsamdev]
repos: [<repos with activity in the window>]
previous: <[[IPM_<date>/OVERVIEW]] or "none">
tags: [ipm, team-activity]
---

# IPM <YYYY-MM-DD>

## Scope

<One paragraph: the window and why it ends there, the orgs and repos covered, who has a card and who is counted as cross-team, and what is not in scope. Name the sources -- merged and open pull requests, reviews, GitHub Issues -- and say that pull requests are the primary record.>

## Headline numbers

| | This window | Previous |
|---|---|---|
| PRs merged | <n> | <n> |
| PRs open at close of window | <n> | <n> |
| Reviews given | <n> | <n> |
| Issues created | <n> | <n> |
| Issues closed | <n> | <n> |
| Reverts | <n> | <n> |

<Drop the Previous column entirely on the first brief. Take its numbers from the previous brief's own table rather than re-querying the earlier window.>

## Decisions needed at this meeting

- **<The decision, stated as a question the room can answer.>** <The situation in one or two sentences, with the evidence linked. Who is blocked, or what the deadline is.>

<Only items that need a decision from the room. Work that is merely in progress belongs in the person notes.>

## Follow-through from the previous IPM

| Item from <[[IPM_<date>/OVERVIEW]]> | Status | Evidence |
|---|---|---|
| <the priority or roadblock as it was written then> | Done | <linked PRs or issues that closed it> |
| <...> | Partial | <what landed, and what is still open, both linked> |
| <...> | No motion | <what would have shown motion, and the absence of it> |

<n> done, <n> partial, <n> no motion.

<On the first brief, replace the whole section with: "No previous brief in the vault; follow-through scoring starts with the next IPM.">

## Team activity

![[<lastname>-<YYYY-MM-DD>]]

![[<lastname>-<YYYY-MM-DD>]]

<One embed per card, in roster order, Grabowski last. Blank line between embeds -- Obsidian needs it to render each as a block.>

## Cross-team contributions

- **<Display Name>** (`<handle>`) -- <one line: what they touched in the team's repos, linked.>

## Roadblocks

- **<The blocked work.>** <What is blocking it, how long it has been blocked, and what unblocks it, with the PRs and issues linked.>

<One bullet per blocker. Review bottlenecks, CI-pinned work, changes-requested stalls, approved-but-unmerged drift, and external dependencies all land here. A bullet that names the work without naming the blocker and its age is not an entry.>

## Churn and rework

- **<The pattern.>** <The count, the PRs it covers, and what changed direction, all linked.>

<Scope pivots and what caused them, closed-unmerged work, reverts and what they reverted, the most-contested PRs by review-thread count, streams of same-day self-merged PRs with no review, and work that landed with no issue behind it. Report the pattern and the count; do not diagnose motive.>

## Outstanding requests

Review queue -- non-draft, no approving review, waiting more than three days:

| PR | Author | Age | Waiting on |
|---|---|---|---|
| <[repo#n](url)> | <handle> | <n> days | <handle, team, or "unassigned"> |

Issues created in the window that nobody has started:

| Issue | Author | Created | Assignee |
|---|---|---|---|
| <[repo#n](url)> | <handle> | <YYYY-MM-DD> | <handle or "none"> |

## Priorities for the next iteration

<Paragraphs, one topic each, optionally opening with the topic in bold. Then the argument for it from what this brief established, with the PRs and issues linked inline. Priorities the user stated go first, in their framing. Three to six of them; a list of ten priorities is a list of none, and this is the section where sentences beat bullets because the reasoning is the content.>

## Caveats

- <Anything that failed to query, and what is therefore missing.>
- <Window edges that cut a work stream in half.>
- <Bots excluded from every count.>
- PR and issue counts measure activity, not output; a one-line fix and a subsystem rewrite are one PR each.
- Only `pymc-labs` and `rsamdev` are covered. Work in other orgs, in notebooks outside version control, or in unmerged local branches does not appear.
````

---

## `<lastname>-<YYYY-MM-DD>.md`

````markdown
---
title: <Display Name> -- IPM <YYYY-MM-DD>
type: ipm-person
person: <[[Display Name]] profile note name, or the display name when no profile exists>
handle: <github handle>
window: <YYYY-MM-DD>..<YYYY-MM-DD>
---

## <Display Name>

<[[Display Name]]> -- <n> merged, <n> open, <n> reviews given, <n> issues created, <n> issues closed.

<What the work was about, in the shape of the streams it belongs to rather than PR by PR: a short paragraph when it was one stream, one bullet per stream when it was several. Read the profile note first so continuing work reads as continuing. Name the subsystem, say what changed, link the PRs that carried it. Where a stream is blocked, state the blocker and its age here. No evaluation.>

### Merged

| PR | Title | Merged |
|---|---|---|
| <[repo#n](url)> | <title as written on the PR> | <YYYY-MM-DD> |

### Open

| PR | Title | Opened | Review state | Notes |
|---|---|---|---|---|
| <[repo#n](url)> | <title> | <YYYY-MM-DD> | <approved / changes requested / no review / draft> | <failing CI, stale n days, blocked on X> |

### Issues

<A table when the volume warrants it, otherwise one sentence with the references linked. Created, closed, and commented, marked as such.>
````

<Use `## <Display Name>` as the top heading, not `#`. The note is embedded under OVERVIEW's `## Team activity`, and a second `#` heading breaks the printed document's hierarchy. When a person had no activity: keep the frontmatter, the profile link, and one sentence -- "No merged or open pull requests, reviews, or issue activity in the window." -- and drop the tables.>

---

## `IPM_index.md`

````markdown
# IPM briefs

Iteration planning briefs, newest first. Each folder holds the brief, one note per person, and `IPM_<date>.pdf` -- the whole thing as one file, which is what goes out to the team.

| Meeting | Window | Merged | Open | Notes |
|---|---|---|---|---|
| <[[IPM_<date>/OVERVIEW]]> | <start>..<end> | <n> | <n> | <one clause on what the iteration was about> |
````
