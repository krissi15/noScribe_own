# Traudi - Herkunftsangaben im Transkript
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

"""Was im Kopf eines Transkripts stehen muss, damit es nachprüfbar ist.

Ein Transkript wird in der Akte zum Prüfgegenstand. Dafür muss erkennbar
sein, dass es ein ungeprüfter maschineller Entwurf ist, und es muss sich
nachweisen lassen, aus welcher Aufnahme und mit welchem Modell es entstand:

- SHA-256 der Original-Audiodatei -- belegt, dass Aufnahme und Text
  zusammengehören, auch wenn die Datei umbenannt oder verschoben wurde
  (``certutil -hashfile <datei> SHA256`` unter Windows prüft das nach),
- Modell mit Herkunft (HuggingFace-Repository),
- Zeitpunkt der Erstellung.
"""

import datetime
import hashlib
from pathlib import Path

# Bewusst ohne Import von model_download: das zieht huggingface_hub nach.
KNOWN_MODELS = {
    'precise': 'dropbox-dash/faster-whisper-large-v3-turbo',
    'fast': 'mukowaty/faster-whisper-int8',
}


def sha256_file(path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def describe_model(name: str) -> str:
    """`precise (dropbox-dash/faster-whisper-large-v3-turbo)`; eigene Modelle
    nur mit ihrem Ordnernamen."""
    name = str(name)
    repo = KNOWN_MODELS.get(name)
    return f'{name} ({repo})' if repo else name


def created_now() -> datetime.datetime:
    """Jetzt, mit Zeitzone -- im Kopf als Ortszeit, im <meta> als ISO 8601."""
    return datetime.datetime.now().astimezone().replace(microsecond=0)


def format_local(moment: datetime.datetime) -> str:
    # Mit '꞉' statt ':' -- wie die übrigen Zeitangaben im Kopf, sonst hält
    # MAXQDA "14:03" für eine Zeitmarke des Transkripts.
    return moment.strftime('%d.%m.%Y %H꞉%M')


def meta_tags(version: str, created: datetime.datetime, model: str,
              audio_sha256: str) -> dict:
    """Maschinenlesbar für das <head> des HTML-Transkripts."""
    return {
        'traudi_version': version,
        'traudi_created': created.isoformat(),
        'traudi_whisper_model': describe_model(model),
        'traudi_audio_sha256': audio_sha256,
        'traudi_origin': 'machine transcription (speech recognition), draft',
    }


def model_name_of(model) -> str:
    """Name eines Modells -- aus dem WhisperModel-Objekt, einem Pfad oder
    einem schlichten Namen."""
    name = getattr(model, 'name', None)
    return str(name) if name else Path(str(model)).name
