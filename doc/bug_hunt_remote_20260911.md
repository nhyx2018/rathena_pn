# Remote runtime acceptance — 11 September 2026

**Current status:** BH-005 has subsequently been fixed and deployed. See
[the deployment and acceptance status](bug_hunt_completion_20260911.md).
This report preserves the original installed-binary reproduction.

Follow-up: the local persistence candidate now passes the acknowledged-result
crash regression and an injected SQL failure/retry check. See
[the durability follow-up](bug_hunt_durability_20260911.md). The installed-binary
findings below are preserved; no production deployment is implied.

Used the supplied SSH connection to inspect the host and create an isolated test
environment from the installed server binaries. The public login, character,
map, web, and database services were not modified or restarted.

## Environment and identity

- Candidate: `/app/rathena-builds/bughunt-20260911-runtime/candidate`.
- Dedicated Docker network: `bughunt-20260911-internal`, with `Internal: true`.
- Test services: `bughunt-test-db`, `bughunt-test-login`, `bughunt-test-char`, and
  `bughunt-test-map`; none publishes a host port.
- Fresh database with synthetic accounts 99000011/99000013 and characters
  99000012/99000014. No production player records were copied.
- The two test characters are a level-275 Dragon Knight and Arch Mage. The combat
  fixture grants the Arch Mage its class skills to supply normal prerequisites.
- Source checkout base: `e985006171d2eb320ee512a653f4c83aea3d81b6`, with installed
  modifications. The local workspace has a different base; `identity.json`
  records actual source hashes rather than assuming the trees are identical.
- The copied map and character executable hashes matched `/proc/<pid>/exe` in
  the running public containers. Map: `9f04be11d39e7fbecd11ef29347c8b63b9b1d64f160482d4aacf1abe25ee768c`;
  character: `fc070d9f323a326b6630ea2ac545e45de14d62571328a3ade94b602992bc4250`.

## Completed checks

| Area | Result | Evidence |
|---|---|---|
| Two-player party lifecycle | Both accounts joined one party; leadership transferred; both entered the same live Old Glast Heim instance; the leader disconnected, reconnected, and re-entered. | `party-combat.json` |
| Physical combat | Five normal client attack requests each dealt 384 damage to a controlled dummy. | `party-combat.json` |
| Magic combat | Five client Fire Bolt requests each dealt 314 damage against Neutral and 283 against Water. The observed change matches the effective 90% element ratio within one damage point. | `party-combat.json`, `verify_combat.py` |
| Reform disconnect before confirmation | Original equipment, tuning, and materials retained after reconnect. | `reform-opened.json` |
| Reform disconnect after acknowledgement | Exactly one completed result; exact materials consumed; refine/cards/unique identity preserved. | `reform-confirmed.json` |
| Reform immediate disconnect after confirmation request | Whole result or whole inputs required; no partial charging or duplicate equipment accepted. | `reform-racing.json` |

Physical and magic checks sent the normal 20260219 action/skill packets through
the real map handlers and combat engine. The NPC fixture only prepares/reports
the dummy and character state for these tests. These are controlled runtime
checks, not an absolute damage balance benchmark or a rendered boss encounter.

Party tests use actual script builtins and live map/character services. Direct
instance entry does not validate the production NPC's quest, cooldown, roster,
or once-only reward gates. The earlier native script fixtures cover selected
gates; rendered dialogue races and complete quest chains remain unverified.

## Recovery and remaining acceptance

**BH-005 reproduced on the installed binaries.** After a successful reform
acknowledgement, abrupt termination of the test map process restored the source
axe, tuning, and all five material quantities on reconnect. Refine, cards, and
unique identity were preserved. SQL readback independently confirmed the restored
inputs. `reform-crash.json` records `atomicity_passed: true` and
`acknowledged_result_durable: false`. Nothing was partially consumed or duplicated,
but the acknowledged upgrade was lost. This persistence limitation remains open;
no production save-path change was made.

The test killed only `bughunt-test-map`, restarted the isolated game services,
and reconnected the protocol client. Production services were not part of the
restart. This establishes process-crash behavior for one recipe, not database
outage or host power-loss behavior.

Initial harness failures were corrected before the completed checks: party
creation requires waiting for asynchronous membership assignment; a synthetic
mage needs normal skill prerequisites. These setup failures are retained in the
logs and are not classified as gameplay defects.

Rendered client acceptance remains unavailable because the native desktop
connection failed in this session. Full boss encounters, overlapping production
NPC dialogues, broader recipe crash coverage, database outage, and host power
loss are still outside the verified scope.

All four test services were stopped after the checks. The isolated network,
candidate, synthetic database, and logs were retained for reproduction, with no
host ports published. `cleanup.json` confirms the stopped state;
`live-service-status.json` records the running public services and original start
times.

Local receipts are under `server-work/bughunt-20260911/remote/results/`, and
harnesses/archive under `server-work/bughunt-20260911/remote/`, beside the repository. Remote receipts are
under `/app/rathena-builds/bughunt-20260911-runtime/`. The supplied SSH password
was not written to these files.
