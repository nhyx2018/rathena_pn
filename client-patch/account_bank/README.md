# Account bank

Open with `@bank`, **Alt+B**, or **Ctrl+B** after logging into a character. The balance is shared across characters on that game login. The panel follows the supplied reference and shows bank and wallet balances, deposit/withdraw, item exchanges, presets, Max choices, Refresh and status.

| Currency | Buy from bank | Sell to bank |
|---|---:|---:|
| 17Carat Diamond (6024) | 501,000,000 | 499,000,000 |
| 1M Zeny (12781) | 1,002,000 | 998,000 |

Bank and wallet limits remain 2,147,483,647 zeny each. Exchange proceeds and costs use the bank balance. Bound, rental, modified, equipped and favorite items are excluded from sale. The note is a non-consuming Etc item and cannot be sold to ordinary NPC shops.

The server validates the active character, both existing login tokens and source IP. Tokens stay in client memory. A separate persistent connection uses the existing map port; no password, web account or extra public service is added. Nonces and request IDs prevent repeated transactions. The DLL observes successful game sends without changing their bytes. The original font extension is retained as `FontScaleOriginal.dll`; the client executable, GRFs and font settings are preserved.

The character server commits inventory, wallet, account registry and the `pn_bank_commits` journal in one InnoDB transaction. Only a committed transaction receives success. Stock native deposits and withdrawals use this path too. Spending, split saves, map changes and logout are deferred while saving; retries carry current state, and repeated SQL commits do not restore old snapshots. If SQL is unavailable the character stays locked until saving recovers. An unacknowledged operation after a server crash must be checked with Refresh/relogin before trying again.

Build with `build.sh /absolute/output/path` using the i686 MinGW GCC toolchain. `BankTransportTest.exe` tests the shipping hooks and persistent socket with a loopback server. `BankLoaderTest.exe` needs the verified original font DLL and a 1.10 FontScale.ini alongside the build. `BankPreview.exe` tests inputs and renders its own hidden window to bank-preview.bmp.

`install.py --client-root CLIENT --build BUILD --backup NEW_BACKUP` installs with backups, hashes, automatic rollback on failure and launcher checks. Close Ragexe first. To revert unchanged installed files: `install.py --client-root CLIENT --backup BACKUP --rollback`. Distribute the matching DLLs, original font DLL, INI, metadata, launcher and licenses together.

Before server deployment, stop game writers, back up SQL, apply `upgrade_20260913_account_bank.sql` to the character database and `upgrade_20260913_account_bank_logs.sql` to the map log database, then deploy the matching map and character servers and item override. Custom SQL table names require adapting the migrations. A fresh installation includes both changes in main.sql and logs.sql. Keep old executables and source for rollback; retaining converted InnoDB tables preserves current player data.

See `doc/account_bank_20260913.md` for deployment and test evidence. No automated check proves every rendered gameplay interaction; the isolated login/char/map tests and native Windows DLL tests are distinct from a manual Ragexe playthrough.
