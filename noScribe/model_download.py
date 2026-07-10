# Traudi - Bezug der Modellgewichte
# Copyright (C) 2026
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Lädt die Modellgewichte von HuggingFace, ohne git und git-lfs.

Die beiden Whisper-Modelle sind zu groß für den Installer (0,8 bzw. 1,6 GB) und
werden deshalb beim ersten Start in das Nutzerverzeichnis geladen. Die
Diarisierungs-Gewichte sind zusammen nur 32 MB und liegen im Installer bei --
sonst bräuchte jeder Endnutzer einen HuggingFace-Token, denn ``pyannote`` ist
ein gated repository.
"""

import dataclasses
import logging
import shutil
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int], None]
"""Wird mit (geladene Bytes, erwartete Bytes) aufgerufen."""


@dataclasses.dataclass(frozen=True)
class ModelSpec:
    name: str
    repo_id: str
    allow_patterns: Optional[list]
    # Unterordner im Repo, dessen Inhalt nach oben gezogen wird.
    strip_prefix: Optional[str] = None
    # Gated repositories verlangen einen HuggingFace-Token.
    gated: bool = False


WHISPER_MODELS = {
    'precise': ModelSpec(
        name='precise',
        # Frühere Repo-ID mobiuslabsgmbh/... leitet hierher weiter.
        repo_id='dropbox-dash/faster-whisper-large-v3-turbo',
        allow_patterns=['config.json', 'model.bin', 'preprocessor_config.json',
                        'tokenizer.json', 'vocabulary.json'],
    ),
    'fast': ModelSpec(
        name='fast',
        repo_id='mukowaty/faster-whisper-int8',
        allow_patterns=['faster-whisper-large-v3-turbo-int8/*'],
        strip_prefix='faster-whisper-large-v3-turbo-int8',
    ),
}

PYANNOTE_MODEL = ModelSpec(
    name='pyannote',
    repo_id='pyannote/speaker-diarization-community-1',
    allow_patterns=['segmentation/pytorch_model.bin', 'embedding/pytorch_model.bin'],
    gated=True,
)


def is_installed(model_dir: Path) -> bool:
    """faster-whisper braucht eine model.bin; alles andere ist Beiwerk."""
    return (model_dir / 'model.bin').is_file()


PYANNOTE_WEIGHTS = ('segmentation/pytorch_model.bin', 'embedding/pytorch_model.bin')


def pyannote_weights_present(pyannote_dir: Path) -> bool:
    """Die beiden großen .bin-Dateien liegen nicht im Repository."""
    return all((Path(pyannote_dir) / rel).is_file() for rel in PYANNOTE_WEIGHTS)


def missing_whisper_models(*search_dirs: Path) -> list:
    """Namen der Whisper-Modelle, die in keinem der Verzeichnisse liegen."""
    missing = []
    for name in WHISPER_MODELS:
        if not any(is_installed(Path(d) / name) for d in search_dirs if d):
            missing.append(name)
    return missing


def expected_size(spec: ModelSpec, token: Optional[str] = None) -> int:
    """Summe der Dateigrößen in Bytes. 0, wenn HuggingFace nicht erreichbar ist."""
    from huggingface_hub import HfApi

    try:
        info = HfApi().model_info(spec.repo_id, files_metadata=True, token=token)
    except Exception as exc:
        logger.warning("Could not read size of %s: %s", spec.repo_id, exc)
        return 0

    total = 0
    for sibling in info.siblings or []:
        if _matches(sibling.rfilename, spec.allow_patterns):
            total += sibling.size or 0
    return total


def _matches(filename: str, patterns: Optional[list]) -> bool:
    if not patterns:
        return True
    import fnmatch
    return any(fnmatch.fnmatch(filename, pat) for pat in patterns)


def _dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())


def download(spec: ModelSpec, target: Path, token: Optional[str] = None,
             on_progress: Optional[ProgressCallback] = None) -> Path:
    """Lädt ein Modell nach ``target``.

    Geladen wird zunächst nach ``<target>.part``; erst ein vollständiger
    Download wandert an seinen endgültigen Platz. Ein Abbruch hinterlässt damit
    kein Verzeichnis, das ``is_installed`` fälschlich für fertig hält.

    ``target`` wird nicht ersetzt, sondern ergänzt: dort liegt bereits die
    versionierte NOSCRIBE_README.txt, die der Installer-Build braucht.
    """
    from huggingface_hub import snapshot_download

    target = Path(target)
    staging = target.parent / (target.name + '.part')
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    total = expected_size(spec, token) if on_progress else 0
    stop_polling = _start_progress_poll(staging, total, on_progress)
    try:
        snapshot_download(
            repo_id=spec.repo_id,
            local_dir=str(staging),
            allow_patterns=spec.allow_patterns,
            token=token,
        )
    except BaseException:
        # Sonst bliebe ein halber Download liegen, den der Modell-Scanner bei
        # jedem Start als unbrauchbares Verzeichnis anmeckert.
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        stop_polling()

    # snapshot_download leaves its bookkeeping in .cache/huggingface.
    shutil.rmtree(staging / '.cache', ignore_errors=True)

    source = staging / spec.strip_prefix if spec.strip_prefix else staging
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        destination = target / item.name
        if destination.is_dir():
            shutil.rmtree(destination)
        elif destination.exists():
            destination.unlink()
        shutil.move(str(item), str(destination))
    shutil.rmtree(staging, ignore_errors=True)

    if on_progress and total:
        on_progress(total, total)
    return target


def _start_progress_poll(watch_dir: Path, total: int, on_progress):
    """Meldet den Fortschritt anhand der Größe des Zielverzeichnisses.

    Das ist gröber als ein Callback aus huggingface_hub, hängt aber an keinem
    undokumentierten tqdm-Interna.
    """
    if not on_progress or not total:
        return lambda: None

    import threading

    done = threading.Event()

    def _poll():
        while not done.wait(0.5):
            try:
                on_progress(min(_dir_size(watch_dir), total), total)
            except Exception:
                logger.debug("Progress callback failed", exc_info=True)

    thread = threading.Thread(target=_poll, daemon=True)
    thread.start()

    def _stop():
        done.set()
        thread.join(timeout=2)

    return _stop
