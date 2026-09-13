"""Run the real shared bank arithmetic with ASan and UBSan."""
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='pn-bank-core-') as directory:
    binary = Path(directory)/'bank-core'
    subprocess.run(['g++','-std=c++17','-O1','-fsanitize=address,undefined','-fno-sanitize-recover=all',
                    '-I'+str(ROOT/'src'),str(ROOT/'tools/ci/bank_core_test.cpp'),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
