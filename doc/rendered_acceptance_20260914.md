# Rendered gameplay acceptance - 14 September 2026

Full completion of all 30 scenarios below remains **pending**. The subsequent
[six-area audit](audit_all_20260914.md) reached the actual Ragexe QA world and
captured the authenticated Master Account panel with correct balances and
exchange prices. Native desktop enumeration now works, but automated inputs
did not complete a rendered transaction. Treat this as partial visual evidence;
fixtures and server protocol checks remain separate from a Ragexe playthrough.

The later [compact v2.3 panel](bank_compact_20260914.md) passed native control,
transport, refresh and font-scaled rendering checks. Its rendered Ragexe
transactions remain part of this checklist.

Use the verified 13 September full client plus `PN-Client-Update-20260914-Bank-v2.3.zip`.
Run scenarios on a disposable QA realm with two fixture accounts and two
characters on one account. Prepare level, quest, funds and capacity states in
the fixture database. Record client/version hashes, setup, expected/actual result
and screenshots for each run; use fresh fixture state between economic cases.

| # | Setup and player action | Expected result |
|---|---|---|
| 1 | Open the bank through the native button, `@bank` and a bank NPC; close and reopen each. | One usable custom panel opens; balances remain unchanged. |
| 2 | Deposit and withdraw a known amount, close the panel, then relog. | Wallet and bank display the exact persisted amounts with clear success feedback. |
| 3 | Submit zero, negative, excessive and unaffordable amounts. | Clear rejection; no balance or item change. |
| 4 | Buy and sell both supported bank exchange items. | Displayed quantities, fees, item descriptions and final balances agree. |
| 5 | Repeat a purchase or sale click quickly while a response is pending. | Feedback and totals match the number of committed transactions without duplicate delivery. |
| 6 | Reconnect the bank panel, relog, then log into a sibling character. | The same account bank balance appears and stale requests do not change it. |
| 7 | Attempt a bank item purchase with insufficient inventory capacity. | Visible rejection; no debit or lost item. |
| 8 | Attempt withdrawal with a full character wallet and funds in the bank. | Visible rejection; both balances remain unchanged. |
| 9 | Open multi-storage using its player commands and the Mystic Box NPC. | Expand Storages appears first; page names and lock states are readable. |
| 10 | Inspect a locked page purchase, then use Cancel and menu Escape. | Both exits preserve money and the page lock. |
| 11 | Confirm one storage expansion with enough funds. | Exactly 50M character zeny is charged once and one 600-slot page opens. |
| 12 | Deposit and withdraw items on normal and premium pages; reconnect. | Each page preserves its own items, quantities and metadata. |
| 13 | Rename and reorder a populated page, then reopen it. | The title and order update while its inventory stays attached to the same page. |
| 14 | Open shared pages from a sibling character and compare private bound storage. | Account pages are shared; character-bound storage stays private. |
| 15 | Deposit a normal card, a six-digit-ID card, non-card items and carded equipment into card storage. | Only card items are accepted; other deposits have clear rejection feedback. |
| 16 | Move items between cart and storage, then inspect guild storage with permitted and restricted fixtures. | Quantities persist exactly and guild access follows permissions. |
| 17 | Visit the Main Office Progression Guide at 108,80 with a new character, including a Druid fixture. | Advice points to the appropriate job preparation NPC and navigation target. |
| 18 | Visit the guide at level 200 before starting Chapter 1, then follow its direction. | The Small Ash Tree at `prt_fild05,353,252` is reachable and provides the story entry. |
| 19 | Visit the guide during Chapter 1, then resume the active quest. | Advice agrees with the quest book without resetting progress. |
| 20 | Visit the guide in Chapter 2 fixtures for stages 0 through 12 and an unknown stage. | Each normal stage gives the correct next contact; an unknown stage preserves its state. |
| 21 | Compare guide advice before a Chapter 2 encounter, after victory and after reporting. | The next objective changes at the appropriate boundary without awarding progress. |
| 22 | Play the Crossroads encounter from entry through completion with two fixture players. | Party entry, objectives, fight and reporting complete without a stuck dialog or stranded member. |
| 23 | Play the Nyrholt encounter through victory, including a death and re-entry attempt. | Checkpoints, party progress and re-entry match the intended encounter rules. |
| 24 | Complete the Phantom expedition and claim its reward; inspect repeat availability before and after cooldown. | The fight and reward finish once; guide advice matches the four-hour cooldown. |
| 25 | Inspect all seven Biosphere hunts below and above level 240, with available and cooldown states. | Level and availability advice matches each quest NPC and navigates correctly. |
| 26 | Follow Episode 21 directions and inspect Raised Land patrols before and after their prerequisites. | Story directions and patrol availability agree with the original NPCs. |
| 27 | Follow the guide's refine, enchant, crown and material directions. | Each target is reachable, named correctly and offers the described service. |
| 28 | Open inventory, collection artwork and tooltips for the currently held item set, including bank exchange items. | Icons, descriptions, amounts and names render consistently without placeholders. |
| 29 | Open Prontera navigation and its map preview; repeat navigation from the Main Office. | A usable map preview renders; record the exact target and steps if No Image reappears. |
| 30 | With two clients, overlap quest dialogs, change party leader and reconnect at a checkpoint. | Dialogs remain usable, party progress is consistent and the correct checkpoint is retained. |

The updated catalog resource audit lists 1,595 item IDs with unresolved raw
references. None is among the 74 currently held IDs. Classify acquisition paths
and runtime fallbacks before treating those candidates as confirmed defects or
adding replacement artwork.
