# -*- mode: python ; coding: utf-8 -*-
"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
PyInstaller Spec: RayRabbit Ecosystem (Cross-Platform)
SPDX-License-Identifier: AGPL-3.0-only
"""
import sys
import platform
from pathlib import Path

block_cipher = None
project_root = Path.cwd()

# Archivos de datos y recursos estáticos
datas = [
    (str(project_root / 'config.yaml'), '.'),
    (str(project_root / 'rayrabbit' / 'resources'), 'rayrabbit/resources'),
]

# Hidden imports necesarios para Uvicorn, FastAPI, WebSockets y LiteLLM
hiddenimports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'starlette',
    'pydantic',
    'cryptography',
    'websockets',
    'colorama',
    'apscheduler',
    'prompt_toolkit',
    'rayrabbit',
    'rayrabbit.cli.main',
    'rayrabbit.cli.orchestrator',
    'rayrabbit.core.message_bus',
    'rayrabbit.protocols.mcp',
    'rayrabbit.protocols.a2a',
    'rayrabbit.protocols.a2ui',
    'rayrabbit.utils.config',
    'rayrabbit.security.keystore',
    'rayrabbit.security.jws'
]

# Selección de iconos y metadatos de versión según la plataforma
system = platform.system()
icon_file = None
version_file = None

if system == 'Windows':
    icon_file = str(project_root / 'rayrabbit' / 'resources' / 'icons' / 'rayrabbit-ai.ico')
    version_file = str(project_root / 'scripts' / 'file_version_info.txt')
elif system == 'Darwin':
    icon_file = str(project_root / 'rayrabbit' / 'resources' / 'icons' / 'rayrabbit-ai.icns')

a = Analysis(
    ['run_local_rayrabbit_cluster.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if system == 'Windows':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='rayrabbit-ecosystem',
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
        version=version_file,
        icon=icon_file,
    )
elif system == 'Darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='rayrabbit-ecosystem',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,
        icon=icon_file,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='rayrabbit-ecosystem',
    )
    app = BUNDLE(
        coll,
        name='RayRabbit Ecosystem.app',
        icon=icon_file,
        bundle_identifier='ai.rayrabbit.ecosystem',
        info_plist={
            'CFBundleDisplayName': 'RayRabbit Ecosystem',
            'CFBundleName': 'RayRabbit Ecosystem',
            'CFBundleVersion': '0.1.0',
            'CFBundleShortVersionString': '0.1.0',
            'NSHighResolutionCapable': 'True'
        }
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='rayrabbit-ecosystem',
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
