# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import PyInstaller.config

USER_PATH = Path("dist")

PyInstaller.config.CONF['distpath'] = str(USER_PATH)

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/schema.sql', 'src'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='can-daq',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)