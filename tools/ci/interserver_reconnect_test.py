#!/usr/bin/env python3
"""Compile the production reconnect callbacks with explicit DNS/socket doubles."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def run(build, source_root):
    build.mkdir(parents=True, exist_ok=True)
    fixture = (ROOT / 'tools/ci/interserver_reconnect_test.cpp').read_text()
    for name, relative in (
        ('chlogif_check_connect_logserver', 'src/char/char_logif.cpp'),
        ('check_connect_char_server', 'src/map/chrif.cpp'),
    ):
        source = (source_root / relative).read_text()
        matches = re.findall(r'(?:static )?TIMER_FUNC\(' + name + r'\)\s*\{.*?^\}',
                             source, re.MULTILINE | re.DOTALL)
        if len(matches) != 1:
            raise RuntimeError('Expected one production callback: ' + name)
        fixture = fixture.replace('// @production:' + name, matches[0])
    generated = build.resolve() / 'interserver-reconnect.cpp'
    binary = build.resolve() / 'interserver-reconnect-test'
    generated.write_text(fixture)
    subprocess.run(['g++', '-std=c++17', '-g', '-O1', '-Wall', '-Wextra',
                    '-Wno-unused-parameter', '-fsanitize=address,undefined',
                    '-fno-sanitize-recover=all', str(generated), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True, timeout=30)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path)
    parser.add_argument('--source-root', type=Path, default=ROOT,
                        help='Optional earlier source tree for reproducing the failure')
    args = parser.parse_args()
    if args.build_dir:
        run(args.build_dir, args.source_root)
    else:
        with tempfile.TemporaryDirectory(prefix='interserver-reconnect-') as directory:
            run(Path(directory), args.source_root)
