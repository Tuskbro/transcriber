# -*- mode: python ; coding: utf-8 -*-

shared_options = [("X utf8", None, "OPTION")]
common = dict(
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

gui_a = Analysis(["gui.py"], **common)
cli_a = Analysis(["cli_entry.py"], **common)
chat_a = Analysis(["chat_export_entry.py"], **common)

gui_pyz = PYZ(gui_a.pure)
cli_pyz = PYZ(cli_a.pure)
chat_pyz = PYZ(chat_a.pure)

gui_exe = EXE(
    gui_pyz,
    gui_a.scripts,
    shared_options,
    [],
    exclude_binaries=True,
    name="Transcriber",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    version="version_info.txt",
)

cli_exe = EXE(
    cli_pyz,
    cli_a.scripts,
    shared_options,
    [],
    exclude_binaries=True,
    name="TranscriberCLI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    version="version_info.txt",
)

chat_exe = EXE(
    chat_pyz,
    chat_a.scripts,
    shared_options,
    [],
    exclude_binaries=True,
    name="ChatExportParser",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    version="version_info.txt",
)

bundle = COLLECT(
    gui_exe,
    cli_exe,
    chat_exe,
    gui_a.binaries,
    gui_a.datas,
    cli_a.binaries,
    cli_a.datas,
    chat_a.binaries,
    chat_a.datas,
    strip=False,
    upx=True,
    name="Transcriber",
)