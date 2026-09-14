# Client release audit and implementation — 14 September 2026

Implemented and installed stricter client checks in the local Data installation,
with rollback copies. Built a separate verified client candidate and a cumulative
ZIP preserving the latest previously validated Bank v2.3 update. The original
September 13 full release, live Docker services, settings, DLLs in Data, and player
saves were not replaced.

## Delivery

- Update ZIP: [PN-Client-Update-20260914-Validator.zip](C:/Users/Alpha/Downloads/Compressed/Data2026/Client-Packages/audit-20260914/PN-Client-Update-20260914-Validator.zip)
- SHA-256: `7abc952ed2580eaad340fb5fe2848d27d7e093c415308d31f094fbd0b88058f7`
- Clean complete candidate: `candidate/PN-Client` under this audit directory.
- Installed tooling rollback: `installed-tooling-backup` (original manifest and scripts).
- Original distribution RARs remain unchanged. No commit, push, release upload or server deployment.

For a fresh installation, use the candidate directory. For an existing installation,
close the game, back up the client and copy the ZIP's PN-Client contents into it.
The delta ZIP preserves player state; it does not remove old AI state. Run Check
Client followed by Verify Client. Diagnostics are optional via `-ReportPath`.

## Confirmed defect and repair

The original launcher returned success when both BankUI.ini and BankUI.dll were
removed. The new regression reproduces that false pass against the original
release launcher. PN bank/font dependencies are now unconditional requirements.
All 15 launcher fixtures pass, including individual and combined removal cases.

The verifier now prefers an installed manifest, falls back to the parent-folder
full-release manifest, and writes optional JSON diagnostics on success or failure.
An explicit manifest still takes precedence. It does not replace player files or
accept mismatched hashes merely to produce a passing report.

## Fresh validation

| Check | Result |
|---|---|
| Clean candidate manifest | 5619 file sizes and SHA-256 hashes passed |
| Active archives | 10 archives; 242,185 payloads verified; zero encrypted skips or payload errors |
| Actual Lua 5.1 loader | 26,916 items registered |
| Item merge decisions | 259 additions; 18 replacements; 0 ignored definitions |
| Bank metadata | Both descriptions, real registration and four ticket art payloads passed |
| DLL chain | Candidate bank v2.3 loads hidden; original font scaling and disabled unauthenticated controls passed |
| Python/PowerShell regression coverage | 15 launcher fixtures; 6 manifest tests; 9 resource/Lua tests; 6 release-gate tests passed |
| Bank core | 500,000 randomized plans and integer boundaries passed with ASan/UBSan |
| Bank service | Production handlers with test doubles passed with ASan/UBSan |

The new source command `tools/client_release_audit.py` emits a repeatable JSON
report for archive payload integrity, override collisions, merge decisions,
runtime registration, missing-icon candidates, and AI hygiene. Its parser tests
are included in the source release gate. It preserves legacy resource-name bytes
and distinguishes identical and changed overrides. Actual GRF writers can omit
alignment padding before the index; payload bounds are checked without falsely
rejecting that valid layout.

## Findings requiring review

- **1,113 cross-archive collisions:** 1,022 have different payloads,
  91 identical payloads; no within-archive duplicate names. Most are new.grf overriding data.grf.
  These are override inventory, not confirmed defects. No archives were merged or removed.
- **2,569 icon-reference candidates across 2,035 item IDs.**
  1,592 overlap the previous limited acquisition triage;
  443 were not in that prior list. That older graph does not prove
  these items unobtainable. Loose files, client fallback behavior and dynamic acquisition
  routes require further review. No placeholder artwork was invented.
- **Eight old AI state files** excluded from the newly built clean candidate only.
  The installed player's AI state is preserved. Nested AI DLLs remain pending dependency review.
- **Everyday Data installation:** three mismatches remain: A_Friends.lua, BankUI.ini,
  and FontScale.dll. Friend state and enabled diagnostics are local changes. The font
  hash matches the prior bank-refresh and bank-v2.3 installation receipts, so this
  is a known preserved variant, not evidence of corruption. Three missing notices
  were restored. Full verification correctly continues to report these differences.
- **Server disk:** 88% used, 12G available at inspection. Review old build/backup
  retention before another large build; no server files were deleted.

## Bank audit coverage and limits

| Scenario | This session | Earlier evidence |
|---|---|---|
| Exact 64-bit values and overflow rejection | Fresh arithmetic suite passed | Real-process boundary tests recorded previously |
| Duplicate/stale replies, authentication and retries | Fresh service fixture passed | Fifteen real-process bank scenarios recorded previously |
| Commit failure and rollback | Fresh handler/test-double coverage passed | SQL failure and actual map-process crash tests recorded previously |
| Shared account persistence and reconnect | Not newly exercised against live processes | Prior isolated realm evidence exists |
| Real rendered deposit/buy/sell sequence | Not performed | Earlier rendered acceptance remains partial |

SSH inspection confirmed the map/character/login/database containers were running,
with zero recorded restarts or OOM kills. All six deployed bank source files and
storage.cpp match the locally tested checkout. This does not independently prove
the build provenance of the running map binary. No live transaction or failure
injection was performed and no production service was restarted.

## Evidence and follow-up

See `evidence/candidate-resource-audit.json`, `candidate-verification.json`,
`bank-item-metadata.json`, `tests.json`, `server-inspection.json`, `build.json`,
`installed-tooling.json`, and `installed-verification.json`.

The next useful work is an isolated rendered bank acceptance run, then provenance
and acquisition checks for the 443 newly listed item IDs. Keep crash/SQL failure
injection in disposable realms. Navigation remains covered only by the earlier
audit; this pass adds no new navigation or full gameplay proof.

Automatic approval review rejected removal of the temporary `candidate-attempt-01`
folder with “blocked by policy.” It remains as unused scratch data, separate from
the delivered candidate and ZIP.
