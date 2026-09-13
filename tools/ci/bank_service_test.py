"""Execute production bank handlers with explicit world/SQL doubles under sanitizers."""
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='pn-bank-service-') as directory:
    binary=Path(directory)/'bank-service'
    subprocess.run(['g++','-std=c++17','-O1','-fsanitize=address,undefined','-fno-sanitize-recover=all',
                    '-I'+str(ROOT/'src'),str(ROOT/'tools/ci/bank_service_test.cpp'),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
