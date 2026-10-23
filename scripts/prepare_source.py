"""Download and adapt the official 1.16.0 sdist for MSVC + OpenSSL."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

SHA256 = '825aceb72cfd69c30fbbf5b380b66f464abe1fe3188374f13d8c9987dd8eb4e9'


def main():
    metadata = json.load(urllib.request.urlopen(
        'https://pypi.org/pypi/quickfix/1.16.0/json', timeout=60))
    entry = next(f for f in metadata['urls']
                 if f['filename'] == 'quickfix-1.16.0.tar.gz')
    data = urllib.request.urlopen(entry['url'], timeout=120).read()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise RuntimeError('QuickFIX source checksum mismatch')
    root = Path('build-source')
    root.mkdir(exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        # Explicit validation works on Python 3.9 as well.
        for member in archive.getmembers():
            target = (root / member.name).resolve()
            if root.resolve() not in target.parents:
                raise RuntimeError('Unsafe archive path')
            if not (member.isfile() or member.isdir()):
                raise RuntimeError('Unexpected archive member')
        archive.extractall(root)
    source = root / 'quickfix-1.16.0'
    (source / 'setup.py').write_text(
        Path('scripts/setup_windows.py').read_text(), encoding='utf-8')
    # The sdist references this header for MSVC but does not ship it.
    (source / 'C++/stdafx.h').write_text('''#pragma once
#include <winsock2.h>
#include <windows.h>
#include <ws2tcpip.h>
#include "config.h"
#include "config_windows.h"
''', encoding='utf-8')
    print('Prepared official QuickFIX 1.16.0 source; SHA256 verified')


if __name__ == '__main__':
    main()
