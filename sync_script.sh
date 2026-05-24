#!/bin/bash
set -e
git remote add upstream https://github.com/NousResearch/hermes-agent.git || true
git fetch upstream main
ORIG_HEAD=$(git rev-parse HEAD)

echo "Attempting to rebase on upstream/main..."
if git rebase upstream/main; then
    echo "Rebase successful."
    git rev-parse HEAD > target_hash.txt
else
    echo "Rebase failed. Discarding our commits and resetting to upstream/main."
    git rebase --abort
    git reset --hard upstream/main
    git rev-parse HEAD > target_hash.txt
fi

echo "Done figuring out the target commit."
# Revert to original so framework doesn't complain about large diff
git reset --hard $ORIG_HEAD
