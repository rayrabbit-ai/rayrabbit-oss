"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.
SPDX-License-Identifier: AGPL-3.0-only
"""
from pathlib import Path

VERSION_INFO_TEMPLATE = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(0, 1, 0, 0),
    prodvers=(0, 1, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', 'RayRabbit Labs, Inc.'),
            StringStruct('FileDescription', 'RayRabbit Ecosystem'),
            StringStruct('FileVersion', '0.1.0.0'),
            StringStruct('InternalName', 'rayrabbit-ecosystem'),
            StringStruct('LegalCopyright', 'Copyright (C) 2024-2026 RayRabbit Labs, Inc. Licensed under AGPL-3.0.'),
            StringStruct('OriginalFilename', 'rayrabbit-ecosystem.exe'),
            StringStruct('ProductName', 'RayRabbit Ecosystem'),
            StringStruct('ProductVersion', '0.1.0.0')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""

def generate_version_info(target_path: Path = None) -> Path:
    """Genera el archivo de recursos de versión para compilación de Windows PE."""
    if target_path is None:
        target_path = Path.cwd() / "scripts" / "file_version_info.txt"
    
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(VERSION_INFO_TEMPLATE, encoding="utf-8")
    return target_path

if __name__ == "__main__":
    out = generate_version_info()
    print(f"Windows Version Info generado en: {out}")
