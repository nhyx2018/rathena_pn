# Account bank

Open with the normal bank button, an NPC using `openbank`, `@bank`, **Alt+B**, or **Ctrl+B** after logging into a character. The balance is shared across characters on that game login. The Master Account panel follows the supplied reference and shows bank and wallet balances, deposit/withdraw, item exchanges, presets, Max choices, Refresh and status.

| Currency | Buy from bank | Sell to bank |
|---|---:|---:|
| 17Carat Diamond (6024) | 501,000,000 | 499,000,000 |
| 1M Zeny Ticket (12781) | 1,002,000 | 998,000 |

The bank holds up to 9,223,372,036,854,775,807 zeny (signed 64-bit capacity). The character wallet remains capped at 2,147,483,647. Amounts use checked integer arithmetic throughout the client, account registry, server and SQL journal; no floating-point conversion is involved. Exchange proceeds and costs use the bank balance. Bound, rental, modified, equipped and favorite items are excluded from sale. The ticket is a non-consuming Etc item and cannot be sold to ordinary NPC shops.

Item quantities start at **1**. Each row shows the maximum quantity currently available to buy or sell. Deposit on-hand zeny first to fund purchases. Buy requires enough bank zeny and inventory space/weight; Sell requires eligible items and room in the bank. A zero, empty or invalid quantity disables both actions. Character changes reset item quantities to one and require a fresh authenticated balance before enabling transactions.

Panel **v2.2** keeps valid controls enabled during automatic balance checks and avoids repainting unchanged replies. A financial click during a refresh waits for the reply, is checked against the latest snapshot, and submits once with the clicked quantity. Failed replies, pending saves and session changes cancel the waiting action. Buffered painting and child-control clipping reduce flicker; repeated open notifications preserve input focus. See the [refresh repair and verification](../../doc/bank_refresh_20260913.md).

Each disabled item action shows the exact bank-Zeny shortfall, missing eligible items, inventory capacity, invalid quantity, bank limit or connection/save status. For example, a bank balance of 1,000,000 needs another **2,000 Zeny deposited** before buying one 1M Zeny Ticket. The character's on-hand balance does not fund the purchase until deposited.

The server validates the active character, both existing login tokens and source IP. Tokens stay in client memory. A separate persistent connection uses the existing map port; no password, web account or extra public service is added. Nonces and request IDs prevent repeated transactions. The DLL observes successful game sends without changing their bytes. The original font extension is retained as `FontScaleOriginal.dll`; the client executable, GRFs and font settings are preserved.

The character server commits inventory, wallet, account registry and the `pn_bank_commits` journal in one InnoDB transaction. Only a committed transaction receives success. Stock native deposits and withdrawals use this path too. Spending, split saves, map changes and logout are deferred while saving; retries carry current state, and repeated SQL commits do not restore old snapshots. If SQL is unavailable the character stays locked until saving recovers. An unacknowledged operation after a server crash must be checked with Refresh/relogin before trying again.

Protocol v2 authenticates a companion automatically while the panel is hidden. Native open, native balance-query and NPC bank UI requests send a separate open notification on that connection; the stock window is dismissed. Notifications never acknowledge financial actions, and stale login generations cannot open the panel. Hidden keepalives run every 15 seconds. If the companion is not ready yet, native banking remains available and is replaced when attachment succeeds. Deploy the server and client together; v1 companions are rejected.

Build with `build.sh /absolute/output/path` using the i686 MinGW GCC toolchain. `BankTransportTest.exe` tests the shipping hooks and persistent socket with a loopback server. `BankLoaderTest.exe` needs the verified original font DLL and a 1.10 FontScale.ini alongside the build. `BankPreview.exe` tests inputs and renders its own hidden window to bank-preview.bmp.

`BankUITest.exe` drives the production panel's real Windows edit and button controls with a recording transport. It covers all four Buy/Sell actions, default quantities, invalid inputs, duplicate/pending requests, funds, eligible items, capacity, unavailable banking and session changes. The old zero-quantity build fails the default-control regression. See [the control repair](../../doc/bank_controls_20260913.md) for scope and evidence.

The control test also checks timer refreshes for zero enable-state changes and no repaint of unchanged state, all six queued financial actions, exact clicked quantities, fresh-snapshot rejection, and cancellation on every non-success reply or session change. `BankRefreshTest.exe` combines the production panel and transport with delayed, fragmented loopback responses to exercise real hook/worker/message delivery, purchase commit and logout cancellation.

`install.py --client-root CLIENT --build BUILD --backup NEW_BACKUP` installs with backups, hashes, automatic rollback on failure and launcher checks. Close Ragexe first. To revert unchanged installed files: `install.py --client-root CLIENT --backup BACKUP --rollback`. Distribute the matching DLLs, original font DLL, INI, metadata, launcher and licenses together.

Optional `--diagnostics` sets `Diagnostics=1` in `BankUI.ini`. It writes a local latest-state report containing connection/control flags and rejection reason codes, without identities, balances, item counts, tokens or packets. Default installations leave diagnostics disabled. See the [diagnostic details](../../doc/bank_refresh_20260913.md#local-diagnostics).

Before server deployment, stop game writers, back up SQL, apply `upgrade_20260913_account_bank.sql` to the character database and `upgrade_20260913_account_bank_logs.sql` to the map log database, then deploy the matching map and character servers and item override. Custom SQL table names require adapting the migrations. A fresh installation includes both changes in main.sql and logs.sql. Keep old executables and source for rollback; retaining converted InnoDB tables preserves current player data.

For the 64-bit update also apply `upgrade_20260913_account_bank_64bit.sql` to the map log database. It widens `zenylog.amount`; the account registry and bank journal already use signed BIGINT. Keep the wide log column on rollback. Once balances exceed the old cap, do not restore a 32-bit bank binary: it would truncate the account value during login.

See [the 64-bit bank report](../../doc/account_bank_64bit_20260913.md) for current deployment and test evidence. No automated check proves every rendered gameplay interaction; the isolated login/char/map tests and native Windows DLL tests are distinct from a manual Ragexe playthrough.
