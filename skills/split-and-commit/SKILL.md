---
name: split-and-commit
description: Break the current working changes into a series of logical, well-scoped git commits. Use when the user asks you to commit your work, split a diff into commits, or organize uncommitted work for review.
---

You are committing work that you (or this conversation) just produced. The user has asked for clean, logical commits — not a single dump, not micro-commits. Treat this as a one-time grant of commit authority: when this turn's work is committed, you do **not** have authority to commit again without re-authorization.

## Input

$ARGUMENTS

## Hard rules

- **Subject line ≤ 79 characters.** No body unless the user asks for one.
- **No Claude attribution.** No `Co-Authored-By: Claude…`, no "🤖 Generated with…", no signature footers.
- **Never bypass safety.** No `--no-verify`, no `--no-gpg-sign`, no `git reset --hard`, no force-push. If a hook blocks the commit, fix the underlying issue.
- **Never push** unless the user explicitly asks.
- **One-time authority.** Once this turn's commits land, do not commit again without re-authorization.
- **Split partial files when needed.** If one file's diff spans multiple logical commits, split it. Mixing two unrelated changes in one commit is messy and unacceptable.

## Workflow

### 1. Survey

Before staging anything:

- `git status -s` — what's actually changed. Identify what *you* introduced versus pre-existing noise (`.DS_Store`, unrelated untracked files, leftover scratch). Don't sweep up files the user didn't ask you to touch.
- `git diff` and `git diff --staged` — what each change actually does.
- `git log -5 --oneline` — match the repo's tone: imperative or past tense, lowercase or sentence case, any ticket/scope prefix conventions.

If the index is dirty from a prior session and doesn't reflect the current diff, `git reset` to clear staging and start deliberately.

### 2. Plan the split

Identify logical units. A unit is a self-contained change a reviewer can evaluate on its own. Group by:

- **Capability** — a new helper module + its tests is one commit, not two.
- **Dependency direction** — primitives first, consumers second. If commit B imports from commit A, A must land first.
- **Reversibility** — each commit, checked out alone, should leave the tree buildable. Don't strand half-implementations.

Avoid:

- One commit spanning two unrelated features.
- A commit that doesn't make sense without a later one.
- Trivial fixup commits — fold them into the parent.

State the plan (commit count, brief title for each) in chat **before** committing, so the user can redirect.

### 3. Stage and commit

For each planned commit:

1. Stage exactly the files (and lines) that belong to it.
2. Commit with a ≤ 79-char imperative subject.
3. Verify with `git log -1 --oneline`.

When a single file's diff spans multiple commits, **write the intermediate state of that file to disk explicitly**, stage and commit, then overwrite with the next state and continue. This is far more reliable than scripting `git add -p` and produces clean per-commit diffs.

### 4. Handle pre-commit hooks

- **Reformatters** (ruff format, black, prettier): the hook modifies files and aborts. Re-stage the now-formatted file and re-commit.
- **Lint failures**: read the error, fix the underlying issue in code, re-stage, re-commit. Don't bypass.
- **Branch protection** (`no-commit-to-branch` or similar): **stop**. Tell the user the branch is protected and ask whether to create a feature branch or where to commit. Do not unilaterally create branches or change branches.
- **Other failing hooks**: investigate and fix the root cause. If you can't, stop and report.

### 5. Report

After the last commit, output:

- The commits you made (`git log <baseline>..HEAD --oneline`).
- Anything still in the working tree that you deliberately did not commit, with a one-line reason each (e.g. "pre-existing untracked, not mine"; "blocked by branch protection").
- Any files that needed pre-existing fixes (e.g. lint cleanups outside the diff) so the user knows they were touched.

## Commit message style

- **Imperative mood.** "Add X", not "Added X" or "Adds X".
- **Concrete subjects.** "Add windowed gradient mass matrix adapter" beats "Update mass matrix".
- **Match repo conventions** seen in `git log` — casing, ticket prefixes (`[area]`, `feat:`, etc.), past-tense if that's the house style.
- **One line.** No body unless the user asks.
- **≤ 79 characters** including any prefix.

## Stop and ask when

- Branch protection blocks a commit.
- The diff genuinely doesn't cleave — one change touches many files in ways that resist splitting; ask whether to bundle or push back.
- You'd need to commit files whose origin is unclear or that you didn't introduce.
- You'd need to push, force-push, amend a published commit, or otherwise act outside this turn's authority.

Stopping politely is always better than committing the wrong thing.
