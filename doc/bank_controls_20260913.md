# Account bank Buy/Sell controls — 13 September 2026

The 17Carat Diamond and 1M Zeny quantity fields started at zero. The panel correctly rejected a zero-item transaction, but this left both Buy and Sell greyed out on first use with no quantity label or explanation. Typing a positive quantity or using `+1` was required before an otherwise valid exchange could become available.

Both item fields now start at **1**, including after character changes. The panel labels the quantity and displays the current maximum purchase and sale quantities supplied by the server. The ticket row and inventory tooltip now explicitly say **1M Zeny Ticket** (item 12781); its quantity counts ticket items. The footer explains that purchases use bank zeny and sales use eligible items on hand. Empty, zero and invalid quantities continue to disable transactions.

![Native Master Account panel with sample balances and working Buy/Sell controls](images/bank-preview.png)

*Preview rendered by the shipping Windows panel, using sample balances and inventory. This is not a captured gameplay session.*

## Transaction rules

| Action | Requirements |
| --- | --- |
| Buy | Positive quantity, enough bank zeny, and inventory space and weight capacity |
| Sell | Positive quantity, enough eligible items on hand, and space in the bank balance |
| All financial actions | Authenticated current character, bank available, and no transaction awaiting a reply or save |

The command handler now applies the same unavailable-bank guard as the visible controls. Prices, inventory eligibility, the server transaction protocol and SQL persistence are unchanged. The bank capacity remains 9,223,372,036,854,775,807 zeny; the character wallet remains capped at 2,147,483,647.

## Verification

- `BankUITest.exe` instantiates the production panel and drives actual Windows edit controls and `BM_CLICK` button messages. All four Buy/Sell controls submit the expected action and quantity through a recording transport.
- The same regression fails against the previous source at the initial item-quantity assertion and passes with the fix.
- Pending and duplicate requests, zero/empty/invalid inputs, presets, insufficient funds, missing eligible items, full inventory, bank capacity, unavailable banking, disconnection and stale sessions pass their control checks.
- The shipping DLL loader, original font scaling, loopback transport and normal/maximum-balance previews pass on Windows.
- The existing 500,000-case arithmetic test and production bank-handler fixtures pass with address and undefined-behavior sanitizers.

The UI test replaces the transport with a recorder; it does not commit transactions against player accounts. Actual server/SQL transaction coverage is documented in the [64-bit bank report](account_bank_64bit_20260913.md). These checks do not constitute a manual Ragexe playthrough.

The updated extension was installed in the local client with byte backups and a successful launcher preflight. Evidence and the installation receipt are retained locally under `server-work/bank-buttons-20260913/`. Restart the game client to load the updated DLL. This client control fix requires no server restart or database migration.
