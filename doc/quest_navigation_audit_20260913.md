# Quest navigation audit and deployed fixes ? 13 September 2026

The verified release is installed on Docker rAthena at `192.168.10.18` and in the owner's Windows client. All 16 loaded episode groups, 13.1 through 21, pass the combined native route-distance and client collision checks. The audit covers 1,849 referenced episode quest IDs; none are missing client metadata. It checks 1,208 episode destination records, with 1,227 episode attributions because some quests belong to multiple episodes.

## Confirmed defects and fixes

- The generator stored up to 1,024 path steps in an 8-bit length. A 579-step path became 67. Length and position now use 16-bit storage; installed distances reach 1,021 steps.
- Map-edge checks accepted coordinates equal to the map width/height. They now reject those coordinates and a missing map safely.
- Native route generation required a walkable door/NPC center, losing valid routes to NPCs in furniture and portals whose centers are in walls. Distance generation now uses the nearest walkable approach within the portal's actual rectangular touch area, or a conservative three-cell NPC interaction area. Catalog coordinates stay intact; disconnected walkable regions cannot be joined by the fallback. The stricter check originally exposed 82 failing episode destination records across nine maps; the installed release has zero.
- El Dicastes elevator destinations were selected from arrays and omitted by the literal-warp annotation tool. It now generates all 48 duplicate-specific elevator links in an isolated generation tree.
- The installed Warper table was stale. Regeneration restores 65 currently loaded destinations from the live registrations. Twenty-five registrations for maps absent from this Renewal server remain excluded.
- Seventy-one missing physical doorway/stair links in Episodes 20 and 21 blocked the maze, barracks, Alberta rooms and equipment warehouse. Restored endpoints come from the owner's original client navigation data. Every destination is walkable in the actual server map cache; every doorway has a walkable cell inside its touch area. External entries retain the existing episode access helpers.
- The Episode 20 captured Rgan's room had no usable entrance. The Iwin Soldier now escorts eligible players inside. Returning during quests 17713?17716 no longer restarts quest 17712. Nadyagand's dialogue and quest 17713 now identify the NPC that actually advances the quest.
- The Episode 21 eastern tent rejected returning players after document progress. Tan now permits active quest 23243 at steps 4?6, preserving steps 5 and 6 on reentry. Unrelated, completed and later quest states stay rejected.
- Seventy-nine Episode 21 quest-book records were absent. The new overlay supplies guides with 104 anchors checked against live NPC declarations. Quest 19200 also incorrectly displayed an unrelated Troy timer; it now describes the actual food procurement assignment. Other existing records and later custom guides are preserved.

## Verification

The actual 32-bit Lua 5.1 runtime and original compiled client quest helper pass all four quest-loader entry points: 11,473 records, 12,438 description callbacks and 114 reward callbacks per loader. The overlay is idempotent, works without `table.insert`, and preserves custom guide overrides.

All 4,071 text navigation links and 318 structured NPC destinations pass structural/map/bounds checks. Nine text points lie on blocked cells but have valid NPC approaches. All native NPC/link distance references and unique IDs are consistent. The installed KRPRI and KRSAK tables match and resolve from the active highest-priority archive. All 302,124 native Lua navigation callbacks and table-end calls pass.

The current native script VM passes 70 entrance scenarios / 253 checks; reconstructing the old entrance logic produces 33 expected failures. Separate instance checkpoint tests pass 113 checks, and finale-flow tests pass 46. ASan, UBSan and the native allocator report no errors. The actual generator pathfinder regression verifies a 579-step path, map boundaries, blocked NPC approaches, rectangular touch areas and disconnected rooms.

| Episode | Quests with destinations | Target attributions | Maps | Route result |
|---|---:|---:|---:|---|
| 13.1 | 77 | 101 | 17 | Passed |
| 13.2 | 32 | 36 | 9 | Passed |
| 13.3 | 15 | 20 | 6 | Passed |
| 14.1 | 28 | 31 | 3 | Passed |
| 14.2 | 52 | 62 | 10 | Passed |
| 14.3 | 18 | 19 | 3 | Passed |
| 15.1 | 22 | 28 | 5 | Passed |
| 15.2 | 17 | 24 | 2 | Passed |
| 16.1 | 36 | 37 | 5 | Passed |
| 16.2 | 33 | 34 | 10 | Passed |
| 17.1 | 55 | 67 | 7 | Passed |
| 17.2 | 114 | 114 | 10 | Passed |
| 18 | 148 | 190 | 12 | Passed |
| 19 | 201 | 221 | 23 | Passed |
| 20 | 105 | 129 | 16 | Passed |
| 21 | 88 | 114 | 13 | Passed |

These route proofs combine the native generator's directed `E` distances with the effective client's GAT components. They prove available geometric paths, while original scripts continue to enforce each player's quest, level, disguise, party and instance conditions. They are not a rendered in-game playthrough of every quest. The supplemental raw NPC scan also records hidden controllers, developer NPCs and legacy/non-episode locations; these are not treated as player quest destinations or silently moved.

## Installation, data preservation and rollback

The map server restarted successfully with no parser/SQL/fatal errors. The running map and character executables still match the deployed bank binaries. Across the update, ordered hashes were unchanged for all 2 character rows, 112 inventory rows, 2 account registry rows, 51 character registry rows, 31 quest rows, 2,590 item-log rows and the bank journal. No database schema changes were made.

Client installation updates `client_repairs.grf`, appends the guide import to `SystemEN/OngoingQuests.lub`, and adds `SystemEN/EpisodeQuestNavigation.lua`. Ten navigation resources changed; the other 163 archive resources remain byte-identical. `DATA.INI`, Ragexe, the bank DLL, the font-wrapper DLL, the original font DLL and font settings are unchanged. Restart the client to load the new data.

Evidence and backups:

- Local evidence: `server-work/quest-navigation-20260913/`; final result: `release/validation.json`.
- Client rollback files and hashes: `server-work/quest-navigation-20260913/client-backup/receipt.json`.
- Server evidence: `/app/rathena-builds/quest-navigation-20260913/`.
- Server rollback files and receipt: `deployment/backup/` and `deployment/report.json` in that remote directory.
- Full SQL backup: `deployment/database-backup.sql` in that remote directory, owner-readable only. Ordinary rollback restores files, not player data.

Generation used a private schema-only database and isolated Docker network; it never executed NPC initialization against the live database. The test database is stopped. Generated `OnNaviGenerate` annotations are confined to the isolated generator tree; live quest logic receives only the reviewed room/reentry fixes.

The canonical regression entry points are `tools/ci/navigation_path_test.py`, `episode_navigation_access_test.py`, `episode_navigation_client_test.lua`, and `navigation_callbacks_test.lua`. The source-anchor guide manifest and doorway provenance are retained in `client-patch/navigation_repair/SystemEN/EpisodeQuestNavigation.json` and `tools/navigation/episode_doorways_20260913.json`.
