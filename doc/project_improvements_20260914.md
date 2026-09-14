# Project improvements and acceptance — 14 September 2026

This pass covers bank/storage, progression, client resources, release reliability,
and the Main Office progression guide. Automated evidence is kept separately
from rendered gameplay acceptance. The server changes were deployed on
14 September 2026 at 11:22 Bangkok time (04:22 UTC).

Evidence directory: `../improvement-20260914` beside this repository; remote
directory: `/app/rathena-builds/improvement-20260914`. Portable receipts are in
[`evidence/project_improvements_20260914/`](evidence/project_improvements_20260914/).

## Changes

- Expanded the existing Progression Guide at `pn_office,108,80`. It now points
  new Chapter 1 players to the Small Ash Tree rather than Robin, whose Zero Cell
  investigation requires Chapter 1 completion. Advice follows Chapter 2 stages
  0–12, distinguishes completed encounters from pending reports, and handles
  unknown stages without changing them.
- Added read-only availability and cooldown advice for all seven Biosphere
  habitat hunts, the repeatable Phantom expedition, and Raised Land patrols.
  The original NPCs retain acceptance, rewards, capacity and entrance checks.
  Equipment advice links existing refiner, enchant, crown and material services.
- Added `Verify Client.cmd` and the shipping PowerShell checksum verifier.
  It detects missing files, old patches and damaged payloads, and rejects invalid
  manifests, duplicate paths and paths outside the installation. It complements
  the existing fast launcher checks.
- Corrected three item resource-name typos and removed the checksum verifier's
  dependency on PowerShell command auto-loading. The cumulative client update
  is installed locally; see the [asset follow-up](client_asset_followup_20260914.md).
- Added `tools/admin/health_check.py` and a five-minute systemd timer. Checks
  cover service state, recent errors and interserver disconnect/DNS warnings,
  verified backup age/integrity, the backup timer, and disk usage. Reports contain
  status and error counts without account identifiers or raw SQL/client logs.
- Found deployment drift: the live monster tables and seed SQL still used
  16-bit `attack2`, while the repository's existing migration and templates use
  unsigned 32-bit columns. Applied the existing migration to all four live tables
  and installed the canonical SQL files. Widening the schema does not retune
  monsters or restore values that may previously have been truncated.

## Deployment

The rollout created a fresh database backup and verified its restore in an
isolated database. No players were online when the map service was restarted.
Before/after comparisons found identical contents in all 34 checked player,
economy and monster tables. The four production server binaries were unchanged.
Login, character, map and web ports were reachable from the Windows workstation.

The guide is active and the health timer is enabled. Its first scheduled run at
11:27 Bangkok time passed all checks, including the existing
`rathena-database-backup.timer`. Previous files, backup and deployment receipts
remain in the remote `deployment/` directory. Client verification tools and the
matching manifest were installed in the local client; changed files have a
separate local backup receipt.

## Verification

| Area | Evidence |
|---|---|
| Full release gate | All 40 checks passed against the isolated candidate; includes native quest/instance checks and map startup |
| Fresh native build | `build-result.json` on the Docker host; isolated networkless build |
| Storage SQL | 185 real SQL assertions plus a MariaDB crash before commit |
| Bank/storage protocol | 15 bank cases and 17 storage scenarios passed using fresh private schemas and synthetic accounts; reconnects, replay, capacity, sharing, page fees and committed/uncommitted map crashes |
| Card filter | 48 non-card deposits rejected and 12 card deposits accepted through real inventory/cart packets by normal and GM fixture accounts |
| Progression guide | 34 real login/map/NPC-dialog scenarios; quests, registers, items, wallet and bank unchanged |
| Native Windows bank | All four control, refresh, transport and DLL-loader fixtures passed |
| Client archives | 242,185 payloads across ten active archives decompressed with size checks; no errors, index duplicates or encrypted skipped payloads |
| Held item resources | All 74 distinct held item IDs have metadata and referenced inventory/collection artwork |
| Chapter 2 client | Installed precedence, Lua callbacks, current recipes and map walkability passed |
| Client distribution | Reconstructed published full client plus the existing v2.2 ItemFix and new verifier; all 5,625 manifest entries passed size/SHA256 verification |
| Client asset follow-up | Exactly three resource fields changed across 26,908 loaded records; six replacement bitmaps verified; all 23 guarded resource repairs passed |
| Windows checks | Eight launcher tests and five checksum-verifier tests passed, including a multi-file regression |
| Health | Current live services, restored backup and disk checks passed; four failure-path unit tests passed |
| SQL migration | Four tables widened; existing values preserved, repeat application passed, unsigned 32-bit maximum accepted in an isolated database |

Exact counts, source identities and final release/deployment results belong in the
adjacent JSON receipts. The original failed gate logs remain available alongside
corrected runs; failures were not relabeled as passes.
The 40-check server gate belongs to the deployed candidate. The later client-only
asset/verifier changes were checked separately as recorded above.

## Rendered acceptance still required

Native desktop control was unavailable during this earlier pass. The later
[six-area audit](audit_all_20260914.md) reached the QA world and captured the
bank panel using the Windows runtime; automated transaction input remained
incomplete. The following diagnostics record the earlier connection state.

After the owner opened ChatGPT desktop and confirmed the plugin was
enabled, a fresh connection exposed Edge and Brave but no native apps. The local
plugin configuration also confirms both Computer Use entries are enabled.
The owner also confirmed Settings > Computer Use > Any App was already on.
A fresh `@Computer` request was also attempted. The helper now starts, but its
app-generated configuration enables only the browser surface and registers only
the browser service. See `computer-use-diagnostic.json` in the portable receipts.

The [30-scenario gameplay checklist](rendered_acceptance_20260914.md) records
the setup and expected results for the remaining playthroughs. None of those
rendered checks is marked as passed by protocol-only evidence.

- Complete representative quest chains and full boss encounters in Ragexe.
- Inspect the bank's actual purchase/sale feedback with a rendered client.
- Exercise overlapping dialogs, party leader changes and checkpoint reconnects
  with two rendered clients.
- Confirm the reported Prontera navigation “No Image” behavior. The winning
  512×512 `data.grf` bitmap was extracted and visually inspected: it is a real
  Prontera map. Its presence does not reproduce or explain the in-game issue.
- Triage the remaining 1,595 catalog item IDs with unresolved raw icon references.
  None are among the 74 currently held IDs. These are catalog candidates, not
  1,595 confirmed gameplay failures; acquisition and runtime fallbacks vary.

## Player use

Visit Main Office (`@office`) and the Progression Guide at 108,80. Choose a
story objective, repeatable quest or equipment goal. Navigation supplies
directions; the guide never warps, charges, grants rewards or advances quests.

After extracting the full 13 September client, apply
`PN-Client-Update-20260914-AssetFix.zip` with the game closed, run `Check Client.cmd`, then
`Verify Client.cmd`. The update includes the previous Bank v2.2 ItemFix and its
matching complete checksum manifest. No new game executable or GRF is required.
The cumulative update also includes the three resource-name corrections and can
be applied over the earlier 14 September update. It is 599,093 bytes, with SHA256
`043f6eea174c3020ac7f6f61ea3a6d3848cb5a8cad7b4d7afaf56c0f2831e18a`.
The full manifest describes the supplied distribution; intentional edits to
supplied settings will be reported as differences. Extra screenshots and saves
are allowed.

## Administrator use

Run `python3 tools/admin/health_check.py` for a read-only report. The systemd
service writes `/var/lib/rathena-health/latest.json`; failures also appear under
`systemctl status rathena-health.service` and `journalctl -u rathena-health.service`.
There is no email, chat or third-party telemetry integration.

The default alert thresholds are 30 hours since the latest successful restored
backup, less than 5 GiB free, or more than 90% filesystem use. Recent service
errors are retained for a 15-minute window, including recovered reconnect events.
