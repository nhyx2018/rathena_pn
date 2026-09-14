# Reward fixes and verification — 14 September 2026

Two confirmed purchase defects were fixed in source and deployed to 192.168.10.18. Fashion Points now rechecks balance and selected-item capacity after the confirmation dialogue, before charging points. KVM now checks capacity for the actual selected reward after confirmation, before charging points. Previously, state changes while the dialogue was open could produce a negative Fashion Points balance or charge KVM Points without delivering the item.

The deployment preserved existing live Fashion Points wording and headers. Only the tested guard additions were applied; the post-confirmation purchase bodies match the tested source. Deployment verified no online characters, retained original files, restarted login before map, checked map readiness without startup errors, and verified both deployed hashes. Backup: `/app/rathena-builds/reward-completion-20260914/deployment-backup`.

## Verification

The new `tools/ci/finalbattle_current_reward_test.py` checks the current, unchanged Final Battle reward bodies using an explicitly scoped native fixture. It does not repin or bypass the historical broad callback-closure gate. The three reward bodies and daily helper were reviewed against the earlier version; intervening changes were outside these reward bodies.

- 574 native cases and 26,296 assertions passed, with ASan and UBSan.
- Eight shop cases exercise real VM dialogue suspension and resumption: normal purchase, lost balance, overweight inventory, and unavailable inventory slots for each shop.
- Both original shop implementations fail the corresponding negative controls, reproducing the defects.
- Three historical reward failure controls passed, with 190 assertions.
- `git diff --check` passed.

The fixture uses explicit world, persistence and transport doubles. It does not prove SQL crash durability, arbitrary callback purity, or equivalence to the deployed server binary. In-game visual interaction was not performed in this pass.

Reproduction in an environment with the native build dependencies:

```sh
python3 tools/ci/finalbattle_current_reward_test.py --native-build-dir /tmp/reward-current --shop-cases tools/ci/shop_purchase_resume_cases.inc
```

Use a fresh build directory. Detailed receipts and deployment records are in the sibling Client-Packages directory, `reward-completion-20260914/` (`receipt.json`, `negative-controls.jsonl`, `deployment.jsonl`, `verification.jsonl`).

## Original audit scope

The 443 flagged IDs have no definitions in the checked live database and no holdings in the checked player tables; no missing-item placeholders or destructive catalog removal were necessary. Quest navigation and displayed reward callbacks passed the earlier checks. Effective archive payload checks passed at the format-specific depth recorded in `client_content_audit_20260914.md`.

The conservative acquisition audit still reports 199 dynamic grant lines. A numeric candidate review distinguished quest IDs, monster IDs, consumed inputs, and view-only catalog entries from grants, and led to the two confirmed fixes above. This is not a claim that every dynamic branch, reward transaction, or opaque archive format has been exhaustively verified. The historical broad callback-closure certification remains separate from the passing current reward fixture.
