---
name: split-and-commit
description: Split a working tree of uncommitted-but-tracked changes into a series of logically coherent commits, each with a short subject line, without signing as Claude. Use when the user has finished working and wants the diff broken into reviewable, history-friendly commits.
tags: [git, commits, history, workflow]
---

## Purpose

Take a working tree containing uncommitted-but-tracked modifications and produce a clean linear history of small, logically coherent commits. This skill grants **scoped, single-shot commit authority** for the current request only — once the requested commits land, that authority is revoked. Do not interpret successful invocation as a standing permission to commit on later turns.

## Input

$ARGUMENTS

## Hard rules

- **Do not sign commits as Claude.** No `Co-Authored-By: Claude` trailer, no `Generated with Claude Code` line, no signing trailer of any kind unless the user explicitly types it.
- **Subject lines stay under 80 characters.** Aim for 50–72; hard cap at 79. Imperative mood ("Add", "Fix", "Refactor"), no trailing period.
- **Subject-only by default.** See *Commit message style* — the bar for adding a body is high, and it is the rule this skill most often gets wrong.
- **One logical change per commit.** If a single file contains multiple unrelated edits, disentangle before committing — never commit a messy file just because it would be convenient.
- **Tracked modifications only.** Untracked files are out of scope unless the user explicitly names them. Surface them in your report so the user can decide.
- **No destructive git operations.** No `reset --hard`, no `push --force`, no rebase, no amend, no `clean -f`. The work should be addable, splittable, and undoable via plain `git reset HEAD~N`.
- **Don't push.** Commits stay local until the user asks.
- **Don't skip hooks or signing.** No `--no-verify`, no `--no-gpg-sign`. If a hook blocks the commit, fix the underlying issue.

## Step-by-step procedure

### 1. Survey the working tree

Run these in parallel before doing anything else:

```bash
git status --short        # what's modified, staged, untracked
git diff                  # unstaged tracked changes
git diff --cached         # already-staged changes (warn if non-empty)
git log --oneline -10     # learn the project's commit-message style
```

Separate what *this session* produced from pre-existing noise — `.DS_Store`, unrelated untracked files, leftover scratch, a stale index from an earlier session. Don't sweep up files the user didn't ask you to touch.

If `git diff --cached` is non-empty, stop and ask: include the staged content in the first commit, or unstage it and treat the whole tree uniformly? Don't silently roll forward — staged content reflects an intent the user already had. Never `git reset` a dirty index without asking; you'd be discarding that intent.

If the repo isn't on a feature branch (e.g. on `main`/`master`), confirm the user wants commits there before proceeding. Once they've confirmed for this repo in this session, that answer holds — don't re-ask on every invocation.

### 2. Read the diffs and identify logical groups

Group hunks by **what they accomplish together**, not by file or by the order you happened to write them. A unit is a self-contained change a reviewer can evaluate on its own:

- "Bug fix in X" — even if it touches 4 files.
- "Refactor: extract Y helper" — file move plus caller updates.
- "Add tests for Z" — new test file plus minor fixture tweak. A new helper module and its tests are one commit, not two.
- "Style cleanup" — typos, dead imports, formatting, only if genuinely independent.
- "Docstring updates" — when prose-only and unrelated to logic.
- Pure renames go in their own commit so reviewers can use `--follow`.

Two constraints on the grouping:

- **Dependency direction.** Primitives first, consumers second. If commit B imports what commit A adds, A lands first.
- **Reversibility.** Each commit, checked out alone, should leave the tree buildable. Don't strand half-implementations.

Group **against** organising by:

- File — a file with mixed concerns must be split (see §3).
- Chronology of when you wrote each piece; that's noise to a reviewer.
- Size — five small unrelated changes are five commits, not one "misc" commit. Conversely, don't manufacture splits to look productive, and fold trivial fixups into the parent commit rather than emitting them separately.

If the diff genuinely doesn't cleave — a single tightly-coupled refactor where every hunk is needed for correctness, or a rewrite of one file — say so and propose one commit, with the reasoning. One honest commit beats a fake split.

**State the plan before you execute it.** Commit count and a one-line title for each, in chat, so the user can redirect before anything lands. For a single-commit plan one sentence is enough; don't turn this into a ceremony.

### 3. Disentangle messy files

A "messy" file is one whose hunks belong to multiple logical commits.

The reliable technique, and the default: **write the intermediate state of the file to disk explicitly.** Produce the version of the file as it should look after commit 1, stage and commit it, then write the next state and continue. This is far more dependable than trying to drive a patch-selection UI, and it produces exactly the per-commit diffs you intended.

`git add -p` and `git restore --patch` are interactive and cannot be driven from a non-interactive shell — do not reach for them, and never try to script an answer stream into one. `git stash --keep-index` is available as a fallback when you need the unstaged remainder parked while you commit and verify, but the write-the-state approach usually makes it unnecessary.

If you genuinely can't tell which lines belong to which group, say so and stop. Don't guess. Offer to walk the file with the user so they can label the hunks, or hand it back for them to split by hand.

Never commit a file with hunks belonging to two different logical changes just because splitting them was tedious. That defeats the entire point of this skill.

### 4. Choose commit order

Order matters for `git bisect` and for review. Prefer:

1. **Pure refactors and renames first** (no behavioural change).
2. **Bug fixes** before features that depend on them.
3. **Tests** alongside or just after the code they cover — not a giant tail-end "tests" commit, unless the tests really were the only late addition.
4. **Doc/comment-only changes last**, unless they're load-bearing for understanding the earlier commits.

If a fast smoke check exists (`pytest -x` on the touched module, `tsc --noEmit`, `cargo check`), run it after each commit. If a commit broke something, stop and investigate before continuing.

### 5. Write the commit messages

**The default is a subject line and nothing else.** This is the rule most often violated, and the failure is always the same: a body that restates the diff in prose.

- Subject under 80 chars (aim 50–72), imperative mood — "Add X", not "Added X" or "Adds X" — no trailing period.
- **Concrete subjects.** "Add windowed gradient mass matrix adapter" beats "Update mass matrix". Name the thing that changed.
- Match the **observed style** from `git log --oneline -10`: casing, Conventional Commits (`fix:`, `feat:`), ticket or area prefixes (`PROJ-123:`, `[parser]`), past tense if that's the house style. Include a ticket reference when you have one; never invent one.
- **Add a body only when the *why* is invisible in the diff** — a non-obvious constraint, a subtle reason for the approach — or when the user asks for one. "The diff is large" is not a reason. "The change is important" is not a reason. If you can't name the specific thing a reader couldn't infer from the diff itself, there is no body.
- **When a body is warranted, it is one or two short sentences.** Not a paragraph, not bullets summarizing the change, not a narrative of how you got there. If you've written more than two sentences, you've overwritten it — cut it back or drop it entirely.
- **Never hard-wrap the body.** One paragraph is one line, however long; the terminal and the web UI wrap it. Blank lines separate paragraphs, and deliberately structured content — lists, tables, aligned columns — keeps its own linebreaks.
- **No Claude signature, no co-author trailer, no "Generated with…" line.** Repeat: no signature.

Single-line messages take plain `-m`. Use a heredoc only when there's a body:

```bash
git commit -m "$(cat <<'EOF'
Subject under 80 chars

The one non-obvious thing a reader couldn't get from the diff.
EOF
)"
```

### 6. Stage, verify, commit, repeat

For each planned commit:

1. Stage exactly what belongs to it — `git add <files>` when every hunk of a file belongs to this commit, otherwise the write-the-state approach from §3.
2. `git diff --cached --stat` — confirm the staged set matches your intent.
3. `git diff` — confirm the leftover working tree is what you expect.
4. Commit.
5. `git status --short` — confirm it landed and the residual diff is right.

Then move to the next. After the last one:

```bash
git log --oneline <baseline>..HEAD     # show what you produced
git status --short                     # confirm clean, or expected leftovers
```

### 7. Handle pre-commit hooks

- **Reformatters** (ruff format, black, prettier): the hook rewrites files and aborts the commit. Re-stage the now-formatted file and re-commit. Check that the reformat didn't pull in changes belonging to a later commit.
- **Lint failures**: read the error, fix the underlying issue in the code, re-stage, re-commit. Don't bypass.
- **Branch protection** (`no-commit-to-branch` or similar): **stop.** Tell the user the branch is protected and ask where to commit. Do not unilaterally create or switch branches.
- **Anything else**: investigate and fix the root cause. If you can't, stop and report — never `--no-verify`.

### 8. Report

- The commits you made, one line each.
- Anything left in the working tree that you deliberately didn't commit, with a one-line reason each ("pre-existing untracked, not mine"; "blocked by branch protection").
- Any file you had to touch beyond the diff — a lint fix outside your changes, a reformat — so the user knows.

Keep it proportionate: a two-commit split doesn't need a section-by-section writeup of your reasoning.

## Edge cases

- **Files with secrets** — `.env`, `credentials.json`, anything dotfile-ish holding keys. Stop and warn explicitly. Never commit by default, even if the user named the file generally.
- **Generated or build artifacts** in the diff: don't commit them. Suggest a `.gitignore` entry as its own commit if appropriate.
- **Whitespace-only or trailing-newline-only diffs**: bundle into a single "Whitespace cleanup" commit if there's no logical home. Don't pad real commits with them.
- **Detached HEAD or unusual branch state**: stop and confirm — the consequences differ from a normal branch.
- **Files whose origin is unclear**, or that you didn't introduce: ask before including them.

Stopping politely is always better than committing the wrong thing.

## What success looks like

- A clean linear sequence of commits, each one a thing you'd be happy to see in a `git blame`.
- Every subject line readable on a phone screen, under 80 chars.
- Messages terse — subject-only almost always, a body only where the *why* is genuinely invisible.
- No signatures, no co-author trailers, no "Generated by…" lines.
- Working tree clean, or holding only what the user chose to leave behind, with those items listed in the report.
- `git reset HEAD~N` puts the user exactly where they started.

## Authority

Commit authority is **scoped to this single invocation**. It covers exactly the commits requested now and expires the moment they land. It does not carry to the next turn, the next request, or the rest of the session.

- Producing a successful split does **not** generalize to "I can commit going forward."
- A later request to change code is **not** a request to commit it. Make the edits and stop.
- Every subsequent commit — including an amend, a follow-up fix, or re-running this skill — needs a fresh, explicit instruction from the user.

When in doubt, make the changes and leave them uncommitted for the user to review.
