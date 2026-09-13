# Open only the Master Account bank

The old bank could appear before the Master Account panel because the server fell back to its stock open and balance replies when the companion was not attached yet. The updated entry points retain the custom-open request until the authenticated companion connects. They do not send a stock open or balance reply. A stock panel created locally by the game is closed immediately, including while the companion is connecting or reconnecting. A legacy close acknowledgement cannot cancel the waiting custom panel.

Normal banking, `@bank`, NPC `openbank`, and native balance-query requests now use that path. Authentication, character matching, and stale-session checks still apply. The protocol and v2.2 client DLL are compatible with this server change; an additional client patch is not required.

## Grey Buy/Sell controls

Quantity means **number of items**. Buying creates the target item even if the character currently owns zero. It uses bank Zeny only, as requested; character-held Zeny must first be deposited. Selling requires eligible matching items in the character inventory.

For example, **15 tickets cost 15,030,000 Zeny**. A bank holding **3,000,000** can buy at most **two** tickets. Selecting one or two enables Buy if inventory capacity permits, even with zero tickets owned. Selecting 15 correctly shows a 12,030,000-Zeny shortfall. This exact quantity case is now covered by the native Windows control test.

## Verification and deployment

- The opening regression fails against the previous production map binary and passes against the rebuilt binary.
- Production bank service handlers pass AddressSanitizer and UndefinedBehaviorSanitizer checks.
- **15 isolated login/character/map scenarios pass**, including opening and balance checking before companion attachment, a legacy close while waiting, reconnection, native banking, `@bank`, NPC banking, item exchanges, duplicate requests, save recovery, crash recovery, and 64-bit balance persistence.
- The Windows control test confirms that the 3M-bank example rejects 15 tickets and enables one or two without requiring an existing ticket.
- Deployment used a database backup and file rollback copies, with zero characters online. Login, character and map handshakes passed; **31 checked persistent-data tables remained unchanged**. The running map binary matches the tested binary.

The packet tests establish server behavior; visual verification inside the game remains a separate check. See the [verification record](evidence/bank_native_only_20260913.json). The change does not alter prices, wallet limits, inventory eligibility or the transaction commit path.
