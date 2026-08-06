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

Clone, then symlink each skill into `~/.claude/skills/`:

```sh
git clone git@github.com:jessegrabowski/claude_skills.git ~/Python/claude_skills

mkdir -p ~/.claude/skills
for d in ~/Python/claude_skills/skills/*/; do
    ln -sfn "$d" ~/.claude/skills/"$(basename "$d")"
done
```

Per-skill symlinks rather than one on `~/.claude/skills` itself, so machine-local
skills can live alongside the synced ones. Restart Claude Code afterward to pick
them up.
