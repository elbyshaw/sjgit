#!/usr/bin/env bash
# Cron entry point: retry adding the users in run.csv to the GitHub team(s).
#
#   1. If run.csv is empty, nobody is left to retry -> exit quietly.
#   2. Run github_invites.py (it rewrites log.txt with this run's results).
#   3. If it finished cleanly, rebuild run.csv from the ERROR lines in log.txt
#      so the next run only retries the users that are still failing.
#      If it crashed part-way (network, auth, ...) run.csv is left alone so
#      nobody is dropped from the retry list.
#
# flock skips a run if the previous one is still going, so runs never overlap.
set -u
cd "$(dirname "$(readlink -f "$0")")" || exit 1
export GH_HOST=github.gatech.edu

stamp() { date '+%F %T'; }

exec 9>.retry_invites.lock
if ! flock -n 9; then
    echo "$(stamp) previous run still in progress, skipping"
    exit 0
fi

if ! grep -q '[^[:space:],]' run.csv 2>/dev/null; then
    echo "$(stamp) run.csv is empty - nobody left to retry"
    exit 0
fi

pending=$(tr ',' '\n' < run.csv | grep -c '[^[:space:]]')
echo "$(stamp) retrying $pending pending user(s)"

output=$(python3 github_invites.py 2>&1)
status=$?
if [ $status -ne 0 ]; then
    echo "$(stamp) github_invites.py exited with status $status; run.csv left unchanged"
    printf '%s\n' "$output"
    exit $status
fi

# Only the interesting lines: users that got added this time, plus the totals.
printf '%s\n' "$output" | grep -E '^> LOG: Adding|^Request completed' | sed "s/^/$(stamp) /"

python3 regen_run_csv.py --allow-empty | sed "s/^/$(stamp) /"
