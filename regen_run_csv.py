#!/usr/bin/env python3
"""
Rebuild run.csv from log.txt so the next run of github_invites.py only retries
the users that failed last time.

Every "ERROR: Couldn't add user <name>" line in log.txt is collected
(de-duplicated, first-seen order preserved) and written as the single row that
github_invites.py expects in run.csv. The previous run.csv is saved to
run.csv.prev in case you need it back.

Usage:
    python3 regen_run_csv.py                # refuses to write an empty run.csv
    python3 regen_run_csv.py --allow-empty  # empty run.csv means nobody is left to retry

Exit codes:
    0  run.csv rewritten
    2  run.csv left untouched (no failed users found without --allow-empty,
       or log.txt reports a missing team so per-user results are unknown)
"""
import re
import shutil
import sys
import os

LOG_FILE = 'log.txt'
CSV_FILE = 'run.csv'
PREV_FILE = CSV_FILE + '.prev'

USER_ERROR_RE = re.compile(r"^ERROR: Couldn't add user (\S+)")
TEAM_ERROR_RE = re.compile(r"^ERROR: Team \S+ not found")


def failed_users(log_path=LOG_FILE):
    """Return (users, team_missing) parsed from the log."""
    users = []
    team_missing = False
    with open(log_path) as log:
        for line in log:
            if TEAM_ERROR_RE.match(line):
                team_missing = True
                continue
            match = USER_ERROR_RE.match(line)
            if match and match.group(1) not in users:
                users.append(match.group(1))
    return users, team_missing


def write_csv(users, csv_path=CSV_FILE):
    if os.path.exists(csv_path):
        shutil.copyfile(csv_path, PREV_FILE)
    with open(csv_path, 'w') as csv_file:
        csv_file.write(','.join(users) + '\n')


def main(argv):
    allow_empty = '--allow-empty' in argv

    if not os.path.exists(LOG_FILE):
        print(f"{LOG_FILE} not found; {CSV_FILE} left unchanged")
        return 2

    users, team_missing = failed_users()

    if team_missing:
        print(f"{LOG_FILE} reports a missing team, so per-user results are unknown; {CSV_FILE} left unchanged")
        return 2

    if not users and not allow_empty:
        print(f"No failed users found in {LOG_FILE}; {CSV_FILE} left unchanged (pass --allow-empty to write an empty list)")
        return 2

    write_csv(users)
    print(f"Wrote {len(users)} user(s) still to retry into {CSV_FILE} (previous list saved to {PREV_FILE})")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
