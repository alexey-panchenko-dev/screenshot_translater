param(
    [string]$Distribution = "dist\ScreenTranslator"
)

$ErrorActionPreference = "Stop"
$internal = Join-Path $Distribution "_internal"
$pyside = Join-Path $internal "PySide6"

if (-not (Test-Path -LiteralPath $pyside)) {
    throw "PySide6 runtime directory not found: $pyside"
}

# PySide6 ships the exact MSVC runtime revision its Qt binaries were built
# against.  Portable Python distributions can contribute another revision at
# the application root, which wins Windows' DLL search and makes QtCore fail
# with ERROR_PROC_NOT_FOUND. Keep PySide6's matching copies at the root.
$runtimeNames = @(
    "MSVCP140.dll",
    "MSVCP140_1.dll",
    "MSVCP140_2.dll",
    "VCRUNTIME140.dll",
    "VCRUNTIME140_1.dll"
)

foreach ($name in $runtimeNames) {
    $source = Join-Path $pyside $name
    if (Test-Path -LiteralPath $source) {
        Copy-Item -LiteralPath $source -Destination (Join-Path $internal $name) -Force
    }
}

# PyInstaller discovers ICU 78 through another dependency.  Qt 6.12 on this
# Windows installation imports the system ICU ABI instead; the bundled copy
# shadows it and QtCore aborts with ERROR_PROC_NOT_FOUND.
foreach ($name in @("icuuc.dll", "icudt78.dll")) {
    $path = Join-Path $internal $name
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Force
    }
}
