# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

root_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
version_file = os.path.join(root_dir, "build", "version_info.txt")
icon_path = os.path.join(root_dir, "assets", "app.ico")
icon = icon_path if os.path.exists(icon_path) else None

hidden = [
    "bcrypt",
    "reportlab",
    "reportlab.pdfgen",
    "reportlab.lib",
    "reportlab.pdfbase",
    "reportlab.pdfbase.ttfonts",
    "reportlab.pdfbase.pdfmetrics",
]
hidden += collect_submodules("ui")
hidden += collect_submodules("services")
hidden += collect_submodules("db")
hidden += collect_submodules("utils")

asset_datas = []
logo_path = os.path.join(root_dir, "assets", "logo.png")
if os.path.exists(logo_path):
    asset_datas.append((logo_path, "assets"))
if icon and os.path.exists(icon):
    asset_datas.append((icon, "assets"))

a = Analysis(
    ["app.py"],
    pathex=[root_dir],
    binaries=[],
    datas=asset_datas,
    hiddenimports=hidden,
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
    name="United Agencies karachi",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon,
    version=version_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="United Agencies karachi",
)
