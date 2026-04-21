# Установка Ollama на Windows (нативно) или через WSL2.
# Запуск в PowerShell (от имени пользователя; при необходимости — «Запуск от имени администратора»):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\deploy\install_ollama.ps1

$ErrorActionPreference = "Stop"

function Test-Wsl {
    try {
        wsl --status 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch { return $false }
}

Write-Host "=== Ollama: установка ===" -ForegroundColor Cyan

# --- Вариант A: WSL2 (рекомендуется для совпадения с Linux-инструкциями) ---
if (Test-Wsl) {
    Write-Host "Обнаружен WSL. Запуск Linux-скрипта в WSL (Ubuntu по умолчанию)..." -ForegroundColor Yellow
    $scriptLinux = Join-Path $PSScriptRoot "install_ollama.sh"
    if (-not (Test-Path $scriptLinux)) {
        Write-Error "Не найден $scriptLinux. Запустите из корня репозитория."
    }
    $winPath = (Resolve-Path .).Path
    $wslPath = (wsl wslpath -a $winPath).Trim()
    wsl -e bash -lc "cd '$wslPath' && chmod +x deploy/install_ollama.sh && ./deploy/install_ollama.sh"
    exit $LASTEXITCODE
}

# --- Вариант B: нативный Windows ---
Write-Host "Установка нативного Ollama для Windows..." -ForegroundColor Yellow

$winget = Get-Command winget -ErrorAction SilentlyContinue
if ($winget) {
    Write-Host "winget install Ollama.Ollama ..."
    winget install --id Ollama.Ollama -e --accept-source-agreements --accept-package-agreements
} else {
    Write-Host @"
winget не найден. Установите Ollama вручную:
  https://ollama.com/download/windows

После установки откройте новый терминал и выполните:
  ollama pull qwen2.5:7b-instruct
"@
    exit 1
}

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Host "Перезапустите терминал или добавьте Ollama в PATH, затем: ollama pull qwen2.5:7b-instruct"
    exit 0
}

& ollama --version
Write-Host "Загрузка модели qwen2.5:7b-instruct..."
& ollama pull qwen2.5:7b-instruct

Write-Host "Проверка: Invoke-RestMethod http://localhost:11434/api/tags"
try {
    Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get | ConvertTo-Json -Depth 5
} catch {
    Write-Host "API пока недоступен. Запустите приложение Ollama из меню Пуск и повторите проверку."
}
