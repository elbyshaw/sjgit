# sjgit

Bulk-adds GT users to SiliconJackets GitHub Enterprise teams via `gh`.

## Files

- `github_invites.py` — reads the single-row `run.csv`, PUTs each user into
  the team(s) listed in `team_names`, and rewrites `log.txt` with one
  `ERROR: Couldn't add user <name> (<reason>)` line per failure.
- `regen_run_csv.py` — rebuilds `run.csv` from the ERROR lines in `log.txt`
  so only the users that are still failing get retried. The previous list is
  saved to `run.csv.prev`.
- `retry_invites.sh` — cron entry point: runs the invite script and, if it
  finished cleanly, regenerates `run.csv`. Skips itself if a previous run is
  still going or if `run.csv` is empty.

## Retry loop

Users cannot be added to a team until they have logged into GitHub Enterprise
with their school credentials at least once, so the first run typically fails
for a chunk of the list. A cron job retries every 5 minutes:

```
*/5 * * * * /home/elby/dev/sjgit/retry_invites.sh >> /home/elby/dev/sjgit/cron.log 2>&1
```

Each cycle: run `github_invites.py` on whatever is in `run.csv` → on success,
shrink `run.csv` to the users that still failed → repeat. When `run.csv` is
empty everyone has been added and each cron run exits immediately.

Watch progress with `tail -f cron.log`; only newly-added users and the run
totals are logged there. Remove the cron line with `crontab -e` once done.

To start a fresh batch, put the new comma-separated list into `run.csv`.
