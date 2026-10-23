"""MSVC build overlay; package metadata and modules come from setup.cfg."""
import os
from pathlib import Path
from setuptools import Extension, setup

root = Path(os.environ['QF_OPENSSL_ROOT'])
if not (root / 'include/openssl/ssl.h').is_file():
    raise RuntimeError('OpenSSL development files not found')

setup(
    data_files=[('share/quickfix', [str(p) for p in Path('spec').glob('FIX*.xml')])],
    ext_modules=[Extension(
        '_quickfix',
        sources=sorted(str(p) for p in Path('C++').glob('*.cpp')),
        include_dirs=['C++', 'swig', str(root / 'include')],
        library_dirs=[str(root / 'lib')],
        libraries=['libssl', 'libcrypto', 'ws2_32', 'crypt32', 'advapi32', 'user32'],
        define_macros=[('HAVE_SSL', '1'), ('HAVE_CXX17', '1'),
                       ('NOMINMAX', '1'), ('WIN32_LEAN_AND_MEAN', '1'),
                       ('TERMINATE_IN_STD', '1'),
                       ('_CRT_SECURE_NO_WARNINGS', '1')],
        extra_compile_args=['/std:c++17', '/EHsc', '/bigobj', '/Zc:__cplusplus'],
        language='c++',
    )],
)
