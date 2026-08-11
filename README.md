# Claude Skills

Skills I personally find useful. No nerds allowed.

Code quality, review, planning, and security-audit skills for
[Claude Code](https://claude.com/claude-code), synced across machines via this
repo.

## Contents

Entry points, invoked directly:

- `code-review` -- shippable-or-not verdict and severity; reports only, never edits
  (`--quick` triage, `--deep` paranoid audit)
- `improve-code` -- tiered audit of correctness, design, and style; `--apply` lands the
  behavior-preserving tiers, bugs stay opt-in
- `improve-tests` -- test quality and coverage as Remove/Improve/Add; `--apply` lands
  Improve and Add, deletions stay opt-in
- `improve-notebook` -- notebook reproducibility, cell granularity, figures, and prose;
  stacks `improve-code --apply` over the cell contents, always applies, and reports the
  joint pass; only re-run-the-world fixes stay proposals
- `plan-scaffold` -- scaffold a step/PR/commit implementation plan in the Obsidian vault
- `split-and-commit` -- break working changes into logical commits
- `lazy-issue` / `lazy-pr` -- file a GitHub issue or open a PR

Alongside those, 22 narrower single-axis passes live under `skills/audit/`, which is
a plugin rather than a plain skill, so they namespace instead of crowding the
top-level slash list:

- `/audit:input-validation`, `/audit:solid-principles`, `/audit:exception-flow-analysis`, ...
- `/audit` -- routes to the right pass when you haven't named one

They are invoked explicitly, never picked up on their own: every pass sets
`disable-model-invocation`, so it fires only from its own slash command or from the
`/audit` router. The entry points above do not call into them -- reach for a pass
when you want one axis examined in depth, and an entry point when you want a verdict
on a whole change.

They group into security (`initial-security-analysis` first, `comprehensive-security-report`
last), design (`solid-principles`, `design-pattern-implementation`,
`code-duplication-detection`, ...), reliability (`error-handling-resilience`,
`resilience-fault-tolerance`, ...), and quality (`readability-and-naming`,
`testing-implementation`, ...). `skills/audit/SKILL.md` is the full index.

`config/` holds files that link to the root of the Claude config directory rather
than into `skills/`. Currently that is `CLAUDE.md`, the global preferences every
session loads. It sits in `config/` rather than at the repo root because a root
`CLAUDE.md` would *also* load as project instructions whenever you work in this
repo, applying the same rules twice from two sources.

Only portable content is synced -- language, response style, code style, testing.
Anything true of one machine but not the others (production data paths, internal
dataset names, locally installed tooling) stays out of the repo in
`~/.claude/CLAUDE.local.md`, which the synced file pulls in with a trailing import:

```
@~/.claude/CLAUDE.local.md
```

A missing import target is silently ignored, so the same synced file works unchanged
on a machine with no local additions -- nothing to comment out, no error at startup.

The import is doing real work and is not decorative: a `CLAUDE.local.md` sitting in
the Claude config directory is **not** picked up on its own. That name auto-loads at
the project level only, so without the `@` line the file is simply never read.

## Install

Clone anywhere and run `install.sh`. It locates the repo from its own path, so
nothing needs editing and it does not care about your working directory:

```sh
git clone git@github.com:jessegrabowski/claude_skills.git
./claude_skills/install.sh          # -n to see what it would do first
```

Re-run it after any pull that renames or moves a skill. Restart Claude Code
afterward to pick the changes up, then confirm with `claude plugin details audit`
and `/help`.

Four things the script is deliberately doing:

- **The clone's location is discovered, not configured.** A symlink encodes an
  absolute path, and `ln` will happily point one at a directory that does not exist.
  Resolving the repo from `BASH_SOURCE` means the script works whatever the clone is
  called and wherever it lives; `CLAUDE_CONFIG_DIR` is honored for the same reason.
- **Stale links are swept first.** A symlink whose target moved does not error, it
  just silently stops resolving, so a rename upstream leaves dead entries behind
  until something removes them. The sweep drops any link in `skills/` that no longer
  resolves -- including ones pointing at other repos, so use `-n` first if you link
  skills from elsewhere.
- **Per-skill links, not one link on `skills/` itself.** Machine-local skills that
  should not be synced can then sit in the same directory. An existing *real*
  directory is never touched: `ln -sfn` against one silently creates the link
  *inside* it (`~/.claude/skills/improve-code/improve-code`) rather than replacing
  it, so the script skips those and says so. To convert one, confirm the repo copy is
  current, remove the real directory, and re-run. An existing *symlink* is replaced
  normally, so re-running is always safe.
- **Only the entry points get linked.** The delegated analysis skills are reached
  through those, not invoked directly, so linking all of them just crowds the skill
  list with near-miss descriptions for the trigger matcher to sort through. `audit`
  is in the list because it is a plugin: linked into `skills/`, Claude Code loads it
  as `audit@skills-dir` and its 22 passes namespace under `/audit:<name>` instead of
  registering top-level.

Once linked, the clone *is* live config. A `git checkout`, branch switch, or rebase
changes the skills in every running session. That is the point -- edit either path
and both see it -- but it means the repo is no longer inert.

There is deliberately no marketplace manifest here. A marketplace install would put
a pinned copy in the plugin cache that updates on `claude plugin update` rather than
on `git pull`, which is the opposite of what this repo is for.
