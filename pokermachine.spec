# -*- mode: python ; coding: utf-8 -*-
# PokerMachine, il file di compilazione per PyInstaller.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 09/09/2026: nasce con la revisione 1. Il .gitignore fa eccezione per questo file.

# La collezione dei suoni condivisa va portata dentro il pacchetto, altrimenti
# Acusticator non la trova e l'eseguibile resta muto. La guida viaggia con lui.
# Il pacchetto e' un file unico: dentro dist c'e' soltanto l'eseguibile.
import os

import GBUtils

COLLEZIONE = os.path.join(os.path.dirname(GBUtils.__file__), 'Acu_Collection.json')

a = Analysis(
    ['pokermachine.py'],
    pathex=[],
    binaries=[],
    datas=[(COLLEZIONE, '.'), ('manuale.txt', '.')],
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
    name='pokermachine',
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
