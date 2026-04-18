# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/gemiterm/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'asyncio',
        'rich',
        'rich.console',
        'rich.progress',
        'rich.table',
        'rich.panel',
        'rich.markdown',
        'rich.syntax',
        'click',
        'playwright',
        'gemini_webapi',
        'gemini_webapi_async',
    ],
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
    [],
    exclude_binaries=True,
    name='GemiTerm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GemiTerm',
)
