# Bank v2.2: stable refresh and responsive actions

Bank v2.1 used the same busy flag for balance reads and financial transactions. Every automatic refresh disabled all six action buttons, replaced the row messages, and repainted the whole panel twice. A click arriving during that interval could be ignored. Direct painting over child controls added visible flicker. Repeated open notifications also reset keyboard focus in an already-open panel.

Version **2.2** keeps valid Deposit, Withdraw, Buy and Sell controls enabled while checking balances. A click during that check waits for its reply, then submits once using the quantity that was clicked. The panel checks the action against the new balance and inventory before sending it. A failed refresh, insufficient funds/items/capacity, pending save, logout or character change cancels the waiting action. It never automatically retries a financial transaction after a failed reply.

Unchanged refresh replies no longer invalidate the panel or change control state. Changed balances use buffered painting, and the panel clips its child controls. Repeated open notifications preserve the current input focus.

![Native bank v2.2 preview with sample funds and eligible items](images/bank-preview.png)

*Rendered by the production Windows panel with sample values; this is not a player screenshot.*

## Install

Download **PN-Bank-v2.2-20260913.zip** from the [client release](https://github.com/patnawa/rathena_pn/releases/tag/client-2026-09-13-bank64). Close the game, back up `BankUI.dll`, and copy the replacement DLL into the folder containing `Ragexe.exe`. Restart the game and check for **v2.2** in the bank title bar. This patch requires the existing PN Master Account client and supersedes the v2.1 patch.

Purchases still use the shared bank balance; selling requires eligible items in the current character's inventory. Each disabled exchange shows its reason beneath the item row. See the [bank guide](../client-patch/account_bank/README.md) for prices, eligibility and balance limits.

## Validation

| Check | Result |
| --- | --- |
| Native timer and controls | An unchanged automatic refresh produces zero `WM_ENABLE` messages and no panel invalidation; status and valid buttons remain stable. |
| All six financial actions | A click during refresh submits exactly once with the original clicked amount; extra clicks are blocked. |
| Fresh snapshot validation | Reduced funds, missing items and lost inventory capacity reject waiting actions. Every non-success reply, disconnection and session change cancels them. |
| Shipping panel and socket transport together | Delayed, fragmented loopback replies exercise real authentication hooks, a queued native Buy click, pending save, committed inventory/balance update, and logout before a queued Sell. |
| Existing regressions | All four item exchanges, deposit followed by ticket purchase/sale, invalid input, presets, limits, connection and stale-session guards pass. |
| DLL chain and previews | Original font extension forwarding and hidden bank loading pass; funded, unfunded and maximum-balance native previews were inspected. |

The installed client passed launcher checks and has a hash-verified rollback backup. Automated fixtures use their own Windows processes and loopback data. A live v2.2 session subsequently authenticated and received unchanged refreshes; its remaining disabled actions had valid funds/inventory requirement reasons. The owner confirmed that blinking stopped. A player purchase/sale has not yet been manually verified. See the [verification record](evidence/bank_refresh_20260913.json).

## Local diagnostics

For a remaining disabled action, setting `Diagnostics=1` under `[Bank]` in `BankUI.ini` enables `BankUI-diagnostics.txt` beside the extension. The report contains the latest connection, refresh and control states plus reason codes such as `Funds`, `Items`, `Capacity` or `Unverified`. It omits account/character IDs, login tokens, nonces, balances, inventory counts and raw packets. Nothing is uploaded. Diagnostics are disabled by default; `install.py --diagnostics` enables them for a local investigation.
