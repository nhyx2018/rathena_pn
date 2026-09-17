# Instance warper and script audit — 2026-09-17

## Scope and findings

Compared the supplied reference-server instance list with the effective Renewal instance database, enabled NPC scripts and Warper. The catalog now tracks 66 reference categories and 102 local instance definitions, with 71 required Warper entries.

Found and fixed a missing Room of Consciousness route. It now appears under Instances > More Episode Instances > Episode 16.1 - Room of Consciousness and lands beside Nillem at prt_lib_q (91,83). ValidateWarp requires ep16_royal >= 18, matching Dimension Warper MkII. This also protects Last Warp. Nillem and Swaying Space retain all instance creation, party, quest and cooldown checks. The similarly named portal at prt_lib (88,90) actually enters Ritual of Blessing and was deliberately not used.

Corrected the access catalog's Old Glast Heim Challenge mapping: the standard Old Glast Heim route is a different entrance. Added persistent geometry/name checks to the source release gate and four native access-boundary cases for Room of Consciousness.

No confirmed instance gameplay-script defect surfaced in the executed tests, so those scripts were not changed.

## Validation

- All 102 instance definitions have cached maps and walkable entry cells.
- Every literal instance_create/instance_enter name in active scripts resolves to an instance definition.
- Manifest integrity passed: effective definitions, maps, enabled scripts and required menu entries.
- Warper audit passed for 618 destinations overall, including 268 dungeon destinations; all have matching navigation registrations.
- Native tests run actual extracted script bodies with controlled world, clock, inventory and movement boundaries. Sanitizers and memory teardown checks passed.

| Test suite | Checks/assertions | Result |
| --- | ---: | --- |
| Instance combat rules | 815 per build, Renewal and Pre-Renewal | Pass |
| Instance entry and reward regressions | 29 | Pass |
| Final instance Warper, including Room of Consciousness | 426 | Pass |
| Immortal dialogue/participants/rewards | 39 | Pass |
| Airship briefing with offline members | 14 | Pass |
| Bioresearch Laboratory | 241 | Pass |
| Alice Twisted Madness | 217 | Pass |
| Episode 21 finale flow | 46 across 16 cases | Pass |
| Episode 21 checkpoint flow | 113 | Pass |

Total: 2,755 counted checks/assertions across the above suites, plus database, catalog and geometry checks. The initial ten-suite run passed; the updated Warper was tested again after adding Room of Consciousness (426 checks supersede the initial 410).

Isolated final candidate startup passed against disposable SQL initialized from 21 schema files. No startup errors were reported. git diff --check passed.

## Reference-list differences

- Garden of Time is represented by Lake of Fire and Hall of Life.
- Endless Tower/Cellar is represented by Endless Tower.
- Hidden Flower Garden is available through Episode 17.2 Security Area 1 / 2.
- Lost in Time, OS, Cor, episode instances, and several classic instances are grouped under the More Episode Instances / More Classic Instances submenus.
- Tower of Trials is explicitly unimplemented in our installed catalog. No placeholder or misleading working route was added.
- Room of Consciousness was the confirmed missing menu entry and is now included.

## Deployment

Final candidate deployed to 192.168.10.18 after isolated validation and a zero-online-player check. Only the Warper script was installed; the map container was restarted, with backup and startup-log verification.

Backup and live startup evidence: `/app/rathena-deploy-backups/instance-audit-20260917/`.
Final deployed Warper SHA-256: `d1deffbd085fde409d3ba0f74c3b76d17c37bc324fb61994a67824dacb93f5aa`.
Linux test logs: `/home/alpha/instance-audit-20260917/`; final native Warper artifacts: `/home/alpha/instance-warper-room-audit/`.

## Limits

These checks verify definitions, entrances, selected access/cooldown/reward/encounter flows and server startup. They are not a complete player walkthrough of all 102 instances, every boss phase or client visual asset. Existing unrelated item-price/monster-stat startup warnings remain. Client navigation files were not regenerated.
