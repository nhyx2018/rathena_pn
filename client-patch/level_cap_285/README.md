# Fourth-job 285/65 client cap

`build_grf.py` reads the effective `externalsettings_kr.lub`,
`externalsettings_kr_qm.lub`, and `externalsettings_kr_sak.lub` from the active
client `DATA.INI` archives. It changes only `BaseLevel4th` from 275 to 285 and
`JobLevel4th` from 60 to 65, preserving each table's other settings and bytes.
It refuses encrypted or compiled tables, unexpected values, and loose files that
could supersede the GRF entries. The generated overlay contains those three
paths only.

Check the active client without writing an archive:

```text
python client-patch/level_cap_285/build_grf.py --client CLIENT_ROOT --check
```

Generate an overlay for review:

```text
python client-patch/level_cap_285/build_grf.py --client CLIENT_ROOT --output level_cap_285.grf
```

The client already uses all ten `DATA.INI` slots. For a release, merge this
overlay at highest priority into the existing `client_repairs.grf`, then validate
the merged archive and its effective resource precedence before installation:

```text
python client-patch/client_compat/merge_grfs.py level_cap_285.grf client_repairs.grf --output client_repairs_285.grf
```

Replace the existing slot-0 archive only after the matching server 285/65
experience tables and level cap are installed. Keep a backup of that archive.
The source client executable's support above 275 remains to be verified in a
live client session.
