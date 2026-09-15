# Reward delivery validation

Run these focused regressions from the repository root on Linux. They execute
production inventory and script VM code with explicit world, transport and
persistence doubles. They do not establish real-client acceptance or SQL/crash
durability. Kafra lottery coverage stops after the common payment, before its
later animation and prize delivery.

Use a separate checkout with Python 3/PyYAML, GCC/G++ with ASan/UBSan, make,
MySQL client development libraries, zlib, PCRE and OpenSSL installed. Build fresh
support objects from that same checkout; do not reuse objects from another
candidate. The [release guide](../tools/ci/release_checks_README.md) and
[CI workflow](../.github/workflows/pn_release_checks.yml) list the dependencies.

```bash
set -euo pipefail
CPPFLAGS=-DCONVERT_ALL ./configure --enable-prere=no --enable-packetver=20260219 --enable-buildbot=no
make import
make -j2 map
export REWARD_VALIDATION_DIR="$(mktemp -d "${TMPDIR:-/tmp}/reward-validation.XXXXXXXX")"
mkdir -p "$REWARD_VALIDATION_DIR/before"
```

The Fall of Glast Heim, Lake of Fire, original Phantom Crystal, merchant and
Kafra negative controls use these exact files from the pre-fix commit. A shallow
clone must first obtain this commit's history.

```bash
REWARD_BASELINE=df18f1b4eac7e27953c10ea3ff95c716f7e22dc6
test "$(git rev-parse "$REWARD_BASELINE^{commit}")" = "$REWARD_BASELINE"
git archive "$REWARD_BASELINE" \
  npc/custom/instances/FallOfGlastHeim.txt \
  npc/custom/instances/LakeOfFire.txt \
  npc/custom/chapter2/Chapter2.txt \
  db/import/chapter2_item_db.yml \
  npc/battleground/bg_common.txt \
  npc/merchants/alchemist.txt \
  npc/cities/aldebaran.txt \
  | tar -x -C "$REWARD_VALIDATION_DIR/before"

python3 -B tools/ci/dynamic_reward_audit_test.py
python3 -B tools/ci/reward_resume_test.py \
  --native-build-dir "$REWARD_VALIDATION_DIR/reward-native" \
  --before "$REWARD_VALIDATION_DIR/before" \
  --cases tools/ci/reward_resume_cases.inc
python3 -B tools/ci/merchant_reward_test.py \
  --native-build-dir "$REWARD_VALIDATION_DIR/merchant-native" \
  --before "$REWARD_VALIDATION_DIR/before"
python3 -B tools/ci/kafra_reserve_native_test.py \
  --native-build-dir "$REWARD_VALIDATION_DIR/kafra-native" \
  --before "$REWARD_VALIDATION_DIR/before"
```

The Crystal item-entry regression isolates a later issue: a direct item-script
dialogue loses its continuation while the queued NPC event can resume. Its
baseline must retain the final reward/helper bodies and `Delayconsume` type.
Construct that intermediate fixture from the current files, changing only the
asserted item-entry script. This edits the temporary fixture, not the checkout.

```bash
python3 - <<'PY'
import os
from pathlib import Path
import shutil
import yaml

fixture = Path(os.environ['REWARD_VALIDATION_DIR']) / 'crystal-before'
npc = Path('npc/custom/chapter2/Chapter2.txt')
db = Path('db/import/chapter2_item_db.yml')
for relative in (npc, db):
    (fixture / relative).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(relative, fixture / relative)
original = (fixture / db).read_bytes()
rows = yaml.safe_load(original)['Body']
item = next(row for row in rows if row['Id'] == 106441)
assert item['Type'] == 'Delayconsume'
assert item['Script'].strip() == 'doevent "CH2_PhantomCrystal::OnOpen";'
old = b'doevent "CH2_PhantomCrystal::OnOpen";'
new = b'callfunc "CH2_OpenPhantomCrystal";'
assert original.count(old) == 1
replacement = original.replace(old, new, 1)
assert replacement.replace(new, old, 1) == original
(fixture / db).write_bytes(replacement)
assert (fixture / npc).read_bytes() == npc.read_bytes()
PY
python3 -B tools/ci/crystal_item_entry_native_test.py \
  --native-build-dir "$REWARD_VALIDATION_DIR/crystal-native" \
  --before "$REWARD_VALIDATION_DIR/crystal-before"
```

All commands must exit successfully. The native runners retain receipts,
source fingerprints and stdout/stderr in their build directories. Deliberately
failing historical grants run under separate negative-control expectations;
the corrected candidate still rejects unexpected warnings and errors. Keep the
temporary directory as validation evidence.

These focused commands do not run the full release gate. Before deployment,
follow the [release guide](../tools/ci/release_checks_README.md) in an isolated
candidate with disposable SQL databases and isolated ports/network. Run the full
gate separately against the frozen final candidate and retain its passing
report and startup log with the focused receipts.
