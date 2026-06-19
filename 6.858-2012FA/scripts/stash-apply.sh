#!/bin/bash
# Apply the first git stash whose message matches a pattern.
# Usage: stash-apply.sh "lab2 verified"
set -e
cd "$(dirname "$0")/../lab"
pattern="$1"
[ -n "$pattern" ] || { echo "usage: stash-apply.sh <pattern>" >&2; exit 1; }
ref=$(git stash list | grep -F "$pattern" | head -1 | sed 's/:.*//')
if [ -z "$ref" ]; then
  echo "no stash matching: $pattern" >&2
  exit 1
fi
echo "Applying $ref ($pattern)"
git stash apply "$ref" || git stash apply --index "$ref" || true
