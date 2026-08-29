<#
.SYNOPSIS
    Bootstrap Zero-Friction para Entorno de Desarrollo de RayRabbit OSS en Windows.
.DESCRIPTION
    Este script verifica si Python está instalado (y lo instala vía winget si es necesario),
    crea un entorno virtual (venv) en el directorio actual, y realiza la instalación
    en modo editable (dev). Soporta ejecución desde cualquier ruta mediante $PSScriptRoot.
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🐇 RayRabbit OSS - Inicializando Entorno de Desarrollo" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Anclaje en Memoria (Elimina necesidad de buscar la ruta)
$RepoPath = $PSScriptRoot
Set-Location -Path $RepoPath
Write-Host "[Info] Directorio anclado: $RepoPath" -ForegroundColor DarkGray

# 2. Verificación de Python
$PythonExe = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $PythonExe) {
    Write-Host "[!] Python no detectado en el sistema." -ForegroundColor Yellow
    $WingetExe = Get-Command "winget" -ErrorAction SilentlyContinue
    
    if ($WingetExe) {
        Write-Host "-> Intentando instalar Python 3.11 automáticamente vía winget..." -ForegroundColor Cyan
        Start-Process -FilePath "winget" -ArgumentList "install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements" -Wait -NoNewWindow
        
        # Refrescar entorno
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $PythonExe = Get-Command "python" -ErrorAction SilentlyContinue
        
        if (-not $PythonExe) {
            Write-Host "[X] Se intentó instalar Python, pero el ejecutable no está disponible en el PATH." -ForegroundColor Red
            Write-Host "Por favor, reinicia la terminal o instala Python manualmente desde Microsoft Store." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[X] 'winget' no está disponible. No se pudo instalar Python automáticamente." -ForegroundColor Red
        Write-Host "Por favor, instala Python 3.10+ manualmente y vuelve a ejecutar este script." -ForegroundColor Red
        exit 1
    }
}

$PyVersion = (python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
Write-Host "[OK] Python detectado: $PyVersion" -ForegroundColor Green

# 3. Creación del Entorno Virtual (VENV)
$VenvPath = Join-Path -Path $RepoPath -ChildPath "venv"
if (-not (Test-Path -Path $VenvPath)) {
    Write-Host "-> Creando Entorno Virtual (venv)..." -ForegroundColor Cyan
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Error creando el entorno virtual." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[Info] Entorno Virtual ya existente en 'venv/'." -ForegroundColor DarkGray
}

$PipExe = Join-Path -Path $VenvPath -ChildPath "Scripts\pip.exe"
if (-not (Test-Path -Path $PipExe)) {
    Write-Host "[X] Pip no encontrado en el entorno virtual." -ForegroundColor Red
    exit 1
}

# 4. Instalación de Dependencias
Write-Host "-> Actualizando PIP..." -ForegroundColor Cyan
& $PipExe install --upgrade pip --quiet

Write-Host "-> Instalando RayRabbit OSS en modo Editable (dev)..." -ForegroundColor Cyan
& $PipExe install -e ".[dev,all]"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Error durante la instalación de dependencias." -ForegroundColor Red
    exit 1
}

# 5. Generación de Identidad Visual y Acceso Directo de Escritorio
Write-Host "-> Configurando identidad visual y acceso directo en el Escritorio..." -ForegroundColor Cyan
$PythonVenv = Join-Path -Path $VenvPath -ChildPath "Scripts\python.exe"
& $PythonVenv (Join-Path -Path $RepoPath -ChildPath "scripts\create_desktop_shortcut.py")

# 6. Mensaje de Éxito
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "✅ Ecosistema Soberano Instalado Correctamente." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "🐰 Puedes iniciar el sistema con doble clic en el acceso directo 'RayRabbit Ecosystem' en tu Escritorio," -ForegroundColor Cyan
Write-Host "   o activar el entorno en esta terminal con:" -ForegroundColor White
Write-Host "    .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "Luego puedes levantar el ecosistema con:" -ForegroundColor White
Write-Host "    rayrabbit start" -ForegroundColor Yellow
Write-Host ""
