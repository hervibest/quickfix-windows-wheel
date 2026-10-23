"""Download and adapt the official 1.16.0 sdist for MSVC + OpenSSL."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

SHA256 = '825aceb72cfd69c30fbbf5b380b66f464abe1fe3188374f13d8c9987dd8eb4e9'


def patch_openssl_file_io(source):
    path = source / 'C++/UtilitySSL.cpp'
    text = path.read_text(encoding='utf-8')

    def replace(old, new, count=1):
        nonlocal text
        if text.count(old) != count:
            raise RuntimeError('Unexpected QuickFIX source: ' + old)
        text = text.replace(old, new)

    # Keep FILE* and file descriptors inside the extension's C runtime.
    # OpenSSL receives only memory BIOs. This also covers DER fallbacks.
    helper = r'''static BIO *qfFileToMemoryBIO(FILE *fp) {
  BIO *bio = BIO_new(BIO_s_mem());
  if (bio == 0) {
    return 0;
  }
  BIO_set_mem_eof_return(bio, 0);
  char buffer[4096];
  size_t count;
  while ((count = fread(buffer, 1, sizeof(buffer), fp)) != 0) {
    if (BIO_write(bio, buffer, static_cast<int>(count)) != static_cast<int>(count)) {
      BIO_free(bio);
      return 0;
    }
  }
  if (ferror(fp)) {
    BIO_free(bio);
    return 0;
  }
  return bio;
}

'''
    marker = 'X509 *readX509(FILE *fp, X509 **x509, passPhraseHandleCallbackType cb, void *passwordCallbackParam) {'
    replace(marker, helper + marker)
    replace('  rc = PEM_read_X509(fp, x509, cb, passwordCallbackParam);', '''  bioS = qfFileToMemoryBIO(fp);
  if (bioS == 0) {
    return 0;
  }
  rc = PEM_read_bio_X509(bioS, x509, cb, passwordCallbackParam);
  BIO_free(bioS);''')
    replace('  rc = PEM_read_PrivateKey(fp, key, cb, passwordCallbackParam);', '''  bioS = qfFileToMemoryBIO(fp);
  if (bioS == 0) {
    return 0;
  }
  rc = PEM_read_bio_PrivateKey(bioS, key, cb, passwordCallbackParam);
  BIO_free(bioS);''')
    replace('BIO_new(BIO_s_fd())', 'qfFileToMemoryBIO(fp)', count=4)
    replace('    BIO_set_fd(bioS, fileno(fp), BIO_NOCLOSE);', '', count=4)
    replace('    ERR_print_errors_fp(stderr);', '''    ERR_print_errors_cb(
        [](const char *line, size_t length, void *) -> int {
          return fwrite(line, 1, length, stderr) == length ? 1 : 0;
        }, 0);''')
    for forbidden in ['PEM_read_X509(fp', 'PEM_read_PrivateKey(fp',
                      'BIO_set_fd(', 'ERR_print_errors_fp(']:
        if forbidden in text:
            raise RuntimeError('Unpatched OpenSSL CRT I/O: ' + forbidden)
    path.write_text(text, encoding='utf-8')
    print('Patched OpenSSL FILE/descriptor I/O to memory BIOs')


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
#include <ws2tcpip.h>
#include <windows.h>
#include "config.h"
#include "config_windows.h"
''', encoding='utf-8')
    patch_openssl_file_io(source)
    print('Prepared official QuickFIX 1.16.0 source; SHA256 verified')


if __name__ == '__main__':
    main()
