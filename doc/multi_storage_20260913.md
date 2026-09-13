# Mystic Box multi-storage — 13 September 2026

The Mystic Box menu provides Storage I–X, Master Storage I–VI, Guild Storage, Card Storage, Character Bound Storage, Rename Storages, Reorder Storages and Expand Storages. Open it with `@storage`, `@mstorage`, or the Main Office Kafra.

## Player rules

- Storage I–III and Master Storage I start unlocked. Card Storage and Character Bound Storage are also available immediately.
- Each additional regular or Master page costs **50,000,000 zeny from the current character's wallet**, after an explicit purchase confirmation. A purchase unlocks one complete **600-slot page**, permanently for the game login.
- Regular, Master and Card pages, paid unlocks, names and menu order are shared by every character on that login.
- Character Bound Storage is private to the character and accepts only character-bound items. Card Storage accepts cards. Existing item storage restrictions still apply.
- Guild Storage retains native guild membership, permissions, capacity and concurrent-use rules.
- Names support 1–23 printable English characters, without colons, color codes or surrounding spaces. An empty name restores the default. Reordering changes menu positions while page inventories retain their identity.
- Existing normal storage is **Storage I**. Its items are not moved to a new table.

The menu and storage windows use the existing client protocol. No replacement client archive or DLL is needed for this feature. Choose a page and close the NPC dialog when prompted to open its storage window.

## Persistence and failure handling

Personal transfers commit inventory or cart, the selected page, wallet and a request journal in one InnoDB transaction. Expansion commits its fee, entitlement and journal together. A repeated request acknowledges an existing commit without applying an old item snapshot again.

The map server serializes each character's bank/storage operations. Spending, item removal, page switching, ordinary saves and logout wait while a commit is pending. Requests retry after a failed save. Positive rewards received during a pending save are included in the subsequent ordinary save. An uncommitted transaction rolls back after a process/database failure.

Page loads and commit acknowledgements include the character, page, session nonce and request sequence. Delayed replies from another operation cannot replace the current page or clear its unsaved state. Storage stacking also compares random options and enchant grade. Inventory metadata is checked before adding a deposit to its destination.

Storage names use the permanent account registry API. Menu layout validation runs once per opening. Makefile dependencies include all new implementation fragments so incremental builds include their changes.

## Schema and deployment

Apply [upgrade_20260913_multi_storage.sql](../sql-files/upgrades/upgrade_20260913_multi_storage.sql) to the character database with game writers stopped and a verified backup. This migration assumes the standard `storage` and `cart_inventory` table names. Adapt it first if those tables were renamed locally.

| Page | Internal ID | SQL table / owner |
| --- | ---: | --- |
| Storage I | 0 | `storage` / account |
| Storage II–X | 100–108 | `pn_storage_02`–`pn_storage_10` / account |
| Master Storage I–VI | 110–115 | `pn_master_storage_01`–`pn_master_storage_06` / account |
| Card Storage | 116 | `pn_card_storage` / account |
| Character Bound Storage | 117 | `pn_character_storage` / character |

The migration converts normal storage and carts to InnoDB, creates the new pages and adds `pn_storage_commits`. New installations receive the same schema through `main.sql`. The character server refuses startup if the required transaction tables are missing or use a nontransactional engine.

Deploy matching map and character binaries with [pn_storage.yml](../conf/pn_storage.yml), its import in `inter_server.yml`, the custom NPC and its script import. Keep local storage overrides consistent with these reserved IDs. Character deletion removes only that character's private bound page.

Keep the journal for retry deduplication and operational review. If a rollback is needed after players have used new pages, retain their tables and entitlements; restore a coherent server version or export those items under controlled maintenance. Do not restore an old database over later player activity.

## Validation

The actual character-server SQL implementation passed **185 assertions** covering every configured personal page, owner checks, account sharing, character isolation, exact expansion fees, insufficient funds, duplicate unlocks, item metadata, cart/inventory independence, transaction-engine requirements and rollback at each write stage. A real disposable MariaDB crash before commit preserved the original inventory and wallet and recovered no uncommitted page or journal rows.

**13 authenticated native storage scenarios passed** through actual login, character and map processes. Coverage includes every menu entry, initial locks, normal/premium deposits and withdrawals, card/bound filters, names and ordering, cross-character persistence, the 50M fee, insufficient funds, disconnect/retry recovery, carts, invalid packets, guild access rejection, a full 600-slot page and committed/uncommitted transfers across real map crashes.

The existing **14 native bank scenarios also passed** against the storage build, including 64-bit limits and financial crash recovery. Reapplying the storage migration preserved a complete ordered dump of fixture data. Automated protocol sessions do not constitute a manual Ragexe playthrough.

The final candidate passed all **38 release checks**, including sanitizer regressions and isolated startup. Deployment completed at **12:07:54 UTC on 13 September 2026** with no players online. A full SQL backup and matching prior files were retained. Ordered hashes of **13 player and financial tables** were unchanged through migration and restart, and all **20 required storage transaction tables** use InnoDB. Running map/character binary hashes match the validated build. A subsequent authenticated production probe received the character list, verified the original wallet cap and removed its temporary login without advancing the account allocator. See the [verification record](evidence/multi_storage_20260913.json).

To reproduce against a compiled Linux checkout, use a local `rathena:local` builder/runtime image with MariaDB client libraries and the `mariadb:noble` database image. The live tests also need host Python, Docker and `nsenter` privileges. Tests create fresh databases on internal Docker networks, refuse existing fixture names, and remove only their own fixtures.

```sh
export PN_STORAGE_CANDIDATE="$PWD"
export PN_STORAGE_TEST_ROOT=/tmp/pn-multi-storage-proof
python3 tools/ci/multi_storage_sql_test.py
python3 tools/ci/multi_storage_live_test.py
```

`PN_STORAGE_IMAGE` can select an equivalent local runtime image. Evidence stays under the test root. Native assertions are in [multi_storage_sql_runtime.cpp](../tools/ci/multi_storage_sql_runtime.cpp); authenticated client scenarios are in [multi_storage_live_client.py](../tools/ci/multi_storage_live_client.py).
