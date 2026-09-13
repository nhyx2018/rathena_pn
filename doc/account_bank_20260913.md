# Account bank delivery ? 2026-09-13

Implemented the supplied bank panel with account-wide character sharing and the exact diamond/note exchange prices. Installed on 192.168.10.18 and the current Windows client. Use @bank or Alt+B after login.

## Correctness fixes and evidence

- Made inventory, wallet, account bank and transaction journal atomic. Converted the existing financial tables to InnoDB without changing row contents. Stock banking now waits for the same commit acknowledgement.
- Added replay protection, checked integer arithmetic, item eligibility/capacity checks, retry handling, deferred spending/saving/logout and character-cache synchronization.
- Fixed integration defects found before deployment: missing character ID in bank replies; per-refresh connections triggering flood protection; missing bank item-log enum; a Unicode window-procedure mismatch; and preset arithmetic overflowing after a maximal pasted number. Malformed replies are rejected before UI arithmetic.
- 500,000 randomized arithmetic cases and boundary/fee cases passed under address and undefined-behavior sanitizers. Production-handler fixtures passed authentication, fragmentation, duplicate/stale request/ack, capacity, item batch rollback and native acknowledgement checks.
- 44 real MariaDB checks passed. Killing the database between financial writes and COMMIT restored the original wallet, bank and inventory.
- Actual isolated login/character/map sessions passed 9 groups: repeated/fragmented requests, rejection boundaries, exact currency fees, item logs, native banking, sibling character sharing, SQL fault plus socket loss/retry, committed map-crash recovery, and rollback of an uncommitted purchase after a map crash. No production accounts or data were used.
- The old-schema migration passed with existing synthetic rows and repeat application. All 26 source release checks passed, including existing reform and inventory regression coverage.
- Native Windows tests passed the real API hooks, persistent companion transport, partial replies, stale sessions, complete FontScale forwarding chain, preserved original font scaling, hidden unauthenticated panel and numeric/button boundaries.

## Deployment

Full SQL backup: `/app/rathena-builds/bank-20260913/deployment/database-backup.sql` (22,753,556 bytes, owner-only access). Source/executable backups and detailed hashes are in the same deployment directory. Client originals and rollback receipt: `server-work/bank-20260913/client-backup`.

All login/character/map services started successfully. The running map and character executable hashes match the tested candidates. All 2 character rows, 2 account-registry rows, 112 inventory rows, 2,590 item-log rows and all storage/cart rows remained byte-for-byte equivalent in ordered SQL output across migration/restart. There were no online characters during deployment.

Local evidence: `server-work/bank-20260913/{sql-report.json,migration-report.json,live-report.json,source-release.json,client-tests.json,deployment/report.json}`. The client executable, DATA.INI, font settings and archives were preserved. Server source changes include Makefile dependencies so edits to bank includes trigger rebuilds.

## Verification limits

Automated proofs cover real SQL/server processes and the actual Windows extensions. They do not constitute a manual rendered Ragexe login and bank interaction. Bank and wallet caps stay at 2,147,483,647, and prolonged SQL failure intentionally holds the character until the pending save is resolved. No claim of universal bug freedom is made.
