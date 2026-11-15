from PyInstaller.utils.hooks import collect_all, copy_metadata

datas = []
binaries = []
hiddenimports = []
datas.append(("assets/screen_translator.ico", "assets"))
for package in ("paddle", "paddleocr", "paddlex", "cv2", "cmudict"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

# PaddleX checks these installed distributions at runtime before creating its
# OCR pipeline. PyInstaller otherwise keeps their modules but drops the
# dist-info metadata, so PaddleX incorrectly reports missing dependencies.
for distribution in (
    "paddlex",
    "imagesize",
    "opencv-contrib-python",
    "pyclipper",
    "pypdfium2",
    "python-bidi",
    "shapely",
):
    datas += copy_metadata(distribution)

analysis = Analysis(
    ["src/screen_translator/main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=[],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="ScreenTranslator",
    icon="assets/screen_translator.ico",
    console=False,
    disable_windowed_traceback=False,
)
collection = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    name="ScreenTranslator",
)
