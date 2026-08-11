#!/usr/bin/env bash
#
# Link this repo's entry-point skills and config files into the Claude Code
# config directory. Safe to re-run: existing symlinks are replaced, real files
# and directories are left alone. See README.md for what each step does and why.

set -euo pipefail

ENTRY_POINTS=(
    code-review
    improve-code
    improve-tests
    plan-scaffold
    split-and-commit
    lazy-issue
    lazy-pr
    audit
)

# Linked from config/ to the root of the Claude config directory.
CONFIG_FILES=(
    CLAUDE.md
)

REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SKILLS="$CLAUDE_DIR/skills"
DRY_RUN=false

usage() {
    cat <<EOF
usage: install.sh [-n|--dry-run] [-h|--help]

Links into \$CLAUDE_CONFIG_DIR (default ~/.claude):
  skills/   ${ENTRY_POINTS[*]}
  files     ${CONFIG_FILES[*]}

  -n, --dry-run   report what would change without touching anything
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        -n|--dry-run) DRY_RUN=true ;;
        -h|--help) usage; exit 0 ;;
        *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

run() {
    if [ "$DRY_RUN" = true ]; then
        return 0
    fi
    "$@"
}

echo "repo:   $REPO"
echo "config: $CLAUDE_DIR"
if [ "$DRY_RUN" = true ]; then
    echo "(dry run, nothing will be written)"
fi
echo

run mkdir -p "$SKILLS"

swept=0
for link in "$SKILLS"/*; do
    if [ -L "$link" ] && [ ! -e "$link" ]; then
        target=$(readlink -- "$link")
        run rm -- "$link"
        echo "swept stale link: $(basename -- "$link") -> $target"
        swept=$((swept + 1))
    fi
done
if [ "$swept" -gt 0 ]; then
    echo
fi

linked=0
skipped=0
for name in "${ENTRY_POINTS[@]}"; do
    src="$REPO/skills/$name"
    dest="$SKILLS/$name"

    if [ ! -d "$src" ]; then
        echo "not in repo, skipping: $name"
        skipped=$((skipped + 1))
        continue
    fi

    if [ -e "$dest" ] && [ ! -L "$dest" ]; then
        echo "real directory, skipping: $name"
        skipped=$((skipped + 1))
        continue
    fi

    run ln -sfn -- "$src" "$dest"
    echo "linked: $name"
    linked=$((linked + 1))
done

for name in "${CONFIG_FILES[@]}"; do
    src="$REPO/config/$name"
    dest="$CLAUDE_DIR/$name"

    if [ ! -f "$src" ]; then
        echo "not in repo, skipping: $name"
        skipped=$((skipped + 1))
        continue
    fi

    # A real file here is the user's own config, and clobbering it would lose
    # content that exists nowhere else. Converting is a deliberate manual step.
    if [ -e "$dest" ] && [ ! -L "$dest" ]; then
        echo "real file, skipping: $name (move it into $REPO/config/ to sync it)"
        skipped=$((skipped + 1))
        continue
    fi

    run ln -sfn -- "$src" "$dest"
    echo "linked: $name"
    linked=$((linked + 1))
done

echo
if [ "$swept" -eq 1 ]; then
    echo "$linked linked, $skipped skipped, 1 stale link swept."
else
    echo "$linked linked, $skipped skipped, $swept stale links swept."
fi

if [ "$DRY_RUN" = false ]; then
    echo "Restart Claude Code to pick these up, then check with:"
    echo "  claude plugin details audit"
fi
