#!/usr/bin/env python3
"""Build the actual navigation pathfinder regression with ASan and UBSan."""
import argparse
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]


def run(build):
    build.mkdir(parents=True,exist_ok=True)
    binary=build.resolve()/'navigation-path-test'
    includes=['src','3rdparty/libconfig','3rdparty/rapidyaml/src',
              '3rdparty/rapidyaml/ext/c4core/src','3rdparty/json/include','/usr/include/mysql']
    subprocess.run(['g++','-std=c++17','-g','-O1','-fno-rtti','-DMAP_GENERATOR','-DPACKETVER=20260219',
                    '-ffunction-sections','-fdata-sections','-fsanitize=address,undefined',
                    '-fno-sanitize-recover=all',*['-I'+p for p in includes],
                    'tools/ci/navigation_path_test.cpp','-Wl,--gc-sections','-o',str(binary)],cwd=ROOT,check=True)
    subprocess.run([str(binary)],cwd=ROOT,check=True,timeout=30)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir',type=Path)
    args=parser.parse_args()
    if args.build_dir:run(args.build_dir)
    else:
        with tempfile.TemporaryDirectory(prefix='navigation-path-') as directory:run(Path(directory))
