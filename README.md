# QuickFIX 1.16.0 — Windows x64 TLS Wheel

Prebuilt QuickFIX Python wheel for **Windows x64 with TLS/OpenSSL support**, built and tested using GitHub Actions.

This repository provides an automated build workflow for compiling QuickFIX 1.16.0 on Windows, including OpenSSL dependencies and a local TLS/FIX connectivity test.

**Build Status:** Successfully built and tested on Windows using CPython 3.9 (x64).

## Download

**QuickFIX 1.16.0 — Windows x64 / Python 3.9 / TLS Enabled**

**File:** `quickfix-1.16.0-cp3.9-windows-x64-tls.zip`

**[Download QuickFIX 1.16.0 Windows TLS Wheel](https://github.com/hervibest/quickfix-windows-wheel/actions/runs/39897775037/artifacts/12477568571)**

Package details:

| Property | Value |
|---|---|
| QuickFIX Version | 1.16.0 |
| Platform | Windows x64 |
| Python Version | CPython 3.9 |
| TLS/OpenSSL | Enabled |
| Build Environment | GitHub Actions — Windows Server 2022 |
| Build Result | Successful |
| Local TLS/FIX Test | Passed |
| Artifact Size | Approximately 5.7 MB |
| Artifact Expiration | November 6, 2026 |

**Note:** GitHub may require you to sign in before downloading GitHub Actions artifacts. The download link is subject to GitHub's artifact retention policy.

## Installation

### 1. Download the Wheel

Download the ZIP artifact using the link above.

### 2. Extract the Archive

Extract the downloaded ZIP file to a directory, for example:

```text
C:\packages\
    quickfix-1.16.0-cp39-cp39-win_amd64.whl
```

### 3. Install QuickFIX

Make sure Python 3.9 x64 is installed.

```powershell
python --version
```

Install the wheel:

```powershell
python -m pip install --no-index "C:\packages\quickfix-1.16.0-cp39-cp39-win_amd64.whl"
```

To upgrade an existing QuickFIX installation:

```powershell
python -m pip uninstall quickfix -y

python -m pip install --no-index "C:\packages\quickfix-1.16.0-cp39-cp39-win_amd64.whl"
```

### 4. Verify Installation

```powershell
python -c "import quickfix; print('QuickFIX imported successfully')"
```

The wheel is compatible only with the matching CPython version and Windows x64 architecture.

If required, install the Microsoft Visual C++ Redistributable 2015–2022 (x64).

## Build Your Own Wheel

You can also build QuickFIX for your preferred Python version using GitHub Actions.

### Steps

1. Create or fork a GitHub repository, such as `quickfix-windows-wheel`.
2. Place the project files in the repository root, including the `.github` directory.
3. Ensure the workflow file exists at `.github/workflows/build-quickfix.yml`.
4. Commit and push the files to the default branch.
5. Navigate to **Actions → Build QuickFIX 1.16.0 Windows TLS → Run workflow**.
6. Select the required Python version. The default is CPython 3.9 x64.
7. After the workflow completes successfully, download the generated wheel from the **Artifacts** section.

Supported build targets:

- CPython 3.9
- CPython 3.10
- CPython 3.11
- CPython 3.12

The successful CPython 3.9 build does not automatically guarantee that all other target versions will build successfully.

## What the Workflow Does

The GitHub Actions workflow automatically performs the following operations:

1. Downloads the official QuickFIX 1.16.0 source distribution from PyPI and verifies its expected SHA256 checksum.
2. Applies an MSVC build overlay with `HAVE_SSL=1` and C++17 support.
3. Provides the missing `stdafx.h` header required by the source distribution.
4. Builds OpenSSL x64 using vcpkg on the Windows runner.
5. Bundles the required OpenSSL DLL dependencies using `delvewheel`.
6. Builds a Windows-compatible Python wheel.
7. Installs the generated wheel into a clean Python virtual environment.
8. Removes vcpkg from `PATH` and executes a local TLS connectivity test.
9. Starts QuickFIX as a FIX initiator and connects it to a local Python TLS server.
10. Verifies mutual TLS authentication, FIX Logon exchange, and successful execution of QuickFIX's `onLogon` callback.
11. Uploads the wheel artifact only if the build and test stages succeed.

## TLS and FIX Connectivity Testing

The automated test verifies:

- TLS connectivity between QuickFIX and a local Python server.
- Client certificate authentication.
- Server-side verification of the client certificate.
- FIX Logon message transmission.
- FIX Logon response processing.
- Successful QuickFIX session establishment.

Temporary test certificates are generated locally.

No Bloomberg credentials, private keys, IP addresses, or production certificates are required.

**Important:** Passing the local TLS test does not guarantee compatibility with Bloomberg FIX endpoints, hostname validation behavior, or production readiness.

Real-world integration still requires endpoint-specific connectivity testing, certificate validation, configuration review, and operational testing.

## Project Structure

```text
.github/
└── workflows/
    └── build-quickfix.yml

scripts/
├── prepare_source.py
├── setup_windows.py
└── test_tls.py
```

| File | Description |
|---|---|
| `build-quickfix.yml` | GitHub Actions build and test workflow |
| `prepare_source.py` | Downloads, verifies, and patches the QuickFIX source |
| `setup_windows.py` | Configures MSVC and OpenSSL build settings |
| `test_tls.py` | Performs local mutual TLS and FIX Logon tests |

## Build Reproducibility

The build process pins the QuickFIX source checksum and selected Python build tools.

However, complete binary reproducibility is not guaranteed because the GitHub Actions runner image, OpenSSL/vcpkg dependencies, and major GitHub Actions versions may change over time.

For production deployments, consider recording the final dependency versions and wheel checksums and performing additional security and compatibility testing.

## Limitations

- Windows x64 only.
- Requires the matching CPython version.
- Prebuilt artifact currently provided for Python 3.9.
- Bloomberg FIX connectivity is not covered by the automated local test.
- No automatic publication to PyPI or GitHub Releases.
- GitHub Actions artifacts are retained for 14 days.

## References

- [Official QuickFIX 1.16.0 on PyPI](https://pypi.org/project/quickfix/1.16.0/)
- [QuickFIX GitHub Repository](https://github.com/quickfix/quickfix)
- [delvewheel — Windows Wheel Dependency Bundling](https://github.com/adang1345/delvewheel)
- [GitHub Actions Build](https://github.com/hervibest/quickfix-windows-wheel/actions/runs/39897775037)

## Disclaimer

This is an independently built Windows Python wheel based on the official QuickFIX 1.16.0 source distribution.

It is not an official QuickFIX release.

Use in enterprise or financial systems should be subject to appropriate security reviews, dependency verification, integration testing, and operational approval.