#!/bin/bash
git remote add upstream https://github.com/NousResearch/hermes-agent.git || true
git fetch upstream main
git reset --hard upstream/main
git commit -m "Sync Fork" --allow-empty
