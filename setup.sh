#!/usr/bin/env bash
# Traudi - Einrichtung für Entwickler (macOS / Linux).
#
#   ./setup.sh              # Modelle mitladen
#   ./setup.sh --no-models  # nur die Abhängigkeiten

set -euo pipefail
cd "$(dirname "$0")"

no_models=0
for arg in "$@"; do
    case "$arg" in
        --no-models) no_models=1 ;;
        *) echo "Unbekannte Option: $arg" >&2; exit 1 ;;
    esac
done

case "$(uname -s)" in
    Darwin) requirements=environments/requirements_macOS_arm64.txt ;;
    Linux)  requirements=environments/requirements_linux.txt ;;
    *) echo "Nicht unterstütztes System: $(uname -s)" >&2; exit 1 ;;
esac

python=$(command -v python3.12 || command -v python3)

if [ ! -d venv ]; then
    echo '==> Erstelle virtuelle Umgebung in venv/'
    "$python" -m venv venv
fi

echo '==> Aktualisiere pip'
venv/bin/python -m pip install --upgrade pip --quiet

if [ "$requirements" = environments/requirements_linux.txt ]; then
    # Getrennter erster Aufruf, damit torch aus dem CPU-Index kommt und nicht
    # als CUDA-Rad von PyPI -- siehe Kommentar in der Requirements-Datei.
    echo '==> Installiere torch (CPU-Index)'
    venv/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu \
        torch==2.8 torchaudio==2.8
fi

echo "==> Installiere Abhängigkeiten aus $requirements"
venv/bin/python -m pip install -r "$requirements"

if [ "$no_models" -eq 0 ]; then
    echo '==> Lade Sprachmodelle (einmalig, ca. 2,4 GB)'
    venv/bin/python scripts/fetch_models.py

    if [ -n "${HF_TOKEN:-}" ]; then
        echo '==> Lade Diarisierungs-Gewichte'
        venv/bin/python scripts/fetch_models.py --skip-whisper --pyannote
    else
        echo 'WARNUNG: HF_TOKEN ist nicht gesetzt - die Sprechererkennung bleibt ohne Gewichte.' >&2
        echo 'Bedingungen bestätigen: https://huggingface.co/pyannote/speaker-diarization-community-1' >&2
        echo 'Danach:  export HF_TOKEN=hf_...' >&2
        echo '         venv/bin/python scripts/fetch_models.py --skip-whisper --pyannote' >&2
    fi
fi

echo
echo 'Fertig. Starten mit:'
echo '    source venv/bin/activate'
echo '    python -m noScribe'
