#!/usr/bin/env python3
"""Lädt die Modellgewichte in den Quellbaum -- ersetzt git-lfs und `git clone`.

    python scripts/fetch_models.py                  # alle Whisper-Modelle
    python scripts/fetch_models.py --only precise   # nur das genaue Modell
    python scripts/fetch_models.py --pyannote       # zusätzlich die Diarisierung

Die Diarisierungs-Gewichte liegen in einem gated repository. Dafür wird ein
HuggingFace-Token gebraucht (`--token` oder die Umgebungsvariable HF_TOKEN),
und die Nutzungsbedingungen müssen einmalig auf
https://huggingface.co/pyannote/speaker-diarization-community-1 bestätigt sein.
Endnutzer brauchen das nicht: der Installer bringt diese Gewichte mit.
"""

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


sys.path.insert(0, str(REPO_ROOT))

# Direkt aus dem Untermodul. `noScribe/__init__.py` importiert bewusst kein
# `main` mehr -- frueher zog schon `import noScribe` die gesamte Anwendung
# mit, und dieses Skript scheiterte mit einem ModuleNotFoundError auf
# AdvancedHTMLParser. Ausgerechnet beim Einrichten, wo man die Gewichte
# holt, BEVOR alles andere installiert ist.
from noScribe.model_download import (  # noqa: E402
    PYANNOTE_MODEL,
    WHISPER_MODELS,
    download,
    is_installed,
)


def _human(num_bytes: int) -> str:
    return f'{num_bytes / 1e6:.0f} MB'


def _progress(name: str):
    state = {'last': -1}

    def report(done: int, total: int) -> None:
        pct = int(done * 100 / total) if total else 0
        if pct != state['last']:
            state['last'] = pct
            print(f'\r  {name}: {pct:3d}%  ({_human(done)} / {_human(total)})',
                  end='', flush=True)

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--target', type=Path, default=REPO_ROOT,
                        help='Wurzelverzeichnis (Vorgabe: das Repository)')
    parser.add_argument('--only', choices=sorted(WHISPER_MODELS), action='append',
                        help='nur dieses Whisper-Modell laden (mehrfach möglich)')
    parser.add_argument('--skip-whisper', action='store_true',
                        help='kein Whisper-Modell laden (für den Installer-Build)')
    parser.add_argument('--pyannote', action='store_true',
                        help='auch die Diarisierungs-Gewichte laden (braucht HF_TOKEN)')
    parser.add_argument('--force', action='store_true',
                        help='auch dann laden, wenn das Modell schon da ist')
    parser.add_argument('--token', default=os.environ.get('HF_TOKEN'),
                        help='HuggingFace-Token (Vorgabe: $HF_TOKEN)')
    args = parser.parse_args()

    wanted = [] if args.skip_whisper else (args.only or sorted(WHISPER_MODELS))

    for name in wanted:
        target = args.target / 'models' / name
        if is_installed(target) and not args.force:
            print(f'{name}: bereits vorhanden ({target})')
            continue
        print(f'{name}: lade {WHISPER_MODELS[name].repo_id}')
        download(WHISPER_MODELS[name], target, on_progress=_progress(name))
        print(f'\r  {name}: fertig -> {target}' + ' ' * 20)

    if args.pyannote:
        target = args.target / 'pyannote'
        if not args.token:
            print('pyannote: kein HuggingFace-Token. Setze HF_TOKEN oder nutze --token.',
                  file=sys.stderr)
            return 1
        # Anders als bei Whisper werden hier nur zwei Dateien in ein bereits
        # bestehendes Verzeichnis nachgelegt.
        print(f'pyannote: lade {PYANNOTE_MODEL.repo_id}')
        _download_into(target, args.token)
        print('  pyannote: fertig')

    return 0


def _download_into(target: Path, token: str) -> None:
    """Legt segmentation/ und embedding/ neben die schon versionierte config.yaml."""
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=PYANNOTE_MODEL.repo_id,
        local_dir=str(target),
        allow_patterns=PYANNOTE_MODEL.allow_patterns,
        token=token,
    )


if __name__ == '__main__':
    sys.exit(main())
