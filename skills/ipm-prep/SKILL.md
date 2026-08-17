---
name: ipm-prep
description: >-
  Assemble the iteration planning meeting (IPM) brief -- two weeks of GitHub activity across the modeling
  team's repos, broken down by person, with follow-through on the previous IPM, roadblocks, rework, and
  outstanding requests -- written into the Obsidian vault as a linked note set that exports to one PDF.
  Use when asked to prep an IPM, prep iteration planning, or put together a sprint review.
---

# IPM prep

Produce the complete record of what the team did in the last two weeks, organized so the meeting can be spent deciding rather than reconstructing. The brief is distributed to the team as a single PDF before the meeting, so it is read by the people it describes: every claim in it has to be attributable to a PR, an issue, or a commit, and nothing in it evaluates a person.

Coverage is the point. A section left thin because the data was tedious to gather is a section the meeting will have to fill from memory, which is exactly what this replaces. Where a source genuinely had nothing, say so explicitly rather than omitting the heading.

## Input

$ARGUMENTS

Expected: nothing, or a window override, or priorities the user wants carried to the top. The default window is the two weeks ending today. Meeting-specific context the user supplies in conversation -- a topic they want covered, a decision they want teed up -- goes into the brief; it does not replace the systematic pass.

## Deliverable

A note folder in the Obsidian vault at `~/Documents/systematic_credit/`:

```
Project Management/
├── IPM_index.md                  running list of every brief, newest first
└── IPM_<YYYY-MM-DD>/
    ├── OVERVIEW.md               the brief; embeds every person note
    ├── <lastname>-<YYYY-MM-DD>.md    one per person with a card
    ├── ...
    └── IPM_<YYYY-MM-DD>.pdf      the whole brief as one file, for distribution
```

`OVERVIEW.md` is the document. It carries every narrative section and pulls the per-person detail inline with Obsidian embeds (`![[fengler-2026-08-17]]`), so *Export to PDF* from `OVERVIEW.md` renders the whole brief as one file with no assembly step. Person notes are separate so the tables do not bury the sections that drive the meeting, and so each one can be read on its own from search or from the person's profile backlinks.

Person note names carry the date (`fengler-2026-08-17.md`) to stay unique across the vault -- an embed of a bare `[[fengler]]` becomes ambiguous the second time this skill runs.

Use the templates in `references/templates.md`; read that file before writing anything.

## Writing for the vault, not for a terminal

**Never hard-wrap prose.** One paragraph is one long line however far it runs, and the editor soft-wraps it. Blank lines between paragraphs, list items, and headings are structure and belong; a newline inside a sentence never does. This applies to table cells, which break badly when split.

ASCII only, American English, no LaTeX. These notes are read in Obsidian and printed to PDF, so `>=`, `->`, and `--` stay as written.

## Voice

Write for a technical reader who will check the claims -- the register of a status memo, not a newsletter. Plain declarative sentences, specific nouns, and a link for every fact.

What that rules out, concretely:

- **No evaluation of people.** Report what was merged, opened, reviewed, and blocked. "Landed the PDE teacher and the synthetic-data engine" is the brief's job; "strong two weeks" and "still no tests" are not. The one exception is a blocker attached to a person's work, which is stated as the blocker rather than as a shortfall: "waiting on review since the 6th", not "slow to follow up".
- **No inflation.** Nothing is major, significant, substantial, or a milestone. A 40-file PR is a 40-file PR. Drop the adjective and give the number.
- **No signposting.** Never write "worth a close look", "the interesting bit", "keep an eye on", or "one thing to watch". Name the thing and its consequence in the same sentence, so the reader gets the substance instead of a promise of substance.
- **No cute framing.** No "one wrinkle", "small gotcha", "fun catch". A caveat that blocks work or forces a decision is stated flatly as what it is.
- **No blog or forum register.** No rhetorical questions, no second-person address, no "let's", no emoji, no bolded key-phrases scattered mid-sentence.
- **No hedging.** State what the data shows. Where the data is incomplete, that belongs in Caveats as a fact about coverage, not as a qualifier smeared across every sentence.
- **No first person, and no narration of the gathering.** The brief describes the iteration, not the process that produced the brief.

Bullets are the right form for most of this brief and are used freely: the sections that enumerate discrete items -- decisions needed, roadblocks, churn findings, cross-team contributions, caveats -- read faster as a list than as a paragraph, and a bold lead-in naming the item is fine there. A reader scanning the brief ten minutes before the meeting needs to find one entry, not follow an argument. Tables carry anything genuinely tabular: PR lists, follow-through scoring, headline counts, the review queue.

Two places want sentences. A bullet still has to be a claim with its evidence attached, so an entry reading "PDE calibration -- blocked" is not a bullet, it is a heading with nothing under it: name what is blocked, by what, for how long. And the priorities section stays paragraphs, because the argument for a priority is what makes it one -- a bold topic lead is welcome, but what follows it carries the reasoning in full sentences rather than collapsing to a list of nouns.

## Scope: the team and the repos

The engineering team, from `Project Management/Personnel/_index.md`:

| Person | Handle | Profile note |
|---|---|---|
| Alexander Fengler | `AlexanderFengler` | `[[Alexander Fengler]]` |
| Camilo Saldarriaga | `CamSalda` | `[[Camilo Saldarriaga]]` |
| Purna Chandra Mansingh | `purna135` | `[[Purna Chandra Mansingh]]` |
| Francesco Muia | `fmuia` | `[[Francesco Muia]]` |
| Jesse Grabowski | `jessegrabowski` | `[[Jesse Grabowski]]` |

Every one of the five gets a card, including anyone with no activity in the window -- an empty card that says so is information, and a missing card reads as an oversight.

**Active PyMC Labs contributors also get full cards.** Anyone outside the five with a merged PR in the window in a repo the modeling team owns is a member for this brief's purposes: `tomicapretto`, `OriolAbril`, `symeneses`, `bwengals`, `williambdean`, `HangenYuu`, `amaloney` and whoever else appears. Resolve their display name with `gh api users/<login> --jq .name` rather than guessing it, and fall back to the login when the field is empty. Card order is alphabetical by last name, with Grabowski last.

**Cross-team contributors get one line each** under *Cross-team contributions*, not a card: the rsamdev platform and app engineers (`mlineen`, `benkimpel`, `goldjacob29`, `novireadyx`, `jmayes-rx`, `akoortrdyx`, `nickschneiderrdx`, `bojanpetrovic`, `PaulMcintyre01`, `jedwards-rdy`, `dbgrossmX`) and any other outside account. Bots (`dependabot[bot]` and friends) are excluded entirely; note the count in Caveats if it was large enough to distort a repo's totals.

**The repo set is discovered, not fixed.** Two orgs are in scope -- `pymc-labs` and `rsamdev` -- and the covered repos are whichever ones a rostered person touched in the window. `pymc-labs/readystate` is the modeling monorepo and dominates; `rsamdev` holds `pymc-models`, `pymc-dashboard`, `dagster-pymc-assets`, `caspar`, `rx-data-py`, `rx-ai` and many repos belonging to other teams. Never enumerate repos from a hardcoded list, and never read activity out of the local clones in `~/Python/` -- they go stale silently.

## Sources

**GitHub, via `gh`** (authenticated as `jessegrabowski`), across both orgs. Pull requests are the primary record of what happened; GitHub Issues are the tracker.

**The previous brief.** Before gathering, find the most recent `Project Management/IPM_*/OVERVIEW.md` dated before this one and read it. Its priorities section and its roadblocks are what the follow-through table scores. If there is no previous brief, say so in that section and skip the tally rather than inventing a baseline.

There is no Linear and no AppSignal in scope. If the user asks for either, say it is not part of this brief and needs its MCP connected at session start.

## Gathering

Run one agent per rostered person, in parallel, plus one repo-level agent. Every agent returns raw data -- reference, title, date, URL, state -- and no prose.

**Per-person agent.** Window bounds as `<start>..<end>`, both `YYYY-MM-DD`:

```
gh search prs --owner rsamdev --owner pymc-labs --author <u> --merged merged:<start>..<end> \
  --limit 100 --json repository,number,title,closedAt,url
gh search prs --owner rsamdev --owner pymc-labs --author <u> --state open \
  --limit 100 --json repository,number,title,createdAt,updatedAt,isDraft,url
gh search prs --owner rsamdev --owner pymc-labs --reviewed-by <u> --updated <start>..<end> \
  --limit 100 --json repository,number,title,author,url
gh search issues --owner rsamdev --owner pymc-labs --author <u> --created <start>..<end> --limit 100 --json repository,number,title,state,url
gh search issues --owner rsamdev --owner pymc-labs --assignee <u> --state open --limit 100 --json repository,number,title,createdAt,url
gh search issues --owner rsamdev --owner pymc-labs --involves <u> --updated <start>..<end> --limit 100 --json repository,number,title,state,url
```

Two search quirks that cost a rerun each time they are forgotten: `mergedAt` is not a valid `--json` field for search, so read the merge date from `closedAt`; and the `merged:<range>` qualifier is a positional argument, not a value for `--merged`, which is a bare flag.

Then per open PR, the state a reviewer would see: `gh pr view <n> --repo <r> --json reviewDecision,isDraft,createdAt,updatedAt,additions,deletions,reviews,comments,statusCheckRollup` and `gh pr checks <n> --repo <r>`.

**Repo-level agent.** Over the repos surfaced above: PRs closed unmerged, reverts (`gh search commits`, or revert titles), force-pushed or reopened PRs, PRs merged the same day they opened with no review, size outliers, review-thread counts on the most-discussed PRs, and issues closed as not-planned. Also the review queue: non-draft open PRs with no approving review, aged in days.

Attribute work by **commit log, not PR author**, when the two differ -- shared branches and hand-offs are common in `readystate`, and the PR author is whoever pressed the button.

## OVERVIEW sections

In this order. Cut none of them; where a section is empty, one sentence says so.

1. **Frontmatter and title** -- see the template. Window, sources, generated date, tags.
2. **Scope** -- one paragraph: the window, the orgs and repos covered, who is counted, and what is not in scope.
3. **Headline numbers** -- table: PRs merged, PRs open, reviews given, issues created, issues closed, reverts. Add a previous-window column when a previous brief exists, and take those numbers from that brief rather than re-querying.
4. **Decisions needed at this meeting** -- only items that need a decision from the room, each with the decision stated as a question and the evidence linked. Hard deadlines and anyone blocked right now go here.
5. **Follow-through from the previous IPM** -- table: item, status (Done / Partial / No motion), evidence with links. Close with the tally.
6. **Team activity** -- the embeds, one per card, in roster order.
7. **Cross-team contributions** -- one line per outside contributor.
8. **Roadblocks** -- review bottlenecks, CI-pinned work, changes-requested stalls, approved-but-unmerged drift, external dependencies. Each with the link and the age.
9. **Churn and rework** -- scope pivots, closed-unmerged work, reverts, the most-contested PRs, unreviewed rapid-iteration streams, and work that landed with no issue behind it.
10. **Outstanding requests** -- the review queue (non-draft, waiting more than three days: PR, author, age, waiting on whom) and issues created in the window that nobody has started.
11. **Priorities for the next iteration** -- paragraphs, one topic each, opening with the topic in plain terms and carrying the evidence and links inline. Priorities the user stated go first. This is the only section that argues rather than reports, and it argues from what the rest of the brief established.
12. **Caveats** -- what the data cannot show. Anything that failed to query, any window edge that cuts a work stream in half, bots excluded, and the standing limits: PR counts are not output, and repos outside the two orgs are invisible.

## Person notes

Each carries frontmatter, a wikilink to the profile note in `Project Management/Personnel/`, a summary of the work by stream -- a paragraph for one stream, a bullet per stream for several -- and the tables. Read the profile before writing the paragraph -- it says what the person owns, which is what makes "landed the converter rewrite" legible as continuing work rather than a one-off.

The merged-PR table has an identical shape in every person note: reference, title, date, and nothing else. If one person's table is long, it stays a table; do not summarize one person's PRs while enumerating another's. Open PRs get their own table with review state and age. Issues get a short table or a sentence, whichever the volume warrants.

## Links

Everything links. `[readystate#2406](https://github.com/pymc-labs/readystate/pull/2406)`, `[pymc-models#324](https://github.com/rsamdev/pymc-models/pull/324)`. Issues use `/issues/<n>`. Repo-qualify the reference text whenever a section spans repos, which is most of them.

**Full identifiers, never merged shorthand.** Write `#2389, #2390, #2391`, never `#2389/90/91`, and give every member of a list its own link. A range collapsed for brevity is a reference the reader cannot click.

Markdown links, not wikilinks, for anything on GitHub. Wikilinks are for vault notes: the person profiles, the previous brief, and any plan folder under `Projects/` the work belongs to. Linking an active plan's `OVERVIEW` when the iteration's work advanced it is worth doing -- it connects the meeting record to the plan it moves.

## Assembly and distribution

**The PDF is part of the deliverable, not an optional extra.** The brief goes out to the team as one file before the meeting, so the last step of every run is:

```
python scripts/assemble.py "<vault>/Project Management/IPM_<date>/OVERVIEW.md"
```

That writes `IPM_<date>.pdf` into the same folder as the notes it was built from, which is where the rest of the meeting's material already lives. It inlines each embed, demotes the embedded headings one level, strips the person notes' frontmatter, and reduces remaining wikilinks to plain text so they do not print as `[[...]]`. The flattened markdown is a temporary intermediate and is discarded; pass `--keep-markdown <path>` only if something downstream needs it. Rendering is landscape at 9pt by default, because full PR titles beside a URL column overflow a portrait LaTeX page; `--portrait` switches back. The engine is pandoc with tectonic, which is what is installed on this machine.

Running it also verifies the embeds: a target that does not resolve is reported and exits non-zero rather than being silently dropped, so a typo in a person note's filename surfaces here instead of as a hole in the PDF.

Where a PR title is long enough to overflow even landscape, pandoc reports an out-of-page-boundary warning. That is cosmetic and affects a row or two; if the clipping matters for a particular brief, *Export to PDF* from Obsidian on `OVERVIEW.md` wraps table cells instead, and produces the same document.

## Verification before handing back

- Every rostered person has a card, and every card's embed resolves in `assemble.py`.
- `IPM_<date>.pdf` exists in the folder and carries every card. The run is not finished without it.
- Zero unlinked PR or issue references, and no collapsed ranges. Grep the written files for `#\d` and check each hit is inside a link. Two hits are allowed: a reference inside a verbatim PR title, which stays as the author wrote it and must be linked elsewhere in the same note, and a numeric span describing a bulk action ("issue numbers 11 to 116"), which is a count rather than a set of references and is written without the `#`.
- Every section present, with an explicit sentence where a section is empty.
- No hard-wrapped paragraphs. Check against the files, not from memory -- wrapping creeps back in around the middle of a long document.
- ASCII everywhere the brief speaks in its own voice. A verbatim PR title or a person's name keeps its real spelling; convert the HTML entities the `gh` JSON output carries (`&amp;`, `&lt;`, `&gt;`) back to their characters, since those are an artifact of the transport and not what the author typed.
- `IPM_index.md` updated with this brief, newest first.
- Nothing evaluative about a person survived into the prose.

## Handing it back

Say where the folder landed, give the headline numbers in a sentence or two, name the decisions the brief is teeing up, and list anything a source could not answer. Do not restate the brief -- the user is about to read it.
