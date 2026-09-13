# 1M Zeny Ticket: Unknown Item repair

Purchased 1M Zeny Tickets appeared as **Unknown Item** because item `12781` was absent from the translated client item table. The bank metadata patch only renamed records that already existed, so it silently skipped the ticket. The server's item definition and bank exchange were already using the correct ID.

`SystemEN/AccountBankInfo.lua` now creates the missing record before applying the bank name and description. Both identified and unidentified registration paths have valid metadata. The record uses the client's existing coupon artwork for its inventory icon, detail image and ground sprite; resource names use explicit legacy byte escapes. Existing ticket resources on other installations are preserved. The description lists the bank prices and weight 1, matching the server's non-consuming Etc item.

## Installation

Download **PN-Bank-v2.2-ItemFix-20260913.zip** from the [client release](https://github.com/patnawa/rathena_pn/releases/tag/client-2026-09-13-bank64). Close the game, back up `BankUI.dll` and `SystemEN/AccountBankInfo.lua`, then replace those two files from the ZIP, merging the `SystemEN` folder. Keep the other files in that folder. Fully restart the game so its item table reloads. Existing tickets use the repaired definition; buying another ticket is unnecessary.

This cumulative patch contains the previously tested v2.2 DLL and the corrected metadata. The bank title still shows **v2.2**. The local repair changed only `SystemEN/AccountBankInfo.lua`, with a byte-for-byte backup and install receipt. No server deployment or player-data edit was needed.

## Verification

- The actual Lua 5.1 loader reproduces the defect with the previous patch: item `12781` is missing.
- The repaired loader registers **26,908 items**, including the ticket, through its production `main()` and `AddItem` callbacks.
- Both description paths include the ticket name, buy price **1,002,000**, sell price **998,000**, and weight **1**.
- All four exact resource paths resolve through the active GRF order. Inventory/detail BMP dimensions, sprite pixel runs and ACT sprite references pass validation.
- Unrelated item metadata is preserved. Repeated loads are safe, and an installation's existing ticket resource identifiers and extra fields remain intact.
- The installed metadata matches the tested source. The executable, bank/font DLLs, settings, archive order and item loader are unchanged.

Run the regression against a compatible installed client:

```text
python tools/ci/bank_item_metadata_test.py --client CLIENT_ROOT --lua LUA51_EXE --require-installed --report bank-ticket.json
```

The client area of `tools/ci/bug_hunt.py` includes this check. Its missing-record case runs even if a later base translation adds the item, preventing a return to the conditional-only patch.

The existing coupon detail artwork was inspected directly. After fully restarting the game, the owner confirmed that the existing ticket shows **1M Zeny Ticket** with the correct icon. This in-game confirmation is recorded separately from the loader and resource tests in the [verification record](evidence/bank_ticket_20260913.json).
