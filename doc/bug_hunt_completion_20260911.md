# Bug hunt deployment and acceptance status — 11 September 2026

BH-005 is fixed and deployed to `192.168.10.18`. Deployment completed at
19:30:28 Bangkok time (12:30:28 UTC). Login, character, map, web, and database
services are running. The running map/character executable hashes match the
candidate tested on the remote isolated network. Public login, character, and
map ports are reachable from the Windows client workstation.

This is the current status; earlier reports preserve the original failure and
intermediate local-only results. The overall acceptance task remains incomplete
because the rendered client connection is unavailable and physical host power
loss has not been tested.

## Deployment

- Installed the nine changed persistence/protocol source files and matching map
  and character binaries. Production source had no drift from the inspected
  snapshot before deployment.
- Stopped login, map, and character services with no players online; backed up
  the replaced files and the full production database.
- Converted inventory from MyISAM to InnoDB. All 98 inventory rows had identical
  serialized content hashes before and after conversion and after restart.
- Updated the inventory definition in `sql-files/main.sql` and installed
  `sql-files/upgrades/upgrade_20260911_inventory_atomic.sql`.
- Verified clean startup and the actual running executables through `/proc`.
  The database and web services remained running during the rollout.

Backups and the deployment receipt are retained on the server at
`/app/rathena-builds/bughunt-20260911-runtime/production-deployment/`.
The directory is restricted to root and the database dump has mode 0600.
The dump is 22,750,190 bytes, SHA-256
`8fdd9287d7c82d9b16560a2283c51239ca950466faa1b83807a649ccb2a0cde9`.

The rollout script can restore replaced source/binaries if startup fails. It
leaves InnoDB in place because it is compatible with the old binaries. No rollback
was needed. A future rollback should stop writers and restore only the intended
files; restoring the database would discard later player changes and is not part
of an ordinary binary rollback.

## Completed verification

| Area | Evidence and result |
|---|---|
| Full local release gate | All 34 checks passed: source regressions, native quest/instance fixtures, asset validation, stable candidate fingerprint, and isolated startup. |
| Build identity | The local fresh build matched 2,819 workspace C/C++ source/header files. The remote deployment used its separately built, verified candidate. |
| Reform handler and commit protocol | Both fixtures passed against the actual remote candidate; 27 transaction cases plus delayed, failed, stale, duplicate, reconnect, retry, and logout cases. |
| Original reform crash regression | Six local disconnect/crash cases passed. The acknowledged result must survive map-process termination. Remote candidate disconnect and acknowledged-crash checks also passed. |
| Additional recipes | Thanos weapon and armor recipes survived acknowledged map crashes. Material counts, expected refine reduction from 10 to 5, cards, and unique identity were checked. Together with the Frontier axe, three recipe paths have real runtime crash evidence. |
| SQL statement failure | No success acknowledgement and no changed committed inventory rows during injected failure; automatic retry completed after repair. Passed locally and remotely. |
| SQL process outage | Actual local database process termination withheld success; restarting SQL allowed the pending reform to commit and acknowledge, preserving metadata. |
| Coordinated process crash | Abrupt termination of all four isolated services, including SQL, preserved the acknowledged result through InnoDB recovery and reconnect; flush-at-commit was 1. |
| Production backup restore | Restored the actual production dump into a disposable database with no network and no published ports. All 118 tables loaded; the 98 inventory rows matched the pre-migration hash. Removed the disposable container and its data volume afterward. |
| Final remote party check | Two protocol clients joined a party, transferred leadership, entered the same instance, disconnected, reconnected, and re-entered successfully. |
| Final remote controlled combat | Five physical attacks dealt 384 each; five Fire Bolts dealt 314 each against Neutral and 283 each against Water. These traverse the actual map combat handlers. |
| Production health | Running executable hashes matched, startup checks passed, and client-workstation TCP probes passed for ports 6900, 6121, and 5121. |
| Cleanup | All local synthetic processes and four remote synthetic services stopped; temporary NPC imports restored; prior failing receipts preserved. |

## Remaining acceptance and access blockers

The Computer Use package initializes, but native app enumeration consistently
returns: `Computer Use native pipe is unavailable: failed to connect native pipe:
The system cannot find the file specified. (os error 2)`.
SSH access is working; it does not supply rendered desktop access. A request to
reconnect Computer Use is pending with the user.

The user subsequently explained that Hyper-V was installed and this workstation
needs a reboot. Server-side work is finished and the remaining acceptance will
resume after that reboot; `../bughunt-20260911/RESUME.md` records the next steps.

Once that connection is restored, the remaining client work is:

1. Inspect full-inventory reform menus and rendered success/failure feedback.
2. Inspect sprites, effects, descriptions, navigation clicks, and active asset
   overrides in the actual game client.
3. Exercise overlapping production NPC dialogues, checkpoint reconnects,
   leader changes and repeated reward attempts with two rendered clients, and
   finish representative quest chains.
4. Play full boss encounters and verify visible cast timing, cooldowns, and
   relevant stacking combinations.

Physical host power loss remains unverified. The isolated SQL/all-services kill
test is process-crash evidence and does not prove host-cache or storage power-loss
behavior. That test requires a separate disposable host/VM arrangement; the live
production host was not powered off.

## Evidence and resume points

Evidence is under `../bughunt-20260911/` beside this repository:

- `full-final-gate/report.json` and `gate.log`: full local release gate.
- `outage-acceptance/runtime-transactions.json`: SQL outage and all-services crash.
- `public-service-ports.json`: workstation reachability.
- `remote/completion-evidence/production-deployment/`: deployment, backup restore,
  startup, and final health receipts, without copying the production SQL dump.
- `remote/completion-evidence/recipe-acceptance/`: weapon/armor crash receipts.
- `remote/completion-evidence/final-runtime/`: final candidate party/combat and cleanup.
- `remote/completion-evidence/durable-run/`: original remote durability and rollback.
- `remote/completion-evidence.zip`: collected non-database evidence archive.

Do not rerun `deploy_durable.py` as a resume step: deployment is complete and its
output directory deliberately prevents accidental replay. Resume at desktop
reconnection and rendered acceptance. The SSH password was held only in the
transport process and was not written into scripts or evidence.
