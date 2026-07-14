# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\Hossein Mobini\\Desktop\\hive-os\\domains', 'domains')]
binaries = []
hiddenimports = ['hiveos', 'hiveos.cli.main', 'hiveos.desktop', 'hiveos.desktop.app', 'hiveos.dashboard', 'hiveos.dashboard.server', 'hiveos.playground', 'hiveos.playground.playground', 'hiveos.playground.runner', 'hiveos.playground.library', 'hiveos.brain', 'hiveos.learning', 'hiveos.storage', 'hiveos.domain', 'hiveos.update', 'uvicorn', 'uvicorn.logging', 'uvicorn.loops.auto', 'uvicorn.protocols.http.auto', 'websockets']
tmp_ret = collect_all('hiveos')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:\\Users\\Hossein Mobini\\Desktop\\hive-os\\src\\hiveos\\desktop\\app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pythoncom', 'pywin32'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HiveOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\Hossein Mobini\\Desktop\\hive-os\\build\\hiveos.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HiveOS',
)
