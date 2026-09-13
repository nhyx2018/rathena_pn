# Login outage after a Docker restart, 2026-09-13

The client displayed "server closed" even though all three game containers were
running and their published ports accepted TCP connections. Login authenticated
the account, then rejected it because no character server was registered.

The navigation deployment at 08:05 UTC stopped login and map while leaving
character running. Docker reassigned login from `172.19.0.2` to `172.19.0.6`;
map acquired `172.19.0.2`. Character retained the old login address and retried
that address every ten seconds. Docker DNS correctly resolved `login` to the new
address. The deployment checked map startup and container state, but missed the
broken character-to-login handshake. Login rejection was recorded at 08:34 UTC.

Restarting character refreshed its DNS lookup and restored both interserver
links. An authenticated probe from the Windows client machine then received the
correct public character endpoint and an empty character list. The probe used a
random temporary account, removed afterward; it created and selected no character.

## Reconnect fix

`chlogif_check_connect_logserver` and `check_connect_char_server` now resolve their
configured upstream hostname before every disconnected connection attempt.
Temporary DNS failure skips the connection attempt, so the old address does not
receive an authentication packet. Existing connections remain untouched. Numeric
address configuration and the existing numeric fallback retain their behavior.

The previous IP synchronization packets could only refresh addresses over an
already working connection. They could not recover a link to an upstream that
had moved. Both directions needed the same correction.

The Docker runbook now requires fresh login/character/map handshake messages and
an authenticated character-list check after a restart.

## Evidence

- Production callback regression, with explicit DNS/socket doubles: 40 checks
  passed under AddressSanitizer and UBSan. The previous callbacks failed 12
  assertions in the same scenarios.
- Real private Docker fixture: login moved from `172.22.0.3` to `172.22.0.6`;
  character reconnected without restarting. Character then moved from
  `172.22.0.4` to `172.22.0.7`; map reconnected without restarting. The fixture
  used a fresh schema and no production player data.
- All 38 full release checks passed, using the candidate build objects and a
  private database. The Alpine GCC 15 ASan library requires a missing platform
  size symbol; the disposable compiler wrapper supplies a weak definition from
  `sizeof(sock_fprog)`. Sanitizer instrumentation remains enabled.
- The SQL range regression now supports both PyYAML loaders, retaining all 7,364
  range assertions when the optional C extension is absent. Both loader paths
  passed. The candidate's stale generated SQL and missing validation files were
  replaced with the already committed validation inputs before the full gate.

## Deployment

The exact tested reconnect sources and character/map binaries were installed at
09:06 UTC (16:06 Bangkok). Startup verified all three application handshakes.
An authenticated login and character-list probe passed again at 09:07 UTC. The
temporary login was removed, and no character was created or selected.

Checksums of every audited persistent row remained unchanged: 2 characters,
112 inventory rows, 2 account registry rows, 51 character registry rows, 31
quests, 2,590 item log rows, and the empty bank journal/cart/storage tables.
All six bank source files were unchanged. Deployment replaced only the two
reconnect source files and their character/map executables, with rollback copies
retained outside the live tree. No SQL migration or client-file change was needed.

Local operational evidence and backups are stored outside Git under
`server-work/login-outage-20260913`; remote evidence is under
`/app/rathena-builds/login-outage-20260913`. This includes the original connection
logs, Docker address mappings, native regression results, build output,
private-network tests, release reports, deployment receipt, and login probes.
