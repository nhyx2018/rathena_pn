# Client asset follow-up - 14 September 2026

Installed three guarded resource-name corrections in the local client and built
`PN-Client-Update-20260914-AssetFix.zip`. This cumulative update applies after the
13 September full client, with or without the earlier 14 September update.
The server deployment and player data were not changed during this follow-up.

| Item | Correction | Reviewed source lead |
|---|---|---|
| 5054 Assassin Mask | Corrected its identified resource to the existing Assassin Mask artwork shared with 5096. The missing inventory icon resolves; the collection image is byte-for-byte identical. | Sleipnir seal reward, `npc/quests/seals/sleipnir_seal.txt:357` |
| 6417 Silvervine Fruit | Corrected the unidentified resource to the item's own existing identified artwork. | Merchant refund, `npc/re/merchants/enchan_mal.txt:701` |
| 11534 Coconut Juice | Corrected the unidentified resource to the item's own existing identified artwork. | Dewata quest reward, `npc/re/quests/quests_dewata.txt:1026` |

Each correction applies only when its original misspelled resource is present.
Names, descriptions, slots, stats and independently corrected artwork are
preserved. The two unidentified-resource fixes do not imply that the normal
identified items previously showed broken icons.

The full package check also encountered a child Windows PowerShell session in
which `Get-FileHash` was unavailable. The verifier now streams SHA256 through the
.NET runtime directly. Its manifest validation and mismatch behavior remain the
same; all five verifier tests and the complete package check passed afterward.

## Verification

- The actual installed Lua loader produced 26,908 item records. Comparison with
  the earlier audit found exactly three resource-field changes and no other
  changes to names or resource fields.
- The Lua regression verifies all item fields, repeat application and custom
  corrections. All 23 reviewed repairs pass: the existing 20 helmet references
  and these three additions.
- All six replacement bitmap references exist in the effective archive stack,
  decompress correctly and have recorded hashes. Five previously missing bitmap
  references are resolved; Assassin Mask's existing collection bitmap is preserved.
- The replacement collection artwork was extracted and visually inspected.
  This is asset inspection, not a rendered Ragexe session.
- Quick client checks and all 5,625 manifest entries passed on the reconstructed
  distribution. The installed local loader then passed the same Lua regression.
- Four local files were updated with a rollback receipt under
  `../improvement-20260914/client-update-assets/installed-backup/` beside the repo.

The archive is 599,093 bytes. SHA256:
`043f6eea174c3020ac7f6f61ea3a6d3848cb5a8cad7b4d7afaf56c0f2831e18a`.
Portable receipts are in `doc/evidence/project_improvements_20260914/`, including
`client-update-assets.json`, `asset-fix-resources.json` and
`asset-fix-metadata-diff.json`.

## Remaining asset leads

The baseline scan covered 920 NPC files reached through the local Renewal import
graph. Of the original 1,598 candidate item IDs, 38 had literal grant, item-script
output or declared monster-drop leads, 306 had only general source references,
and 1,254 had no lead in those scanned categories. These categories do not prove
runtime availability: item groups, dynamic variables, conditions, achievements,
barter and monster summons require additional tracing.

There were 55 item-ID/name matches in custom NPC sources. Five costumes
(19293, 19670, 19855, 31375 and 31899) appear in the view-only Fashion Catalogue;
that NPC displays names and does not sell those costumes. Two enchant IDs
(29046 and 29362) appear in the fashion enchant mappings. The other 48 matches
include quest IDs, monster IDs, rates and ordinary words that overlap item names.
A raw token match must not be counted as a confirmed item acquisition path.

Two unresolved coins (7915 and 7916) appear in monster drop declarations. The
scanned NPC files contained no literal spawn for those four minion IDs; dynamic
summons were not resolved. Another 33 candidate items are outputs of item scripts,
mostly boxes whose own acquisition paths still require review.

After the three corrections, 1,595 item IDs retain unresolved raw references.
All 74 previously observed held item IDs still have metadata and referenced
artwork. The full priority data and source hashes remain in
`../improvement-20260914/asset-priorities.json` beside the repo.

## Desktop acceptance

This section records the earlier connection state. The later
[six-area audit](audit_all_20260914.md) captured the actual QA bank panel with
the Windows runtime; its automated transaction input remained incomplete.

The owner enabled the plugin, confirmed Any App was on and sent a fresh
`@Computer` request. The helper started, but the app-generated configuration
contained `CUA_REPL_ENABLED_SURFACES=browser` and registered only the browser
service. No native apps were exposed. The configuration was inspected without
modifying it; the reason the app omitted the native surface remains unresolved.
See `computer-use-diagnostic.json` in the portable receipts. The
[30 rendered scenarios](rendered_acceptance_20260914.md) remain pending.
