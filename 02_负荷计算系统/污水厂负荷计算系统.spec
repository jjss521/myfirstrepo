# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_load_calc.py'],
    pathex=[],
    binaries=[],
    datas=[('load_calc', 'load_calc')],
    hiddenimports=['tkinterdnd2', 'matplotlib', 'matplotlib.backends.backend_tkagg', 'matplotlib.backends.backend_agg', 'openpyxl', 'xlrd', 'ttkbootstrap'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6', 'PySide2', 'PyQt5', 'PyQt6', 'PyQt4'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='污水厂负荷计算系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
