# Screen Translator

Screen Translator is a Windows desktop and tray application: press `Alt+Q`, drag over text,
and a Russian/English translation appears next to the selected region.

## Install from GitHub

Open the latest GitHub Release, download `ScreenTranslator-Setup.exe`, and run it. The installer
does not require administrator rights, creates Start menu and optional Desktop shortcuts, and
can be removed from **Windows Settings → Apps**. Python is not required on the user's PC.

The first Windows SmartScreen prompt can appear because community builds are not code-signed;
choose **More info → Run anyway**.

For maintainers, pushing a version tag builds and publishes the installer automatically:

```powershell
git tag v0.1.0
git push origin v0.1.0
```

The same build can be started manually from **GitHub → Actions → Build Windows installer**;
in that case the setup executable is available as a workflow artifact.

## Ready-to-run local build

After running `build.ps1`, launch:

```text
dist\ScreenTranslator\ScreenTranslator.exe
```

Keep the whole `ScreenTranslator` folder together; the executable needs its `_internal` and
`data` subfolders. The app opens a dark main window, stays in the notification area, and does
not open a console.

Usage:

1. Run `ScreenTranslator.exe`.
2. Press `Alt+Q`.
3. Drag a rectangle around the text. Press `Escape` to cancel.
4. Use **Copy** or **Save** in the popup, or close it with **×**.
5. To stop the program, right-click its tray icon and choose **Exit**.

The main window has an on/off button and a dictionary with separate English → Russian and
Russian → English tabs. Closing the window hides it to the tray; click the tray icon or choose
**Open** in its menu to show it again.

OCR runs locally with PaddleOCR. Translation uses Google's public web translation endpoint and
therefore sends only the recognized text (not the screenshot) over the network. No API key is
required. Screenshots, logs, settings, and SQLite history stay under the build's `data`/`logs`
folders.

Every successful translation is also appended to the readable UTF-8 dictionary at
`data\dictionary.md`. The temporary capture is deleted when its popup is closed or expires;
abandoned captures and leftovers from an earlier run are cleaned automatically.

## Features

- native global `Alt+Q` hotkey without administrator privileges;
- DPI-aware selection and capture, including Windows scaling such as 125%;
- local Russian/English OCR on a background thread;
- automatic language direction (`ru` ↔ `en`);
- popup with original text, translation, Copy, and Save;
- dark main window with a synchronized enable/disable control;
- dictionary cards grouped by translation direction;
- a persistent circular learned/not-learned marker on every dictionary card;
- local SQLite history and tray settings;
- latest-request policy so repeated captures do not create an unbounded queue;
- bundled OCR models, so the supplied build does not need a first-run model download.

## Development setup

Requires Windows 10/11 and Python 3.12 or 3.13. PaddlePaddle currently has no compatible
Windows wheel for Python 3.14.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
.venv\Scripts\python.exe -m screen_translator.main
```

Checks and reproducible folder/installer build:

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.\build.ps1
# To also create dist\installer\ScreenTranslator-Setup.exe (requires Inno Setup 6):
.\build.ps1 -Installer -Version 0.1.0
```

`build.ps1` downloads the required local OCR models when missing, applies the Windows Qt/ICU
runtime fix, and bundles the models into the distribution. The result works without Python and
does not download OCR models on first launch. Inno Setup 6 is the only additional installer-build
dependency; end users do not need it.

## Architecture

```text
src/screen_translator/
    main.py              application composition and DPI setup
    capture/             native hotkey, overlay geometry, mss capture
    core/                settings, language detection, pipeline orchestration
    ocr/                 PaddleOCR adapter, preprocessing, worker thread
    translation/         provider abstraction, Google web adapter, worker thread
    ui/                  overlay, translation popup, tray, settings dialog
    storage/             SQLite records and storage worker
tests/
scripts/                 packaging/runtime helpers
```

## Known limitations

- Recognition still depends on contrast and the selected pixels; include a small margin around
  very short text.
- Translation requires internet access and availability of the public Google endpoint.
- Mixed-DPI layouts with multiple monitors should be checked on the actual monitor arrangement.
- If another program already owns `Alt+Q`, the tray reports the hotkey conflict.
