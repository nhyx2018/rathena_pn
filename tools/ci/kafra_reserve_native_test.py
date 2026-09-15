"""Native complete Kafra reserve1 source, final confirmation, and plain grants.

Inventory/VM operations execute production code. Registry, transport and world
use inherited explicit doubles. Lottery cases stop immediately after its common
payment, before later animation/input; no lottery delivery or durability claim.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import finalbattle_current_reward_test as current

test = current.test
PATH = 'npc/cities/aldebaran.txt'
NAME = 'Kafra Employee#reserve1'
IDS = (1201, 501, 516)
RUNNER = Path(__file__)
CASES = RUNNER.with_name('kafra_reserve_native_cases.inc')


def validate(root):
    manifest = current.validate(root)
    reader = test.gate.base.Reader(root)
    _, rows = test.gate.base.database_graph(reader)
    items = test.gate.base.scalar_overlay(rows['db/item_db.yml'], 'Id')
    for id in (501, 516):
        item = items[id]
        assert item['Type'] == 'Healing', (id, 'actual ordinary stackable type')
        assert not any(item.get('Flags', {}).get(k, False) for k in ('UniqueId', 'Autoequip')), (id, 'plain output identity')
        assert not item.get('Stack', {}).get('Inventory', False), (id, 'no custom inventory stack limit')
        assert item.get('Weight', 0) > 0, (id, 'positive actual weight')
    manifest['kafra_source_sha256'] = test.sha((root/PATH).read_bytes())
    manifest['kafra_native_runner_sha256'] = test.sha(RUNNER.read_bytes())
    manifest['kafra_native_cases_sha256'] = test.sha(CASES.read_bytes())
    manifest['kafra_items'] = {str(id): items[id] for id in IDS}
    return manifest


def prepare(build, before):
    build.mkdir(parents=True, exist_ok=True)
    for label, root in (('before', before), ('after', test.ROOT)):
        body = test.gate.body((root/PATH).read_text(), NAME)
        (build/f'kafra-{label}.script').write_text(body)
    manifest = validate(test.ROOT)
    inputs = list(current.inputs())
    assert not {row['Id'] for row in inputs[4]}.intersection(IDS)
    inputs[4] += [manifest['kafra_items'][str(id)] for id in IDS]
    inputs[6] = manifest
    (build/'shop_cases.inc').write_text('#define SHOP_ITEM_COUNT 3\n' + CASES.read_text())
    # Keep the shared harness unchanged. Expand only this fixture's explicit
    # registry double allowlist to the actual Kafra persistent point variable.
    driver = (test.ROOT/test.DRIVER).read_text()
    old = 'check(name=="ARG0"||'
    assert driver.count(old) == 1, 'Exact inherited registry boundary expected'
    generated = build/'kafra_finalbattle_driver.cpp'
    generated.write_text(driver.replace(old, 'check(name=="RESRVPTS"||name=="ARG0"||', 1))
    test.DRIVER = str(generated.resolve())
    (build/'kafra-fixture.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return tuple(inputs)


def negative_output(result):
    result.check_returncode()
    text = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout+'\n'+result.stderr)
    assert text.count('KAFRA_RESERVE_NATIVE_OK cases=12 negative=1 expected_grant_failures=4') == 1, text
    for expected in ('buildin_getitem: Failed to add the item to player.', "[Warning]: Script command 'getitem' returned failure."):
        assert text.count(expected) == 4, (expected, text)
        text = text.replace(expected, '')
    assert text.count('Memory manager: No memory leaks found.') == 1
    assert text.count('FINALBATTLE_NATIVE_OK') == 1
    assert not re.search(r'\[(?:error|warning)\]|AddressSanitizer|UndefinedBehaviorSanitizer|runtime error:|TEST FAIL|infinity loop|fatal error|(?:double|invalid) free|Memory manager:(?! No memory leaks found\.)', text, re.I), text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-build-dir', type=Path, required=True)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    inputs = prepare(args.native_build_dir, args.before)
    if args.prepare_only:
        print('KAFRA_NATIVE_FIXTURE_PREPARED exact full body and item contracts validated')
        raise SystemExit(0)
    test.native(args.native_build_dir, inputs, verifier=validate, fixture_only=True)
    result = subprocess.run([str(args.native_build_dir.resolve()/'finalbattle_reward_capacity_test'), str(args.native_build_dir.resolve()), 'candidate'], cwd=test.ROOT, capture_output=True, text=True, env=dict(os.environ, KAFRA_NEGATIVE='1'), timeout=120)
    (args.native_build_dir/'kafra-negative.stdout.txt').write_text(result.stdout)
    (args.native_build_dir/'kafra-negative.stderr.txt').write_text(result.stderr)
    negative_output(result)
    print('KAFRA_NEGATIVE_CONTROLS_OK stale point overwrites, unaffordable redemption and four lost payments reproduced')
