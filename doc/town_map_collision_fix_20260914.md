# Town map collision fix — 14 September 2026

Deployed the server map cache matching the installed `new.grf` geometry for Einbroch, Lighthalzen and Yuno. The client assets were preserved. This removes client/server disagreement over which cells permit movement.

| Map | Corrected walkability cells | Checked navigation points |
| --- | ---: | ---: |
| Einbroch | 885 | 159 |
| Lighthalzen | 13,956 | 243 |
| Yuno | 53 | 153 |

The repair follows DATA.INI precedence, extracts GAT cell types and RSW water heights, and applies the native conversion rules. All other base-cache map records are byte-identical. Import and Renewal caches are unchanged.

Verification: no lost approach/arrival points or previously connected point pairs among 555 registered navigation points; no lost local access around 393 static NPC/warp registrations. Four-way connectivity is a geometric check; it does not simulate dynamic quest gating or rendered gameplay. Existing navigation distance tables were not regenerated; route-length estimates may differ, while the checked connections remain available.

The native cache reader passed 1,416 cases, 1,321 map records and 5,524 assertions with zero failures/errors, ASan/UBSan errors or allocator leaks. Native pathfinding regression passed long paths, bounds, blocked NPC approaches, rectangular touch areas and disconnected rooms. The harness now supports both glibc and musl cookie offsets and links optional libraries only when installed.

Deployment checked zero online players, retained a rollback cache, and verified live cache hashes and successful map-server authentication/startup. The initial restart attempt rolled back because login was stopped during map-to-character authentication; the successful retry started login before map. No application binaries or SQL data were edited by the deployment script.

Installed cache SHA-256: `624f84eabfc3fef0e818a9491b9bb4b7e3f5a33756eecbcf369ca8d27f547dfd`.
Previous SHA-256: `42d5028ee2f1d263002427fe0f7b38053d06592ef803831e298569387336faf0`.

Remote rollback: `/app/rathena-builds/map-collision-fix-20260914/map_cache.before.dat`. Restore it to `/app/rathena/db/map_cache.dat` with map-server stopped, then start services in dependency order.

Local build, connectivity evidence, native logs, startup log and deployment receipt: `Client-Packages/map-collision-fix-20260914/`.
