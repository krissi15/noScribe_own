# Traudi - Datenschutz: kein ungewollter Netzverkehr, keine liegengebliebenen Daten
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

"""Was Traudi nicht nach außen geben und nicht liegen lassen darf.

Bewusst ohne schwere Importe: `noScribe/__init__.py` ruft
:func:`disable_telemetry` auf, und das Paket wird auch von Hilfsskripten
geladen, bevor torch & Co. installiert sind.
"""

import os
import shutil
import time
from pathlib import Path

# pyannote.audio 4 schickt ohne Gegenmaßnahme bei jeder Sprechererkennung
# Sitzungskennung, Audiodauer und Sprecherzahl an otel.pyannote.ai -- die
# mitgelieferte telemetry/config.yaml steht auf `metrics_enabled: true`.
# pyannote übernimmt die Voreinstellung nur, wenn PYANNOTE_METRICS_ENABLED
# noch nicht gesetzt ist; deshalb muss das hier vor jedem pyannote-Import
# passieren. Die übrigen Schalter schließen verwandte Wege (OpenTelemetry,
# huggingface_hub) gleich mit.
TELEMETRY_OFF = {
    'PYANNOTE_METRICS_ENABLED': 'false',
    'OTEL_SDK_DISABLED': 'true',
    'HF_HUB_DISABLE_TELEMETRY': '1',
    'DO_NOT_TRACK': '1',
}


def disable_telemetry() -> None:
    """Schaltet die Telemetrie der Bibliotheken ab, auch gegen eine
    anderslautende Umgebungsvariable -- abschaltbar ist sie damit nur im Code.

    Gilt für den eigenen Prozess und alle Kindprozesse, weil die Umgebung
    beim Start eines Prozesses vererbt wird.
    """
    os.environ.update(TELEMETRY_OFF)


def go_offline() -> None:
    """Für die Arbeitsprozesse (Whisper, pyannote): ab hier wird nichts mehr
    nachgeladen. Im Hauptprozess nicht aufrufen -- der Modell-Download beim
    ersten Start braucht das Netz."""
    disable_telemetry()
    os.environ['HF_HUB_OFFLINE'] = '1'


def remove_tree(path, attempts: int = 5, delay: float = 0.5) -> bool:
    """Löscht ein Verzeichnis und versucht es kurz erneut.

    Unter Windows hält ein gerade beendeter Kindprozess die WAV-Datei oft noch
    einige hundert Millisekunden fest. `TemporaryDirectory.cleanup()` gibt
    dann sofort auf, und die Aufnahme bliebe in %TEMP% liegen.
    """
    path = Path(path)
    for attempt in range(attempts):
        if not path.exists():
            return True
        try:
            shutil.rmtree(path)
            return True
        except OSError:
            if attempt < attempts - 1:
                time.sleep(delay)
    return not path.exists()


def remove_stale(directory, pattern: str, max_age_hours: float) -> list:
    """Entfernt Dateien oder Verzeichnisse in `directory`, auf die `pattern`
    passt und die älter als `max_age_hours` sind. Gibt die entfernten Pfade
    zurück.

    Fängt ab, was ein Absturz oder ein hart beendeter Prozess liegen gelassen
    hat. Das Mindestalter schützt eine parallel laufende Traudi-Instanz.
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []
    cutoff = time.time() - max_age_hours * 3600
    removed = []
    for entry in directory.glob(pattern):
        try:
            if entry.stat().st_mtime >= cutoff:
                continue
            if entry.is_dir():
                if remove_tree(entry, attempts=1):
                    removed.append(entry)
            else:
                entry.unlink()
                removed.append(entry)
        except OSError:
            pass  # gesperrt oder schon weg -- beim nächsten Start erneut
    return removed


_TRUE = {'true', '1', 'yes', 'ja', 'on'}
_FALSE = {'false', '0', 'no', 'nein', 'off', ''}


def as_bool(value, default: bool) -> bool:
    """Liest einen Schalter aus der config.yml, ganz gleich in welcher Form.

    YAML macht aus `true` ein bool, aus `'True'` einen String; eine
    Softwareverteilung schreibt gern das eine, Traudi selbst das andere.
    Bisher stürzte `force_pyannote_cpu: true` beim Start wortlos ab
    (`bool` hat kein `.lower()`), und `auto_save: false` wurde ignoriert.
    """
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    return default
