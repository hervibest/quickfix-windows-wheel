# QuickFIX 1.16.0 — Windows x64 TLS wheel

Paket workflow GitHub Actions. **Belum dijalankan pada runner Windows.**
Ini belum merupakan wheel yang sudah berhasil dibangun.

## Jalankan

1. Buat repository GitHub kosong, misalnya `quickfix-windows-wheel`.
2. Ekstrak ZIP ini. Masukkan semua isinya ke root repository, termasuk
   folder `.github`. Jangan menaruh seluruh folder proyek satu tingkat
   di bawah root. Pastikan file workflow berada di
   `.github/workflows/build-quickfix.yml`.
3. Commit ke default branch.
4. Buka **Actions → Build QuickFIX 1.16.0 Windows TLS → Run workflow**.
5. Pilih versi Python sesuai server. Default: **CPython 3.9, x64**.
6. Setelah run berhasil, buka bagian **Artifacts** dan download
   `quickfix-1.16.0-cp3.9-windows-x64-tls` (nama menyesuaikan input).
7. Ekstrak artifact ZIP, kemudian install `.whl` di server:

```bat
python -m pip install --no-index C:\packages\quickfix-1.16.0-cp39-cp39-win_amd64.whl
```

Wheel Windows ini hanya untuk Windows x64 dan versi CPython yang cocok.
Jika runtime MSVC yang diperlukan belum tersedia, pasang Microsoft Visual
C++ Redistributable 2015–2022 x64 sesuai kebijakan server.

## Yang dilakukan workflow

- Download source resmi PyPI 1.16.0 dan verifikasi SHA256 yang diharapkan.
- Terapkan overlay build MSVC dengan `HAVE_SSL=1` dan C++17.
- Lengkapi `stdafx.h` yang tidak disertakan sdist.
- Build OpenSSL x64 menggunakan vcpkg bawaan runner Windows 2022.
- Bundle dependency DLL OpenSSL menggunakan delvewheel.
- Install wheel ke virtualenv bersih, buang vcpkg dari PATH, lalu jalankan
  QuickFIX sebagai initiator ke server TLS Python di loopback.
- Server tes meminta dan memverifikasi client certificate, menerima FIX
  Logon, dan membalas Logon. Test mensyaratkan callback `onLogon` QuickFIX.
- Upload wheel hanya bila build dan tes lulus. Jika gagal, lihat log run
  dan artifact diagnosis jika tersedia.

Sertifikat tes dibuat sementara; tidak diperlukan IP, credentials, private
key, maupun sertifikat Bloomberg. Tes lokal ini tidak membuktikan koneksi
Bloomberg, validasi nama host QuickFIX, atau kesiapan produksi.

## Catatan build

Versi Python dapat dipilih: 3.9, 3.10, 3.11, 3.12. Kombinasi ini merupakan
target build; keberhasilannya harus dibuktikan oleh workflow.
Source checksum dipatok. Versi tool Python dipatok; image runner, versi
OpenSSL/vcpkg, dan major tag Actions mengikuti lingkungan GitHub sehingga
build ini belum sepenuhnya reproducible. Jangan menganggap nomor versi
QuickFIX saja cukup untuk mereproduksi binary.

Paket tidak mempublikasikan ke PyPI atau membuat GitHub Release.
Artifact disimpan 14 hari. Unduh sebelum kedaluwarsa.

## Files

- `.github/workflows/build-quickfix.yml`: workflow manual.
- `scripts/prepare_source.py`: download, verifikasi, patch source.
- `scripts/setup_windows.py`: overlay setuptools untuk MSVC/OpenSSL.
- `scripts/test_tls.py`: tes TLS dua arah dan FIX Logon lokal.

Source resmi: https://pypi.org/project/quickfix/1.16.0/
QuickFIX: https://github.com/quickfix/quickfix
DLL packaging: https://github.com/adang1345/delvewheel
