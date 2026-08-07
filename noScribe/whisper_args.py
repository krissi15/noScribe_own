# Traudi - Parameter für die Transkription
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

"""Wie aus Auftrag und Konfiguration die Whisper-Parameter werden.

Bewusst ein eigenes Modul ohne torch, faster-whisper oder Tk: nur so lassen
sich diese Entscheidungen testen, ohne ein 1,6-GB-Modell zu laden. Es ist
zugleich die Stelle, an der frühere Abweichungen zwischen Eltern- und
Kindprozess zusammenlaufen -- die Vorgabewerte stehen jetzt nur noch hier.
"""

import logging
from pathlib import Path
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

# Whispers Kontextfenster für den Prompt umfasst 224 Token. Was darüber
# hinausgeht, verwirft das Modell stillschweigend -- eine lange Wortliste wäre
# also wirkungslos, ohne dass es jemand merkt. Für Deutsch sind rund drei
# Zeichen je Token eine brauchbare Näherung; der Sicherheitsabstand nach unten
# ist Absicht.
MAX_PROMPT_CHARS = 600

# Werte, die "entscheide selbst" bedeuten. 'default' steht in bestehenden
# Konfigurationsdateien und hieß bisher faktisch float32 auf der CPU; es wird
# deshalb mitgemeint. Wer ausdrücklich float32 will, trägt float32 ein.
AUTO_COMPUTE_TYPES = frozenset({'', 'auto', 'default', 'none', None})


def resolve_compute_type(configured: Optional[str], device: str) -> str:
    """Rechengenauigkeit für faster-whisper.

    Auf der CPU ist int8 zwei- bis dreifach schneller als float32, bei einem
    Qualitätsunterschied, der für Sprachaufnahmen nicht ins Gewicht fällt.
    Bisher stand hier 'default', was auf der CPU float32 bedeutete -- die
    Voreinstellung war also die langsamste Möglichkeit.
    """
    value = (configured or '').strip().lower()
    if value not in AUTO_COMPUTE_TYPES:
        return value
    return 'int8' if device == 'cpu' else 'float16'


def load_vocabulary_file(path) -> list:
    """Liest eine Wortliste: ein Begriff je Zeile, '#' leitet einen Kommentar ein.

    Reiner Text und nicht YAML, damit die Liste per Softwareverteilung
    ausgerollt, zwischen Kolleginnen und Kollegen weitergegeben und in einer
    Versionsverwaltung vernünftig verglichen werden kann.
    """
    path = Path(path)
    if not path.is_file():
        return []
    terms = []
    try:
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.split('#', 1)[0].strip()
            if line:
                terms.append(line)
    except OSError:
        logger.warning('Wortliste %s ließ sich nicht lesen', path, exc_info=True)
    return terms


def build_prompt(style_example: str, terms: Iterable[str],
                 max_chars: int = MAX_PROMPT_CHARS) -> str:
    """Setzt Füllwort-Beispiel und Fachbegriffe zu einem Prompt zusammen.

    Beides geht bewusst in **einen** `initial_prompt` statt teils dorthin und
    teils nach `hotwords`: faster-whisper baut aus beiden denselben
    Kontext-Token-Strom, und welcher von beiden bei gleichzeitiger Angabe
    gewinnt, hängt von der Fassung ab. Ein Kanal ist vorhersagbar.

    Gekürzt wird von hinten und an Begriffsgrenzen -- ein halb abgeschnittenes
    Wort würde das Modell in die falsche Richtung schieben. Das Füllwort-
    Beispiel hat Vorrang, weil es die Ausgabeform steuert.
    """
    style_example = (style_example or '').strip()
    prompt = style_example
    remaining = max_chars - len(prompt)

    seen = set()
    accepted = []
    for term in terms:
        term = str(term).strip().rstrip(',')
        key = term.casefold()
        if not term or key in seen:
            continue
        # +2 für ', ' vor dem Begriff.
        cost = len(term) + (2 if accepted or prompt else 0)
        if cost > remaining:
            break
        seen.add(key)
        accepted.append(term)
        remaining -= cost

    if accepted:
        joined = ', '.join(accepted)
        prompt = f'{prompt} {joined}' if prompt else joined

    return prompt.strip()


def build_transcribe_options(job, *, device: str, number_threads: int,
                             language_code: Optional[str],
                             vad_threshold: float,
                             vocabulary: Iterable[str],
                             condition_on_previous_text: bool,
                             locale: str) -> dict:
    """Der vollständige Parametersatz für den Kindprozess.

    Alle Vorgabewerte stehen hier. Der Kindprozess füllt nichts mehr selbst
    auf -- genau daher kam die frühere Abweichung, dass die Konfiguration
    beam_size 1 vorgab, ins Protokoll auch 1 geschrieben wurde, das Modell
    aber mit 5 lief.

    Die `compute_type`-Auflösung bleibt bewusst dem Kind überlassen, wenn hier
    'auto' als Gerät steht: erst dort ist bekannt, ob eine brauchbare
    Grafikkarte vorhanden ist. Ebenso der endgültige Prompt -- bei der
    Spracheinstellung "Auto" steht die Sprache erst nach der Erkennung fest,
    und das Füllwort-Beispiel gibt es je Sprache.
    """
    return {
        'whisper_model': job.whisper_model,
        'device': device,
        'compute_type': resolve_compute_type(job.whisper_compute_type, device),
        # Der unaufgelöste Wert, damit das Kind bei device='auto' selbst
        # entscheiden kann, sobald die Hardware feststeht.
        'compute_type_configured': job.whisper_compute_type,
        'cpu_threads': number_threads,
        'local_files_only': True,
        'language_name': job.language_name,
        'language_code': language_code,
        'disfluencies': job.disfluencies,
        'beam_size': int(job.whisper_beam_size),
        'word_timestamps': True,
        'vad_filter': True,
        'vad_threshold': vad_threshold,
        # Ohne diese Bremse verfängt sich Whisper bei langen Aufnahmen in
        # Wiederholungsschleifen -- die Einschränkung, die das README bisher
        # nur beschrieben hat.
        'condition_on_previous_text': condition_on_previous_text,
        'vocabulary': list(vocabulary),
        'locale': locale,
    }
