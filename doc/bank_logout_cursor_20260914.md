# Bank logout and pointer fix — 14 September 2026

The reported build kept the panel visible after logout and did not restore a
visible system pointer when the cursor display count was negative. Both failures
were reproduced using new native regressions against the baseline panel source.

The current-session notification now hides the panel before clearing balances,
queued actions and request state. The open path rejects unauthenticated sessions.
Old session messages and late replies cannot reopen a logged-out panel. Hidden
authentication refresh remains available for normal server-driven bank opening.

The panel handles WM_SETCURSOR for itself and its controls: a Windows arrow over
the panel/buttons and an I-beam over amount edits. Cursor display-count increments
are tracked and balanced on hide, deactivation, destruction, or departure from
the panel thread's windows. A short timer maintains the pointer while hovering
and releases the adjustment after moving back to the game. No global cursor
replacement, cursor positioning or game cursor-art replacement is introduced.

## Verification

- Baseline control fixture fails the new visible-arrow assertion.
- Baseline production UI/transport fixture fails the hidden-panel assertion after
  the authenticated game socket closes.
- All four rebuilt native Windows suites pass: controls, delayed refresh/logout,
  socket transport, and DLL/font forwarding.
- New controls coverage checks hidden OS cursor recovery, text cursor handling,
  100 repeated cursor messages without count drift, exact count restoration on
  hiding, logout hiding, rejection of login-screen hotkeys, and stale replies.
- The delayed-refresh fixture checks panel hiding after a real hooked socket
  close and continued hiding after the old reply completes.
- The cumulative virtual full installation verifies all 5,620 file hashes and
  sizes; its ZIP integrity check passes.

This is native fixture evidence, not a new rendered Ragexe playthrough. The user
closed the game before installation. Only BankUI.dll, fix notes, release metadata
and the matching installed manifest were changed in the active Data installation.
Settings, font DLLs, player state and server files were preserved.

Installed DLL SHA-256:
`1ebd05d3965d933617c34e6754fcb34b0299ec478a77a384841fb1a249eb01ff`

The package, receipt, tests, baseline reproduction and rollback copy are under
`Client-Packages/bank-ui-fix-20260914` next to the Data directory. The cumulative
ZIP retains the preceding Bank v2.3 and validator update. No commit, push or
release upload was performed.

Windows behavior references: [WM_SETCURSOR parent handling](https://learn.microsoft.com/en-us/windows/win32/menurc/wm-setcursor)
and [thread-local cursor visibility counter](https://devblogs.microsoft.com/oldnewthing/20091217-00/?p=15643).
