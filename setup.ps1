# Traudi - Einrichtung für Entwickler (Windows).
#
#   .\setup.ps1            # CPU-Variante
#   .\setup.ps1 -Cuda      # mit CUDA 12.8
#   .\setup.ps1 -NoModels  # ohne Modell-Download
#
# Endnutzer brauchen das nicht: für sie gibt es den Installer unter
# https://github.com/krissi15/noScribe_own/releases

[CmdletBinding()]
param(
    [switch]$Cuda,
    [switch]$NoModels
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

# pip und huggingface_hub schreiben ihre Fortschrittsbalken nach stderr. Mit
# ErrorActionPreference = 'Stop' macht PowerShell daraus einen abbrechenden
# NativeCommandError, obwohl der Befehl erfolgreich war. Deshalb laufen native
# Aufrufe hier mit 'Continue' und werden über den Exit-Code geprüft.
function Invoke-Native {
    $ErrorActionPreference = 'Continue'
    & $args[0] @($args[1..($args.Count - 1)])
    if ($LASTEXITCODE -ne 0) {
        throw "Befehl fehlgeschlagen (Exit-Code $LASTEXITCODE): $($args -join ' ')"
    }
}

$python = 'py'
$pyArgs = @('-3.12')
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    $python = 'python'
    $pyArgs = @()
}

if (-not (Test-Path 'venv')) {
    Write-Host '==> Erstelle virtuelle Umgebung in venv\'
    Invoke-Native $python @pyArgs -m venv venv
}

$venvPython = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'

Write-Host '==> Aktualisiere pip'
Invoke-Native $venvPython -m pip install --upgrade pip --quiet

if ($Cuda) {
    Write-Host '==> Installiere Abhängigkeiten (CUDA 12.8)'
    Invoke-Native $venvPython -m pip install -r environments\requirements_win_cuda.txt
} else {
    Write-Host '==> Installiere Abhängigkeiten (CPU)'
    Invoke-Native $venvPython -m pip install -r environments\requirements_win_cpu.txt
}

if (-not $NoModels) {
    Write-Host '==> Lade Sprachmodelle (einmalig, ca. 2,4 GB)'
    Invoke-Native $venvPython scripts\fetch_models.py

    if ($env:HF_TOKEN) {
        Write-Host '==> Lade Diarisierungs-Gewichte'
        Invoke-Native $venvPython scripts\fetch_models.py --skip-whisper --pyannote
    } else {
        Write-Warning 'HF_TOKEN ist nicht gesetzt - die Sprechererkennung bleibt ohne Gewichte.'
        Write-Warning 'Bedingungen bestaetigen: https://huggingface.co/pyannote/speaker-diarization-community-1'
        Write-Warning 'Danach:  $env:HF_TOKEN = "hf_..."'
        Write-Warning '         venv\Scripts\python.exe scripts\fetch_models.py --skip-whisper --pyannote'
    }
}

Write-Host ''
Write-Host 'Fertig. Starten mit:'
Write-Host '    venv\Scripts\activate'
Write-Host '    python -m noScribe'
