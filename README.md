# Claude Skills

Skills I personally find useful. No nerds allowed.

Code quality, review, planning, and security-audit skills for
[Claude Code](https://claude.com/claude-code), synced across machines via this
repo.

## Contents

Entry points, invoked directly:

- `code-review` -- honest review that reports findings without touching files
- `improve-code` -- standards and professionalism pass, applied in place
- `improve-tests` -- test quality and coverage audit
- `plan-scaffold` -- scaffold a step/PR/commit implementation plan in the Obsidian vault
- `split-and-commit` -- break working changes into logical commits
- `issue` / `lazy-pr` -- file a GitHub issue or open a PR

The remaining directories are focused analysis skills that the entry points
above delegate to: security (`initial-security-analysis`, `input-validation`,
`authentication-flow-review`, `secrets-management-audit`, ...), design
(`solid-principles`, `design-pattern-implementation`, `code-duplication-detection`,
...), and reliability (`error-handling-resilience`, `exception-flow-analysis`, ...).

## Install

Clone, then symlink the entry-point skills into `~/.claude/skills/`:

```sh
git clone git@github.com:jessegrabowski/claude_skills.git ~/Documents/Python/claude_skills

REPO=~/Documents/Python/claude_skills
mkdir -p ~/.claude/skills

for name in code-review improve-code improve-tests plan-scaffold split-and-commit issue lazy-pr; do
    src="$REPO/skills/$name"
    dest=~/.claude/skills/"$name"
    [ -d "$src" ] || { echo "not in repo, skipping: $name"; continue; }
    if [ -e "$dest" ] && [ ! -L "$dest" ]; then
        echo "already a real directory, skipping: $name"
        continue
    fi
    ln -sfn "$src" "$dest" && echo "linked: $name"
done
```

Set `REPO` to wherever the clone actually landed — the symlinks encode that path,
and `ln` will not warn you if it doesn't exist.

Per-skill symlinks rather than one on `~/.claude/skills` itself, so machine-local
skills can live alongside the synced ones. Restart Claude Code afterward to pick
them up.

Three things the loop is deliberately doing:

- **Only the entry points get linked.** The delegated analysis skills are reached
  through those, not invoked directly, so linking all of them just crowds the skill
  list with near-miss descriptions for the trigger matcher to sort through.
- **An existing real directory is never touched.** `ln -sfn` against a real directory
  silently creates the link *inside* it (`~/.claude/skills/improve-code/improve-code`)
  rather than replacing it, so the loop skips those and tells you. To convert one,
  confirm the repo copy is current, remove the real directory, and re-run. An existing
  *symlink* is replaced normally, so re-running after a move is safe.
- **The clone becomes live config.** Once linked, a `git checkout`, branch switch, or
  rebase changes the skills in every running Claude Code session. That's the point —
  edit either path and both see it — but it means the repo is no longer inert.
