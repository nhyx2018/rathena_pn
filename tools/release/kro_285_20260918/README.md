# September 2026 release controllers

These are the reviewed source scripts for the 285/65 client and server release
and the Kafra lottery correction. Generated ZIPs, GRFs, SQL backups, install
proof, and production receipts live outside this source repository.

The client builders require the release workspace containing
`improvement-pass-20260914`, `kro-285-20260917`, and
`remediation-20260918`. Set `PN_CLIENT_PACKAGES_ROOT` to that
`Client-Packages` directory before running them from this repository. The
builder checks pinned SHA-256 values for the clean manifest, release metadata,
285/65 GRF, and final deterministic ZIP. Rebuilding a different release
requires reviewing and updating those pins.

Example in PowerShell:

```powershell
$env:PN_CLIENT_PACKAGES_ROOT = 'C:\path\to\Client-Packages'
python tools/release/kro_285_20260918/build_client_update.py --check
python -m unittest tools/release/kro_285_20260918/test_build_client_update.py
```

`build_ops_archive.py` packages the staged operations scripts from the same
release workspace. `deploy_server.py` and `deploy_kafra.py` are server-side
controllers with fixed production paths; do not run them in a development
checkout. Their offline tests use mocks and do not call Docker or the firewall:

```text
python -m unittest tools/release/kro_285_20260918/test_deploy_server.py tools/release/kro_285_20260918/test_deploy_kafra.py
```

The production operations controller is staged at
`/app/rathena-builds/kro-285-20260917/deploy_server.py`. Updating the source
copy in this repository does not itself redeploy the running game server.
