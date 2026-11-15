param(
    [switch]$Installer,
    [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"

$runningBuild = Get-Process -Name "ScreenTranslator" -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like "$PWD\dist\ScreenTranslator\*" } |
    Select-Object -First 1
if ($runningBuild) {
    throw "Close the running Screen Translator (PID $($runningBuild.Id)) before rebuilding."
}

$python = if (Test-Path -LiteralPath ".venv\Scripts\python.exe") {
    ".venv\Scripts\python.exe"
} else {
    "python"
}

& $python "scripts\cache_ocr_models.py"
if ($LASTEXITCODE -ne 0) { throw "Unable to cache OCR models" }

& $python -m PyInstaller --noconfirm "ScreenTranslator.spec"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }
& ".\scripts\fix_pyside_runtime.ps1"

$modelSource = "data\models\paddlex"
$modelDestination = "dist\ScreenTranslator\data\models\paddlex"
if (Test-Path -LiteralPath $modelSource) {
    New-Item -ItemType Directory -Path (Split-Path $modelDestination) -Force | Out-Null
    Copy-Item -LiteralPath $modelSource -Destination $modelDestination -Recurse -Force
}

$assetDestination = "dist\ScreenTranslator\assets"
New-Item -ItemType Directory -Path $assetDestination -Force | Out-Null
Copy-Item -LiteralPath "assets\screen_translator.ico" `
    -Destination "$assetDestination\screen_translator.ico" -Force

Write-Host "Build ready: dist\ScreenTranslator\ScreenTranslator.exe"

if ($Installer) {
    $isccCandidates = @(
        "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue).Source
    )
    $iscc = $isccCandidates |
        Where-Object { $_ -and (Test-Path -LiteralPath $_) } |
        Select-Object -First 1
    if (-not $iscc) {
        throw "Inno Setup 6 is required to create the installer: https://jrsoftware.org/isdl.php"
    }
    & $iscc "/DMyAppVersion=$Version" "installer.iss"
    if ($LASTEXITCODE -ne 0) { throw "Installer build failed" }
    Write-Host "Installer ready: dist\installer\ScreenTranslator-Setup.exe"
}
