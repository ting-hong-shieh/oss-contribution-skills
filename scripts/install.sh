#!/usr/bin/env bash
# Install the OSS contribution skills for Claude Code and/or Codex.
#
# The skills are installed as symlinks, so a `git pull` in this checkout
# updates every install without reinstalling.
#
#   ./scripts/install.sh                 # both hosts, user scope
#   ./scripts/install.sh --claude        # Claude Code only
#   ./scripts/install.sh --codex         # Codex only
#   ./scripts/install.sh --project DIR   # project scope, into DIR
#   ./scripts/install.sh --uninstall     # remove links this script created
#
# Adapters and hooks are NOT installed. They are opt-in enforcement and must
# be read before use: adapters/claude-code/README.md, adapters/codex/README.md

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS=(oss-radar oss-contribute oss-pr-maintenance)

want_claude=0
want_codex=0
uninstall=0
project_dir=""

while [ $# -gt 0 ]; do
    case "$1" in
        --claude) want_claude=1 ;;
        --codex) want_codex=1 ;;
        --uninstall) uninstall=1 ;;
        --project)
            shift
            [ $# -gt 0 ] || { echo "--project requires a directory" >&2; exit 2; }
            project_dir="$1"
            ;;
        -h|--help)
            sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
    shift
done

# No host selected means both.
if [ "$want_claude" -eq 0 ] && [ "$want_codex" -eq 0 ]; then
    want_claude=1
    want_codex=1
fi

if [ -n "$project_dir" ]; then
    mkdir -p "$project_dir"
    base="$(cd "$project_dir" && pwd)"
    claude_dir="$base/.claude/skills"
    codex_dir="$base/.agents/skills"
else
    claude_dir="$HOME/.claude/skills"
    codex_dir="$HOME/.agents/skills"
fi

targets=()
[ "$want_claude" -eq 1 ] && targets+=("$claude_dir")
[ "$want_codex" -eq 1 ] && targets+=("$codex_dir")

# Remove a path only when it is a symlink this script would have created.
# A real directory there is someone else's skill and is never touched.
remove_link() {
    local link="$1"
    if [ -L "$link" ]; then
        rm -f "$link"
        echo "removed $link"
    elif [ -e "$link" ]; then
        echo "skipped $link: not a symlink, leaving it alone" >&2
        return 1
    fi
}

status=0

for dir in "${targets[@]}"; do
    if [ "$uninstall" -eq 1 ]; then
        for skill in "${SKILLS[@]}"; do
            remove_link "$dir/$skill" || status=1
        done
        continue
    fi

    mkdir -p "$dir"
    for skill in "${SKILLS[@]}"; do
        source_dir="$REPO_ROOT/skills/$skill"
        if [ ! -f "$source_dir/SKILL.md" ]; then
            echo "missing $source_dir/SKILL.md" >&2
            status=1
            continue
        fi
        link="$dir/$skill"
        if [ -e "$link" ] && [ ! -L "$link" ]; then
            echo "skipped $link: not a symlink, leaving it alone" >&2
            status=1
            continue
        fi
        ln -sfn "$source_dir" "$link"
        echo "linked $link -> $source_dir"
    done
done

if [ "$uninstall" -eq 0 ]; then
    echo
    echo "Restart the host, or start a new session, to pick the skills up."
    echo "Enforcement adapters are opt-in and were not installed."
fi

exit "$status"
