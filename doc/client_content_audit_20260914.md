# Item, quest and archive audit — 14 September 2026

Follow-up: [reward fixes and current native verification](reward_completion_20260914.md) records two deployed shop fixes and the passing 574-case current reward fixture. The historical broad callback gate remains unchanged. The observations below describe the initial audit pass.

This pass closes the 443 catalog-only IDs against live data, expands barter acquisition tracing, checks the effective override payloads, and checks client quest/reward callbacks. It does not certify all dynamic reward transactions or all archive visuals.

## 443 flagged item IDs

All 443 lack definitions in the live server's 29,590-item database, parsed through 22 imported YAML files. No flagged IDs were found in the live inventory, cart inventory, storage, guild storage, mail attachments or auction tables. They are unused client catalog records in the checked configuration. No catalog entries or player records were deleted, and no placeholder artwork was introduced.

Seven raw local/server item-file hashes differed. The conclusion therefore uses a separate parse of the live server's actual imports, rather than assuming local hashes were equivalent.

Evidence: `443-item-classification.json`, `live-items.jsonl`, `live-definitions.jsonl`.

## Acquisition auditor fix

The previous auditor started at custom barters and missed Renewal barter imports. `tools/audit_item_acquisition.py` now traverses `npc/barters.yml`, including Renewal and custom imports. Its imported-database regression passed.

The expanded local audit finds 6,207 candidate item acquisition paths, up from 5,056. Every traced item has client metadata. None of the 2,035 flagged catalog IDs has a static acquisition path. There remain 199 dynamic grant lines and prerequisite/runtime conditions that this conservative static analysis cannot resolve; absence of a path is not proof of universal unavailability.

Evidence: `acquisition.json`.

## Quest navigation and displayed rewards

- All 302,124 native Lua navigation callbacks passed; maximum represented distance 1,021.
- All four quest loaders passed with 11,473 records, 12,438 description callbacks and 114 reward callbacks per loader. Repeated overlays and preservation of custom guides passed.
- The 114 displayed item-reward callbacks reference 30 unique items. Every item has client metadata and a live server definition; every amount is positive.

These checks validate callback behavior and displayed reward data. They do not prove the displayed amounts match every script branch, nor that rewards survive full inventory, disconnects, retries or process crashes.

The deeper `finalbattle_reward_capacity_test.py` test rejected its historical callback baseline: engine, database, NPC and closure fingerprints differ from its reviewed baseline. Its 11 output-negative controls passed, but current reward-capacity execution was not reached. The old baseline was not repinned. Current transaction/reward-capacity verification remains open and needs a fresh review of the changed inputs before the strict native suite can be reused.

Evidence: `callback-tests.json`, `content-validation.json`.

## Archive overrides

The 1,022 changed collision relationships resolve to 995 unique effective resources:

| Check | Resources | Result |
| --- | ---: | --- |
| Complete bitmap decoding | 853 | Passed |
| Lua 5.1 compilation | 54 | Passed |
| XML parsing using declared encoding | 5 | Passed |
| GAT/GND/RSW signatures | 26 | Passed |
| Other formats | 57 | Prior payload integrity only |

Four XML files initially failed because the parser was passed multibyte-encoded byte strings. Decoding their declared encodings before parsing resolved the audit-tool issue; no XML assets needed changes.

Each resource's winning archive, SHA-256, decoded size where applicable and result are recorded in `content-validation.json`. Bytecode compilation does not execute every game callback. Signature checks are not full map-format validation. The 57 other payloads and visual intent of overrides remain outside semantic proof. The separately deployed three-town collision fix remains in place with zero walkability differences in the checked six-map set.

## Changes and limits

Only audit tooling and reports changed in this pass. Production was queried read-only; the live definition parse ran in a disposable network-isolated container with a read-only application mount. No server restart, client asset replacement or database mutation was needed.

The reproducible workstation scripts are `audit_content.py`, `classify.py`, `prepare_live_check.py` and `live_definitions.py`. Source changes are the barter import-root correction and its fixture. No claim is made that the remaining dynamic grants, reward transaction behavior or every visual override is fully audited.
