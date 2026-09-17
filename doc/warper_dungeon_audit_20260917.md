# Warper and dungeon audit — 2026-09-17

## Result

Audited the active Renewal Warper against the reference screenshots, server map caches, loaded map configuration, NPC imports, navigation registrations and native script execution. Deployed the scoped Warper fix to Docker host 192.168.10.18. The map server registered successfully with no startup errors.

## Fixes

- Reset per-character menu flags, restriction mask, menu text and coordinate array at the start of each conversation. Canceled or direct-warp conversations previously left temporary state behind, which could affect first-floor-only configurations.
- Corrected Hidden Dungeon navigation landings: prt_maze01 to (99,31), prt_maze03 to (182,88), matching the actual menu.
- Added 90 missing Renewal navigation registrations, including Amicitia, Abyss 4, Unknown Clock Tower Basement, Issgard, Biosphere and episode/chapter areas. Registrations honor the first-field/first-dungeon settings.
- End the navigation callback explicitly before OnInit so navigation generation cannot reset NPC settings.
- Added a destination/configuration audit to the source release checks and a native regression for reopening after stale menu state.

Existing story-access checks and Last Warp behavior were preserved. Navigation registrations are server generation inputs; this task did not regenerate or distribute client navigation files.

## Verification

- 617 direct/generated menu destinations checked; 268 belong to dungeon menus.
- All destinations exist in map caches and have walkable landing cells.
- Destinations are loaded or explicitly restricted to Pre-Renewal.
- 920 active NPC script references exist; all named Warper access helpers are defined in the loaded scripts.
- Menu targets resolve; manually listed map counts match their submenus.
- No menu destination lacks a matching navigation registration after the fix.
- Native instance/access/navigation regression: 410 checks, 0 failures, 0 parser/runtime errors; clean native memory teardown with sanitizers enabled. Movement and selected world services are test boundaries, not live player actions.
- Isolated production-binary startup against disposable SQL: 21 schema files; no startup errors.
- Live deployment: zero online players before restart; map, char and login containers running afterward; Map Server is now online marker confirmed.
- git diff --check passed.

Commands: `python tools/ci/warper_destination_test.py`; Linux `python3 tools/ci/instance_warper_test.py --build-dir /home/alpha/warper-audit-native`.

## Reference screenshots

The screenshots are from another server, as confirmed by the user. Our menu groups several entries instead of listing each separately:

| Reference entry | Our route |
| --- | --- |
| Abandoned Pit / Snake's Nest / Sacred Root | Issgard Dungeon |
| Abyss Lake 4 | Abyss Lakes, floor 4 |
| Abyss Glast Heim | Glast Heim, Abyss Glastheim Castle F1 |
| Amicitia | Abandoned Lab Amicitia |
| Clock Tower Unknown Basement | Clock Tower, Unknown Basement |
| Einbech Dungeon 3 | Einbroch Dungeon, floor 3 |
| Deep Root Cave | Episode 20 Areas, Deep Roots Cave |
| Magma Dungeon F3 | Magma Dungeon, floor 3 |
| Odin's Past | Odin Temple, Odin Past |
| Rudus F4 | Rudus Dungeon, floor 4 |
| Garden of Time | Existing Lake of Fire / Hall of Life instance entrance routes |
| Chapter 1 | Call of the World Tree and Chapter 1 / Zero Cell |

Ancient Temple Arket, Niflheim Pumpkin Farm, Power Twisted Plains and Unknown Blue Hole could not be positively mapped to installed dungeon content by those names. Mjolnir Underground Cave is also absent from the Warper; `mjo_wst01` exists in map configuration/index, but a map entry alone does not establish complete playable content. No speculative destinations were added.

## Deployment and limits

Backup: `/app/rathena-deploy-backups/warper-20260917/warper.txt`.
Startup evidence: `/app/rathena-deploy-backups/warper-20260917/startup.log`.
Deployed SHA-256: `a55883126444822a32291463b92325c1ea8bb6a24e01e26796f0de3c00fc870e`.

Pre-existing startup warnings remain: root execution, item 12781 buy/sell protection, and monster IDs 22177/22180 Attack2 clamping. These are outside the scoped Warper fix. No full player walkthrough of every quest, spawn, boss or client map asset was performed; startup and automated checks do not prove every dungeon mechanic is error-free.
