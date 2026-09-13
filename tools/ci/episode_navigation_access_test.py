#!/usr/bin/env python3
"""Native VM regressions for the captured Rgan and eastern tent entrances.

Production NPC bodies, quest changes, suspension and branching run unchanged.
Transport and character persistence use the encounter harness's explicit doubles.
No connection to a running server or database is possible in the test process.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

import episode21_encounter_flow_test as native
from episode_party_progression_test import npc_body

TARGETS = (
    ('npc/custom/episode20/SidesAndDailies.txt', 'Iwin Soldier#ep20_home'),
    ('npc/custom/episode21/Progression.txt', 'Tan#ep21_east_tent'),
)


def fixtures(build, pre_fix=False):
    entries = []
    digest = hashlib.sha256()
    for i, (relative, name) in enumerate(TARGETS):
        body = '{\n' + npc_body(native.ROOT / relative, name) + '\n}'
        if pre_fix:
            if i == 0:
                body = body.replace('close2; warp "icas_in2",33,114; end;', 'close;')
                for quest in range(17713, 17717):
                    body = body.replace(f' && isbegin_quest({quest}) == 0', '')
            else:
                body = body.replace('EP21_ResistanceStep < 4 || EP21_ResistanceStep > 6', 'EP21_ResistanceStep != 4')
                body = body.replace('if (EP21_ResistanceStep == 4) EP21_ResistanceStep = 5;', 'EP21_ResistanceStep = 5;')
        filename = f'entrance_{i}.script'
        (build / filename).write_text(body)
        digest.update(body.encode())
        entries.append('{' + json.dumps(name) + ',' + json.dumps(filename) + ',"",0,false},')
    header = 'static Case source_cases[] = {' + ''.join(entries) + '};\n'
    header += 'static int quest_ids[] = {17712,17713,17714,17715,17716,23243};\n'
    (build / 'episode_cases.inc').write_text(header)
    digest.update(header.encode())
    return digest.hexdigest()


CASES = r'''
    const std::string tent = "Tan#ep21_east_tent", home = "Iwin Soldier#ep20_home";
    for (int status : {0,1,2}) for (int step = 0; step <= 12; ++step) {
        reset();
        if (status) seed_quest(0,23243,status == 2);
        registries[players[0]->id]["EP21_ResistanceStep"] = step;
        finish(tent);
        bool admitted = status == 1 && step >= 4 && step <= 6;
        check(moves.size() == (admitted ? 1u : 0u), "tent admits only the active document/Valdaris steps");
        check(registries[players[0]->id]["EP21_ResistanceStep"] == (admitted && step == 4 ? 5 : step),
              "reentry preserves the document checkpoint and rejects all unrelated steps");
        if (admitted && !moves.empty()) check(moves[0].map == "mbase_in" && moves[0].x == 289 && moves[0].y == 124,
                                              "admitted entrant uses the real eastern tent landing");
        check(items.empty() && reputation.empty() && experience.empty(), "tent transport cannot issue rewards");
    }
    for (int step : {0,4,5,6,11}) for (int quest : {0,17712,17713,17714,17715,17716}) {
        reset(); if (quest) seed_quest(0,quest);
        registries[players[0]->id]["EP20_Step"] = step;
        finish(home);
        check(moves.size() == (step >= 5 ? 1u : 0u), "captured Rgan entry retains the Episode 20 gate");
        if (step >= 5 && !moves.empty()) check(moves[0].map == "icas_in2" && moves[0].x == 33 && moves[0].y == 114,
                                             "soldier actually transports the entrant to Nadyagand");
        if (quest) check(q(0,quest) == Q_ACTIVE, "room entry preserves the active side-story quest");
        if (quest > 17712) check(q(0,17712) == -1, "returning during later stages never restarts the first quest");
        if (!quest) check(q(0,17712) == (step >= 5 ? Q_ACTIVE : -1), "eligible first visit starts exactly one quest");
        check(items.empty() && reputation.empty() && experience.empty(), "room entry cannot issue rewards");
    }
    reset(); registries[players[0]->id]["EP20_Step"] = 11;
    registries[players[0]->id]["EP20_Side_Home"] = 1;
    finish(home); finish(home);
    check(moves.size() == 2 && q(0,17712) == -1, "completed story retains repeatable daily access without restarting it");
'''


def run(build, pre_fix):
    prefix, main = native.CPP.split('extern "C" int __wrap_main', 1)
    start = main.index('    // Every shared dialogue transition:')
    end = main.index('    for (auto& entry : codes)')
    native.CPP = prefix + 'extern "C" int __wrap_main' + main[:start] + CASES + main[end:]
    native.CPP = native.CPP.replace('EP21_NATIVE_RESULT', 'EPISODE_NAVIGATION_ACCESS_RESULT')
    native.fixtures = fixtures
    native.run(build.resolve(), False, pre_fix, completion_marker='EPISODE_NAVIGATION_ACCESS_RESULT ')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path)
    parser.add_argument('--pre-fix', action='store_true', help='Reconstruct the two entrance regressions; expected failure')
    args = parser.parse_args()
    if args.build_dir:
        args.build_dir.mkdir(parents=True, exist_ok=True)
        run(args.build_dir, args.pre_fix)
    else:
        with tempfile.TemporaryDirectory(prefix='episode-navigation-') as directory:
            run(Path(directory), args.pre_fix)
