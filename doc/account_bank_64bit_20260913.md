# Bank opening and 64-bit balances — 2026-09-13

The Master Account panel now opens through the game bank button, the native balance-query path, NPC `openbank`, `@bank`, Alt+B and Ctrl+B. All characters on one game login share the bank. Its capacity is 9,223,372,036,854,775,807 zeny; the character wallet retains its 2,147,483,647 cap.

## Defects corrected

The original integration did not route native bank or NPC UI packets to the extension, and the server's `@bank` command only printed instructions. Protocol v2 authenticates the companion while the panel is hidden and carries separate open notifications. The client distinguishes those notifications from transaction replies and rejects stale login generations. A stock window opened before attachment is closed when the companion becomes ready.

The bank had several independent 32-bit restrictions: `map_session_data::bank_vault`, the registry load cast, `pc_setparam`'s narrowed local value, and the generic `pc_setreg2` clamp. The last defect was caught by the real character-switch test: an atomic bank commit succeeded, then the ordinary registry flush overwrote it with INT_MAX. The bank registry now preserves the full value through both save paths. Other registry clamps and the character wallet cap are retained.

Bank arithmetic checks available funds and capacity before adding or multiplying. The client renders exact integers, including values above 2^53. Zeny logging and `zenylog.amount` now preserve signed 64-bit transaction amounts. Existing nonce, replay, ownership, item eligibility, pending-save and atomic SQL protections remain in use.

## Verification

- 500,000 randomized arithmetic cases, boundary cases and production bank-handler fixtures passed under address and undefined-behavior sanitizers.
- 49 checks against actual character-server SQL code passed, including failed writes, ownership, replay, reconnect, INT64_MAX persistence and cache synchronization. A forced MariaDB crash rolled back the uncommitted financial writes.
- All 14 isolated login/character/map scenarios passed. These include actual bank-button, balance-query, command and NPC opening; committed and uncommitted map crashes; exact item fees and wide log entries; the ordinary registry flush; character sharing at 2^31, 2^53 and INT64_MAX; and rejection of native withdrawals into a full wallet.
- The log migration preserved existing rows on repeated application and retained positive and negative 64-bit values.
- Native Windows transport, DLL forwarding, original font scaling, input constraints, and normal/max-balance renders passed. Idle and interleaved open notifications cannot acknowledge financial actions.
- All 38 full release checks passed, including the existing quest, instance and inventory regressions.

## Deployment

Installed the matching server binaries, sources, log migration and Windows extension. The server completed login/character/map handshakes; a subsequent authenticated login and character-list probe passed. A read-only bank protocol probe confirmed version 2, the two distinct limits and rejection of unauthenticated financial access. The temporary login row was removed without advancing the account allocator.

Ordered row hashes for 11 player, bank, quest, inventory and log tables were unchanged across migration and restart. The original client executable, font configuration and archive configuration were preserved. SQL and file backups are retained under `/app/rathena-builds/bank-wide-20260913/deployment` and the local `server-work/bank-wide-20260913/client-backup`.

Evidence is in `server-work/bank-wide-20260913/final-report.json` and its referenced reports; server evidence uses the matching directory under `/app/rathena-builds`. The tests exercise real server processes and the shipping Windows code, but do not constitute a manual rendered Ragexe playthrough.

Deploy both sides together. Keep the wide log column on rollback, and do not restore a 32-bit bank binary after accounts acquire balances above its old cap. See [the bank build and installation guide](../client-patch/account_bank/README.md).
