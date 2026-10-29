---
name: clean-archive
description: Sweeps the Obsidian vault for finished artifacts left by fresh-review, lazy-review, plan-scaffold and ipm-prep, checks them against GitHub PR state, and moves them into the vault archive. Plans are updated and archived only after one approval.
disable-model-invocation: true
argument-hint: "[repo or project name to limit the sweep]"
---

# clean-archive

The vault fills with artifacts whose work is over: reviews of merged PRs, plans whose last PR landed weeks ago, old IPM briefs. Each one stays searchable and linked after it moves to the archive, so moving it costs nothing, and leaving it costs attention every time the vault is searched. This skill finds what is finished by asking GitHub, the source of truth, never the checkboxes and status lines in the notes, which go stale.

## Input

$ARGUMENTS

With no argument, sweep every repo and project. With a name, sweep only `Reviews/<name>/` and `Projects/<name>/`, and skip the IPM step.

## 1. Locate the roots

Read `<review-root>` and `<review-archive>` from `CLAUDE.local.md`. If either is unset, ask once. The vault is the ancestor of `<review-root>` that contains `.obsidian/`. The other roots follow from it:

```
<vault>/Projects/<project>/<plan-name>/OVERVIEW.md     plan-scaffold plans
<vault>/Project Management/IPM_<YYYY-MM-DD>/           ipm-prep briefs
<vault>/Archive/<path below the vault root>            where everything moves
```

An archived artifact keeps its path below the vault root, so `Projects/pymc-models/foo/` goes to `Archive/Projects/pymc-models/foo/`. Never overwrite anything already in the archive. Stop and report a collision.

Every `gh` and `git` call in this skill is read-only, and each runs as a single command so the user's allow rules match it. No `git fetch`, no `git pull`, no checkout: PR state comes from `gh`, which needs no local refs.

## 2. Reviews: move without asking

Apply the rule in `../lazy-review/references/artifacts.md` ("Archiving older reviews") to every `<review-root>/<repo>/` folder in scope. Take `<owner/name>` from each review's `00_brief.md` or `00_scope.md`. Look up each distinct PR once and reuse the answer for every folder that names it. A stack folder (`Stack_<first>-<last>_...`) is finished when every PR in the range that exists is merged or closed.

Move the finished folders, delete repo folders left empty, and keep the list of what moved for the report. Done when every folder in scope has a PR state, a "no PR" verdict, or a stated reason it could not be looked up.

## 3. IPM briefs: keep the two most recent

Sort the `Project Management/IPM_<YYYY-MM-DD>/` folders by date and move all but the two newest to `Archive/Project Management/`. The newest is the current brief and the second is the one it scores follow-through against, which ipm-prep reads on its next run. `IPM_index.md` stays where it is, and its wikilinks keep resolving after the move.

## 4. Plans: survey, propose, apply on approval

Every `OVERVIEW.md` under `<vault>/Projects/` is a plan. Survey each one to settle three things:

- **Verdict.** DONE when every PR the plan calls for is merged or closed with the work landed elsewhere, or when the plan's own text says it was dropped or replaced. ACTIVE when any planned PR is open or not yet opened. UNCLEAR when the plan does not name its PRs well enough to tell, with what is missing. A plan whose frontmatter already says `done`, `abandoned` or `superseded` is DONE.
- **Stale rows.** Every `☐` in a step's commit table, or in a PR-level `merged` line, whose PR is merged.
- **Evidence.** The PR numbers and states behind the verdict, in one clause.

Find the PRs from the step files' PR tables and from PR numbers, pull URLs and branch names in the text. The frontmatter `repo:` gives the default repo, and a plan can name PRs in other repos. With more than about ten plans, fan the survey out to read-only subagents, about twelve plans each, and give each the verdict rules above, the repo, and the instruction that no file, git or gh write is allowed.

Present one proposal and wait for approval:

1. Plans to archive, each with its verdict evidence and the `status:` it gets: `done`, `abandoned` or `superseded`. The last two carry a one-line `status_reason:` taken from the evidence.
2. Rows to tick, counted per plan.
3. Plans that look stalled, with a one-line reason and no proposed change: no PR activity in a month, or every remaining PR unopened. These are the user's call. Archive any that the user names.

ACTIVE plans with no stale rows do not appear. The survey is done when every plan in scope has a verdict.

On approval, apply the whole batch. Tick the approved rows. For each plan to archive, set `status:` (adding frontmatter when the OVERVIEW has none), follow the archiving steps in `../plan-scaffold/SKILL.md` ("Archiving"), and rewrite the trailing status phrase of the plan's README line to match its new status.

## 5. Fix links and report

Grep the vault for wikilinks written from the vault root (`[[Projects/...`, `[[Reviews/...`, `[[Project Management/IPM_...`) that point at a moved path, and prefix them with `Archive/`. Partial-path links such as `[[foo/OVERVIEW]]` keep resolving and need no change. Done when that grep finds no link to a pre-move path.

Report in this order: reviews moved and reviews kept (open PR, no PR, lookup failed), IPM folders moved, plans archived and rows ticked, plans left for the user's call. Name anything a lookup could not answer.
