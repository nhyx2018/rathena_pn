# BH-005 durability follow-up — 11 September 2026

**Current status:** production deployment and extended recovery tests have now
passed. See [the deployment and acceptance status](bug_hunt_completion_20260911.md)
for the current receipts and remaining desktop-dependent checks. The text below
records the earlier local validation stage.

The in-progress inventory persistence fix now passes the local regression that
previously reproduced loss of an acknowledged equipment reform after a map-server
crash. This validates the local candidate; it does not establish that production
has been updated.

## Candidate behavior

Inventory writes use an explicit SQL transaction with automatic reconnection
disabled during the transaction. Character startup and inventory saves require
InnoDB. Reform success is sent to the client only after the character server
confirms the inventory commit. Pending commits retry and reject overlapping
reforms; replies are matched to the character and request identifier.

Existing installations must apply
`sql-files/upgrades/upgrade_20260911_inventory_atomic.sql` to the configured
inventory table before starting the new character server. Its instructions call
for stopping writers and backing up inventory. Map and character binaries must
both support the new commit packets. No production migration or deployment was
performed during this resumed pass.

## Resumed verification

The existing fresh local build was checked against all 2,819 workspace C/C++
source/header files, with no drift. Binary hashes are retained in the new receipt.
The rebuild had reset test connection overrides; these were restored only in
`/home/alpha/bughunt-20260911-build`, using loopback ports and the existing isolated
synthetic database in `/home/alpha/bughunt-20260911-sql`.

| Check | Result |
|---|---|
| Production commit protocol fixture | Passed delayed, failed, stale and duplicate replies, reconnect, current-inventory retry, and logout. |
| Production reform transaction fixture | All 27 cases passed. |
| Disconnect before confirmation, after acknowledgement, and racing confirmation | All three passed. |
| Map crash before confirmation | Original inputs retained. |
| Map crash after acknowledgement | Completed reform retained, including item metadata. The regression now requires the completed result. |
| Map crash racing confirmation | Whole original inputs retained; no partial consumption. |
| Injected SQL DELETE failure | No success acknowledgement; every committed inventory row remained unchanged. |
| Removal of injected SQL failure | Automatic retry committed the completed reform, acknowledged success, and preserved metadata. |
| Working-tree whitespace check | Passed. |

Evidence lives beside the repository under `../bughunt-20260911/`:

- `resumed-durability/runtime-transactions.json`: six passing runtime cases.
- `resumed-durability/fresh-build-receipt.json`: source and binary identity.
- `resumed-durability/*test.py.log`: the two production-code fixtures.
- `resumed-sql-failure/runtime-transactions.json`: SQL rollback and retry result.
- Both directories retain generated reproduction scripts and service logs.
- `resume_checks.py`, `resume_identity.py`, `resume_sql_failure.py`, and
  `sql_failure_local_case.txt` reproduce this pass with fresh evidence directories.

The synthetic inventory table was converted to InnoDB. Test processes were shut
down and the temporary NPC import restored by the harnesses' cleanup handlers.
Prior failing receipts were preserved.

## Remaining scope

BH-005 is locally validated for one reform recipe and map-process crashes.
The remote report still describes the previously tested installed binaries.
Production deployment, remote candidate verification, database connection loss,
host power loss, broader recipes, and rendered-client acceptance remain pending.
The injected SQL statement error proves rollback and retry for that failure mode;
it is not a database-outage or host-crash test.
