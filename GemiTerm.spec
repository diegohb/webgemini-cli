# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\gemiterm\\__main__.py'],
    pathex=['C:\\Python314'],
    binaries=[],
    datas=[('src/gemiterm', 'gemiterm')],
    hiddenimports=['rich', 'rich.console', 'rich.progress', 'rich.table', 'rich.panel', 'rich.markdown', 'rich.syntax', 'click', 'playwright', 'gemini_webapi', 'gemini_webapi_async'],
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
    name='GemiTerm',
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
