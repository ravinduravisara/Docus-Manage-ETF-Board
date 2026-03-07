# -*- mode: python ; coding: utf-8 -*-
import os, sys
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

# Collect everything from pymupdf (DLLs, data, etc.)
pymupdf_datas, pymupdf_binaries, pymupdf_hiddenimports = collect_all('pymupdf')
fitz_datas, fitz_binaries, fitz_hiddenimports = collect_all('fitz')

all_datas = pymupdf_datas + fitz_datas + [('assets', 'assets')]
all_binaries = pymupdf_binaries + fitz_binaries
all_hiddenimports = pymupdf_hiddenimports + fitz_hiddenimports + [
    'pymupdf', 'pymupdf._extra', 'pymupdf.mupdf',
    'fitz', 'fitz.fitz',
    'PIL', 'PIL.Image',
    'sqlalchemy', 'sqlalchemy.dialects.sqlite',
]

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DocusManage',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='assets/app_icon.ico' if os.path.exists('assets/app_icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='DocusManage',
)
