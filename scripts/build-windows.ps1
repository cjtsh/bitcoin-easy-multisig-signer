#Requires -Version 5.1
<#
.SYNOPSIS
    Run ON Windows. Build the self-contained Bitcoin Easy Signer bundle and a zip
    that can be unpacked and run.

.DESCRIPTION
    This mirrors scripts/build-macos.sh's gate order deliberately: the same
    fail-closed checks in the same sequence, so an operator who knows one script
    can read the other. The differences are the platform, the packaging step, and
    the absence of signing.

    There is no RELEASE switch here, unlike the macOS script. macOS needs it
    because notarization only applies to a public build. Windows has no equivalent
    one-time round trip, so every build this script makes is the same artifact;
    whether it is published is the workflow's decision, not the script's.

    This does not publish anything.

.PARAMETER Version
    The version to build, e.g. 0.6.4. Must equal APP_VERSION in version.py.
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string] $Version
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# The reviewed SHA-256 of vendor/libusb-1.0.dll.
#
# Same discipline as build-macos.sh, which hardcodes the 8f6ad6c1... digest of the
# reviewed dylib and refuses to bundle anything else. This digest was taken from
# the reviewed artifact produced by .github/workflows/windows-inputs.yml run
# 37035301559 on 2026-10-02, compiled from the pinned libusb-1.0.30.tar.bz2, and
# is recorded in three other places: vendor/README.md, REVIEWED in
# tests/test_libusb_vendor.py, and the LIBUSB_WINDOWS_SHA256 repository variable.
#
# To change it, rebuild with that workflow, verify the bytes against the pinned
# source, commit the file, then update all four places in one commit.
$reviewedLibusbSha256 = 'f7ca6ca40f70e06140e1fab01deedb262464b45bface9eff62c1864e74ff1311'

function Fail {
    param([Parameter(Position = 0)][string] $Message)
    [Console]::Error.WriteLine($Message)
    exit 1
}

# Every path in this script is relative to the repository root, so start there
# rather than wherever the caller happened to be.
Set-Location -LiteralPath (Join-Path $PSScriptRoot '..')

if ($env:OS -ne 'Windows_NT') {
    Fail 'The Windows bundle must be built and tested on Windows.'
}
$architecture = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
if ($architecture -ne 'AMD64') {
    Fail "The released Windows bundle is x64 only; this machine reports $architecture."
}

if ([string]::IsNullOrWhiteSpace($Version)) {
    Fail 'Usage: scripts\build-windows.ps1 VERSION (e.g. 0.6.4)'
}
if ($Version -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$') {
    Fail 'Expected a numeric version such as 0.6.4.'
}

# hwi 3.2.0 declares Requires-Python >=3.9,<3.13 and is bundled into the app, so a
# newer interpreter cannot install it. Fail here with an actionable message
# instead of deep inside pip. PYTHON names the interpreter, because the right one
# is not always the first python on PATH.
$pythonExe = if ([string]::IsNullOrWhiteSpace($env:PYTHON)) { 'python' } else { $env:PYTHON }
$pythonCommand = Get-Command $pythonExe -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    Fail @"
PYTHON=$pythonExe was not found on PATH.
Name a Python 3.10-3.12 interpreter, for example:
  `$env:PYTHON = 'C:\Python312\python.exe'; scripts\build-windows.ps1 $Version
"@
}
$pythonPath = $pythonCommand.Source
$pythonMinor = (& $pythonPath -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")').Trim()
if ($pythonMinor -notin @('3.10', '3.11', '3.12')) {
    Fail @"
This build needs Python 3.10-3.12; $pythonExe is Python $pythonMinor.
The bundled HWI requires <3.13 and embit requires >=3.10.
Name a supported interpreter explicitly:
  `$env:PYTHON = 'C:\Python312\python.exe'; scripts\build-windows.ps1 $Version
The GitHub Actions workflow pins 3.12 already.
"@
}

$appVersion = (& $pythonPath -c 'from version import APP_VERSION; print(APP_VERSION)').Trim()
if ($Version -ne $appVersion) {
    Fail "Bundle version $Version does not match app version $appVersion."
}

$lockFile = 'requirements-desktop-windows.lock'
if (-not (Test-Path -LiteralPath $lockFile -PathType Leaf)) {
    Fail @"
$lockFile is missing.
It is generated on Windows from requirements-desktop.txt, reviewed, and committed;
requirements-desktop.lock is macOS-resolved (it pins pyobjc and macholib) and must
not be reused here. See WINDOWS-PORT.md for the bootstrap sequence.
"@
}

$venvPython = '.build-venv\Scripts\python.exe'
$lockDigestFile = '.build-venv\requirements-desktop-windows.sha256'

# Local builds always recreate the environment. CI prepares it before any secret
# is present, then explicitly reuses that same environment in the build step.
if ($env:BUILD_DEPS_PREPARED -eq '1') {
    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        Fail 'Prepared build environment is missing.'
    }
    $expectedLockDigest = (Get-FileHash -LiteralPath $lockFile -Algorithm SHA256).Hash.ToLowerInvariant()
    if (-not (Test-Path -LiteralPath $lockDigestFile -PathType Leaf) -or
        (Get-Content -LiteralPath $lockDigestFile -Raw).Trim() -ne $expectedLockDigest) {
        Fail 'Prepared build environment does not match the desktop lock.'
    }
} else {
    if (Test-Path -LiteralPath '.build-venv') {
        Remove-Item -LiteralPath '.build-venv' -Recurse -Force
    }
    & $pythonPath -m venv .build-venv
    if ($LASTEXITCODE -ne 0) { Fail 'Could not create .build-venv.' }
    & $venvPython -m pip install --disable-pip-version-check --require-hashes -r $lockFile
    if ($LASTEXITCODE -ne 0) { Fail "Could not install $lockFile." }
    (Get-FileHash -LiteralPath $lockFile -Algorithm SHA256).Hash.ToLowerInvariant() |
        Set-Content -LiteralPath $lockDigestFile -NoNewline
}

if ($env:PREPARE_ONLY -eq '1') {
    Write-Host 'Hash-locked build environment prepared.'
    exit 0
}

if (-not (Test-Path -LiteralPath 'assets\AppIcon.ico' -PathType Leaf)) {
    Fail 'assets\AppIcon.ico is missing. Regenerate it with scripts\make-windows-icon.py.'
}

# Windows, unlike macOS, has no signing step, so the native library is never
# covered by a code signature here. Verify it anyway: the digest is what ties the
# shipped DLL to the reviewed build, and without it a swapped binary would ship as
# "the Windows build" with nothing to compare against.
$libusbDll = 'vendor\libusb-1.0.dll'
if (-not (Test-Path -LiteralPath $libusbDll -PathType Leaf)) {
    Fail "Bundling HWI requires the vendored libusb input at $libusbDll."
}
if ($reviewedLibusbSha256 -notmatch '^[0-9a-f]{64}$') {
    Fail @"
The reviewed Windows libusb digest has not been pinned yet.
  scripts\build-windows.ps1   reviewedLibusbSha256
Dispatch .github/workflows/windows-inputs.yml, review the DLL it produces against
the pinned libusb 1.0.30 source, commit it as $libusbDll, then record its SHA-256 in
this script, in tests\test_libusb_vendor.py and in vendor\README.md.
"@
}
$libusbSha256 = (Get-FileHash -LiteralPath $libusbDll -Algorithm SHA256).Hash.ToLowerInvariant()
if ([string]::IsNullOrWhiteSpace($env:LIBUSB_SHA256)) {
    Fail @"
LIBUSB_SHA256 is required; refusing an unverified native library.
Observed digest: $libusbSha256
"@
}
if ($env:LIBUSB_SHA256 -notmatch '^[0-9a-fA-F]{64}$') {
    Fail 'LIBUSB_SHA256 must be a 64-character hex SHA-256 digest.'
}
$expectedLibusbSha256 = $env:LIBUSB_SHA256.ToLowerInvariant()
if ($expectedLibusbSha256 -ne $reviewedLibusbSha256) {
    Fail 'LIBUSB_SHA256 does not match the reviewed libusb input for this source revision.'
}
if ($expectedLibusbSha256 -ne $libusbSha256) {
    Fail @"
libusb integrity check FAILED: $libusbDll
  expected (LIBUSB_SHA256):   $expectedLibusbSha256
  actual   (Get-FileHash):    $libusbSha256
Refusing to bundle a native library that does not match LIBUSB_SHA256.
"@
}
Write-Host "libusb integrity check passed (sha256 $libusbSha256)."

# PyInstaller separates --add-data source and destination with the platform path
# separator, which is ';' here and ':' on macOS. Passing them as array elements
# keeps PowerShell from treating the semicolon as a statement separator.
#
# The array is not called $args: that is one of PowerShell's own automatic
# variables, and reusing the name invites a subtle failure at the worst moment.
$appName = 'Bitcoin Easy Signer'
$pyInstallerArguments = @(
    '--noconfirm', '--clean', '--windowed', '--onedir', '--name', $appName,
    '--icon', 'assets\AppIcon.ico',
    '--add-data', 'ui.html;.', '--add-data', 'LICENSE;.', '--add-data', 'DISCLAIMER.md;.',
    '--add-data', 'PRIVACY.md;.', '--add-data', 'THIRD-PARTY-NOTICES.md;.',
    '--add-data', 'vendor\libusb-COPYING;.',
    '--collect-data', 'certifi', '--distpath', 'dist', 'desktop.py'
)
& $venvPython -m PyInstaller @pyInstallerArguments
if ($LASTEXITCODE -ne 0) { Fail 'PyInstaller did not build the desktop app.' }

$appDir = Join-Path 'dist' $appName
$appExe = Join-Path $appDir "$appName.exe"
if (-not (Test-Path -LiteralPath $appExe -PathType Leaf)) {
    Fail 'PyInstaller did not produce the Windows executable.'
}

# The one-file helper extracts the bundled DLL to its own private temp directory,
# so the library has to be inside the archive rather than next to the executable.
#
# Two copies go in, and the second one is not redundant. libusb1's loader searches
# its OWN package directory first (usb1\libusb-1.0.dll) and only then the DLL
# search path, and it does that search at import time, before hwi_entry.py gets to
# choose a library. Shipping a copy inside the package is what makes that first
# candidate succeed regardless of how the frozen bundle lays out _MEIPASS; the
# copy at the archive root is the one hwi_entry.py loads and verifies.
$aliasDir = 'build\libusb-alias'
New-Item -ItemType Directory -Path $aliasDir -Force | Out-Null
Copy-Item -LiteralPath $libusbDll -Destination (Join-Path $aliasDir 'libusb-1.0.dll') -Force

& $venvPython -m PyInstaller --noconfirm --clean --onefile --name hwi `
    --collect-all hwilib --collect-all hid --collect-all requests `
    --collect-all urllib3 --collect-all certifi `
    --add-binary "$libusbDll;." --add-binary 'build\libusb-alias\libusb-1.0.dll;usb1' `
    --distpath dist\hwi scripts\hwi_entry.py
if ($LASTEXITCODE -ne 0) { Fail 'PyInstaller did not build the HWI helper.' }

$hwiExe = Join-Path $appDir 'hwi.exe'
Copy-Item -LiteralPath 'dist\hwi\hwi.exe' -Destination $hwiExe -Force
& $hwiExe --help > $null
if ($LASTEXITCODE -ne 0) { Fail 'The bundled HWI helper could not run.' }

# Exercise the exact packaged USB stack: this loads libusb and queries USB
# descriptors without opening a hardware wallet or prompting it.
& $hwiExe --dsh-check-libusb > $null
if ($LASTEXITCODE -ne 0) {
    Fail 'Bundled HWI could not load libusb and query USB devices.'
}

$zip = Join-Path 'dist' "Bitcoin-Easy-Signer-v$Version-windows-x64.zip"
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
Compress-Archive -LiteralPath $appDir -DestinationPath $zip -CompressionLevel Optimal
Write-Host "Created $zip"
Write-Host @"
This build is not code-signed, so Windows SmartScreen will warn on first launch.
Test opening the app, BSMS file import, balance, and the native PSBT save on Windows.
"@
