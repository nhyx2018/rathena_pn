# Follow-up audit and disk cleanup — 14 September 2026

Completed the item, quest/navigation, archive-override and disk audits. No gameplay/server deployment was made during this follow-up. Disk cleanup completed without restarting production containers.

## Disk result

- Root usage fell from **88% to 66%** (`df`). Available space rose from **12.05 GB to 34.07 GB** (decimal).
- Reclaimed **22,020,321,280 bytes**: nine inactive build directories, 17,186,848,768 bytes; three obsolete episode deployment directories, 4,833,472,512 bytes.
- The nine builds were streamed to `old-server-builds-20260907-09.tar.gz` on this workstation. All 55,140 file/link entries were checked against a source manifest, then the remote source was rehashed and checked for running references before deletion.
- Archive size: 7,860,032,968 bytes. SHA-256: `edf5cb87ffd68f00c731baaeb8e4d5dd559581f9fef908442fcc6bcc47c40be7`.
- User confirmed the latest full-VM Veeam backup succeeded and is stored outside 192.168.10.18. That confirmation supported removal of the old original/r4/r5 episode deployment copies. The newer r6/r7 copies were retained and their release archive indexes were readable. This was not a full restore test.
- SQL backups, smaller rollback patches, current builds, active application files and Docker volumes were preserved. All seven production containers remained running after cleanup.

Largest pre-cleanup consumers: `/app/rathena-builds` 30.06 GB, `/app/rathena-deploy-backups` 11.03 GB, `/var/lib/containerd` 13.70 GB. Containerd includes application image layers, so its full size is not reclaimable cache. An unrelated stopped OpenWebUI deployment and its volume were preserved.

Recommended ongoing practice: use off-host Veeam for historical recovery; keep two recent, tested rollback versions for each application deployment series; remove disposable build trees after validation and rollback requirements are satisfied. The retained episode copies do not represent two complete current-system restore points. No scheduled deletion or Veeam setting was installed or changed.

Evidence: `evidence/disk-before.jsonl`, `disk-cleanup.json`, `backup-inventory.jsonl`, `backup-cleanup.jsonl`, `live-cache.jsonl`, `offload-manifest.json`.

## Item availability

The 443 newly flagged item IDs are absent from the effective server item database. Across all 2,035 catalog IDs with missing archive-icon references, 1,592 exist in the server database; none had a static acquisition path in this audit.

Added reusable `tools/audit_item_acquisition.py`, including imported YAML databases, item groups, active NPC includes, literal grants, shops, mob drops, invoked barter shops, achievement rewards and an optional older held-item snapshot. The audit traced 5,056 item source paths across 920 active NPC files; all 5,056 had client metadata. A synthetic imported-database test passed, including invoked barter and nested group paths. Its first run exposed and fixed handling of bank IDs absent from a fixture database.

This does not prove the flagged items can never be obtained. There are 199 unresolved dynamic grant lines, and prerequisite reachability, future content, runtime artwork fallbacks and rendered icons remain outside static proof. Evidence: `evidence/item-acquisition.json`.

## Quest, reward and navigation verification

- Native Lua 5.1: 302,124 navigation callbacks passed; maximum route distance 1,021; safe end-of-table behavior.
- Four quest loaders passed: 11,473 records, 12,438 description callbacks and 114 reward callbacks per loader; repeated overlays remained safe and custom guides were preserved.
- Native remote candidate tests passed: episode navigation access (70 cases / 253 assertions), navigation pathfinding, Episode 21 checkpoints (113 checks), finale flow (16 cases / 46 assertions).
- Earlier local legacy navigation and party progression checks also passed. A local native link attempt failed because its support object files were stale; native checks were instead run with the current remote candidate objects in disposable, network-isolated containers.

These validate Lua callbacks and native test scenarios with explicit test doubles; they are not a complete live-player playthrough or SQL integration test. Evidence: `evidence/native-quests.jsonl`; Lua invocation results recorded below.

## Archive overrides and actionable map finding

Reviewed the 1,022 changed archive collisions from the earlier integrity audit (242,185 verified payloads, zero reported payload errors). Extracted the effective navigation and quest helpers and exercised their callbacks.

Compared all six overridden GAT maps against the effective import → renewal → base server map-cache order. All three local cache hashes match the deployed files. Dimensions agree for all six maps, but walkability differs:

| Map | Differing cells |
| --- | ---: |
| Airplane | 0 |
| Einbroch | 885 |
| Lighthalzen | 13,956 |
| Payon | 0 |
| Veledor | 0 |
| Yuno | 53 |

**Next gameplay priority: reconcile the client map set and server collision data, starting with Lighthalzen.** Select the intended geometry, then check NPC/warp coordinates and movement on a candidate before deploying either changed client assets or a server cache. No map was changed blindly during this audit. Archive precedence assumes ascending DATA.INI; visual appearance and executable lookup behavior were not proven.

Evidence: `evidence/archive-overrides.json`; reproducible extraction/comparison script: `audit_overrides.py`.

## Verification commands

From the client Data directory, using its existing Lua 5.1 executable:

```text
lua5.1.exe server-work/rathena_pn_push/tools/ci/navigation_callbacks_test.lua ../Client-Packages/audit-followup-20260914/extracted ../Client-Packages/audit-followup-20260914/extracted/navi_f_krpri.lub
lua5.1.exe server-work/rathena_pn_push/tools/ci/episode_navigation_client_test.lua SystemEN/EpisodeQuestNavigation.lua ../Client-Packages/audit-followup-20260914/extracted/questinfo_f.lub
```

The unrelated previously blocked local `candidate-attempt-01` scratch directory was not touched by this server cleanup.
