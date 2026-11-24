#!/usr/bin/env python3
from pathlib import Path, PurePosixPath
import hashlib, io, sys, zipfile
root = Path(__file__).resolve().parent
for line in (root/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest, rel = line.split('  ', 1)
    p = root / rel
    if hashlib.sha256(p.read_bytes()).hexdigest() != digest:
        sys.exit('SHA256 mismatch: '+rel)
    if p.suffix.lower()=='.zip':
        with zipfile.ZipFile(p) as z:
            if z.testzip() is not None: sys.exit('ZIP CRC mismatch: '+rel)
            for n in z.namelist():
                q=PurePosixPath(n.replace(chr(92),'/'))
                if q.is_absolute() or '..' in q.parts or (q.parts and ':' in q.parts[0]):
                    sys.exit('Unsafe path: '+rel+' / '+n)
print('SHA256 and component ZIP CRC OK')
