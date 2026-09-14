# Client usability update

Install after the enchantment repair client patch. Close the game, back up `SystemEN/itemInfo.lua`, and copy `Start Game.cmd`, `Check Client.cmd`, `tools/` and `SystemEN/` into the matching client directory.

- **Start Game.cmd** checks the client files and starts Ragexe with the game directory as its working directory. It leaves a readable error on screen if a required file is missing.
- **Check Client.cmd** runs the same checks without starting the game.
- **Verify Client.cmd** compares every file in the matching release's `client-manifest.json` against its size and SHA-256. Place that manifest in the game folder. Use this slower check after installing or updating; `Check Client.cmd` remains the quick launch check. Extra screenshots and saves are allowed, while changed supplied settings are reported. Use the updated manifest after applying the bank patch.

September 14 audit update: bank and font components are required even if both
BankUI files are absent. Removing the whole extension can no longer bypass the
quick check. The verifier prefers an in-folder manifest and otherwise searches
the parent folder used by the full-release layout. An explicit `-Manifest` takes
precedence. Pass `-ReportPath verification-report.json` to the verifier to export
size/hash failures for support; the destination directory must already exist.

Maintainer resource audit (Python and a Lua 5.1 executable required):

```text
python tools/client_release_audit.py --client PATH --lua PATH_TO_LUA51 --output audit.json
```

This verifies unencrypted GRF payloads, records archive collisions with payload
equality, executes the actual item loader and registration callback, rejects
missing declared merge tables, and lists missing archive-icon candidates and
per-character AI state for review. It does not establish loose-file precedence,
item obtainability, correct artwork, navigation, or rendered gameplay. Encrypted
or damaged payloads prevent an integrity pass. Merge provenance covers merge
calls, not subsequent direct field edits. JSON resource paths retain legacy
filename bytes as hex to avoid changing Korean names through Unicode folding.
- Item names no longer carry source-server suffixes. Official source labels appear at the bottom of tooltips; the ExampleRO custom-name placeholder is removed. Item IDs, database links, descriptions, art and slots are preserved.

The launcher checks DATA.INI archive presence, repeated priorities, gaps, duplicate archives, classic and Event Horizon GRF headers, this loader's literal Lua imports, and the FontScale configuration. It reads only archive headers, so it does not scan the multi-gigabyte base archive on every launch. It does not download files, alter game settings, require administrator privileges, or contact a server. PowerShell's execution-policy override applies only to the launcher process.

The file check does not validate all compressed contents or prove that gameplay works. The launcher opens the existing Ragexe.exe without modifying it. Existing graphics, sound, controls and font-size preferences remain as configured.

Validation on the supplied client: all nine active archives passed; seven launcher fixtures covered valid input and failure cases. Native Lua 5.1 registered 26,906 items, including 4,947 cleaned names. Item tables, resource names and slots were unchanged; source footers were verified. No rendered game session was performed.

For a different client loader, merge only the presentation settings (`DisplayServer = 3`, `DisplayCustomServer = 0`, `CServerName = 'Custom'`) into its own itemInfo.lua rather than replacing the file. Keep the existing import and override order.

Rollback: restore the previous SystemEN/itemInfo.lua and remove the three added launcher files. The active installation backup and validation evidence are under `server-work/client-usability-20260909` in the owner's game directory.
