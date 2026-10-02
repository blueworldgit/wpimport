# Create Duplicates: Runbook and Machine Handoff

## What the batch script does

`create_all_duplicates.py` reads pages from the configured
`/wp-json/custom/v1/products-with-replacements` endpoint, gathers and
deduplicates the product IDs before making writes, then calls
`duplicate_product()` in `createduplicates.py` for each eligible product. It
logs to the console and a file, retries endpoint reads, and can resume from a
prior run log.

The duplicate logic in `createduplicates.py` creates products with status
`publish`. This is a live write operation.

## Important target check before continuing

The endpoint originally supplied for this work was on
`maxuspartsdirect.co.uk`, but the interrupted batch log records requests to
`shane.maxusvanparts.co.uk`. Both the replacement endpoint and WooCommerce API
target are derived from local `config.py` (`WORDPRESS_URL`). **Do not resume
until you confirm that the new machine's `WORDPRESS_URL` and credentials point
to the same intended store as the old run.** Do not treat two domains as
interchangeable without confirming they contain the same products and prior
duplicates.

Also confirm that the custom endpoint does not return duplicates created by
this script as new source candidates. The duplicate carries product metadata
from its source, including replacement metadata. Use the dry-run below and
inspect the eligible source IDs/SKUs before allowing live creation.

## Files needed on the other machine

Commit/push these project files:

- `create_all_duplicates.py`
- `createduplicates.py` (includes the duplicate payload/status behavior)
- `CREATE_DUPLICATES_RUNBOOK.md`
- `SETUP_NEW_MACHINE.md` and `.gitignore` if changed
- The **full checkpoint log**: `create_all_duplicates_20260916_154314.log`

The small `create_all_duplicates_20260916_153642.log` is only a one-product
test. Do not use it as the resume checkpoint when continuing the full run.
The full log is approximately 0.9 MB and contains operational product IDs/SKUs;
include it only in the private project repository. Keep it unchanged until the
run is complete.

Do not use `git add .` for this handoff. The workspace also has unrelated
changes/untracked files; stage only the intended script, documentation, and
checkpoint files after reviewing `git status`.

## Credentials and local setup

`config.py` and `keys.txt` are needed locally but must not be committed. Create
or copy them securely on the new machine (outside the public repository/history)
and configure:

- `WORDPRESS_URL` for the confirmed target store.
- WooCommerce consumer key and secret in the format expected by
  `createduplicates.py`.

The current Git repository has previously tracked `config.py` and `keys.txt`;
`.gitignore` does not untrack files already in Git. Before pushing, remove those
files from Git tracking while keeping the local copies, ensure both names are
ignored, and rotate the WooCommerce keys because tracked credentials must be
treated as exposed. On the new machine, recreate the local files from a secure
source; do not recover credentials from Git history.

Install the dependencies from the project requirements in the active
environment. The script needs `requests` and `WooCommerce`, both listed in
`requirements.txt`.

## Resume workflow

In PowerShell, from the repository root, activate the project's environment and
verify the runner's options:

```powershell
.\env\Scripts\Activate.ps1
python create_all_duplicates.py --help
```

First run a **no-write preflight**. It fetches the full endpoint list, skips IDs
with confirmed successes from the checkpoint, and logs every remaining
candidate. Inspect the logged endpoint host, candidate IDs/SKUs, and count. If
newly created duplicate IDs appear as candidates, stop and resolve the endpoint
filtering before doing a live run.

```powershell
python create_all_duplicates.py --dry-run --resume-from-log .\create_all_duplicates_20260916_154314.log --log-file .\create_all_duplicates_20260916_154314.log
```

When the target and preflight list are confirmed, resume live using the same
file as both the resume source and log destination. This preserves one
cumulative history across repeated interruptions; keep using that same file
for each later restart.

```powershell
python create_all_duplicates.py --resume-from-log .\create_all_duplicates_20260916_154314.log --log-file .\create_all_duplicates_20260916_154314.log --pause 0.5
```

The pause is optional and limits the request rate. Press `Ctrl+C` to stop; the
runner records an interruption. On restart, use the same command and same log.
Confirmed successes are skipped and explicit failures are retried. If the log
has an ID with `Creating duplicate` but no following success/failure, the
outcome is ambiguous: inspect WooCommerce before deciding whether it is safe to
retry. Only then use `--retry-incomplete` if appropriate.

The resume parser understands repeated run sequence numbers in the same
cumulative log. Do not delete, truncate, rename, or replace the checkpoint log
mid-run.

## Recorded checkpoint

The full log `create_all_duplicates_20260916_154314.log` records:

- 1,300 source-product attempts started.
- 1,180 confirmed success records.
- 120 explicit failure records.
- No unresolved in-progress product record.
- The run stopped before page 14 of 28 could be fetched, after a DNS failure
  for `shane.maxusvanparts.co.uk`.

The runner resumes by source product ID, not by assuming page 14 is still the
right place. It re-fetches the current endpoint pages, skips logged successes,
and retries products that failed or were not yet reached. The endpoint may
change between runs, so review the dry-run output before creating more products.

## Completion checklist

Consider the batch complete only when all of the following are true:

1. The final live run reaches `Run complete` and exits with code `0`.
2. The final summary reports `failed=0` and `skipped_ambiguous=0`.
3. The endpoint fetch completed all reported pages; no page-fetch errors remain.
4. Any failed product IDs from earlier runs have been retried successfully or
   explicitly investigated and documented.
5. The final cumulative log is saved with the project handoff/operational
   records, and the created products are spot-checked in the confirmed store.

Exit code `1` means the run stopped on an endpoint/runtime error or has product
failures; review the end of the log and rerun with the same cumulative log after
resolving the issue. Exit code `130` means the user interrupted the run.