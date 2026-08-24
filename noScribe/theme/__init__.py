# Traudi - Farbsystem
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

"""Farben für die Stellen, die am CustomTkinter-ThemeManager vorbeigehen.

``rlp_justiz.json`` deckt ab, was das Framework selbst zeichnet. Dieses Modul
liefert dieselben Werte für ``tk.Canvas`` (Fortschritt in der Warteschlange),
die Text-Markierungen der Protokoll-Textbox und die Kurzinfos.

Beide Quellen stammen aus ``palette.py``; die JSON wird daraus von
``scripts/make_theme.py`` erzeugt. Farben gehören deshalb weder hierher noch
nach ``main.py``, sondern ausschließlich in die Palette.

``COLORS`` wird beim Programmstart über :func:`apply_mode` gefüllt. Das Dict
wird dabei **an Ort und Stelle** verändert, damit ein früheres
``from .theme import COLORS`` gültig bleibt.
"""

from pathlib import Path

from .palette import DARK, DEFAULT_MODE, LIGHT, MODES

# Alte Namen, die main.py seit jeher benutzt, auf die Bedeutungen der Palette
# abgebildet. So musste nicht der halbe Quelltext angefasst werden.
#
# `error` ist bewusst `on_error`: Fehler erscheinen als heller Text auf rotem
# Balken, nie als rote Schrift. Auf dunklem Grund erreicht das Wappen-Rot nur
# 3,38:1 und wäre als Schriftfarbe unzulässig.
ALIASES = {
    'red': 'primary',
    'red_hover': 'primary_hover',
    'gold': 'accent',
    'error': 'on_error',
}

COLORS: dict = {}

_current_mode = None


def apply_mode(mode: str) -> str:
    """Füllt ``COLORS`` mit dem gewählten Satz und gibt ihn zurück.

    Unbekannte Werte fallen auf die Vorgabe zurück, statt die Anwendung beim
    Start an einer verschriebenen Konfigurationszeile scheitern zu lassen.
    """
    global _current_mode
    if mode not in MODES:
        mode = DEFAULT_MODE
    COLORS.clear()
    COLORS.update(MODES[mode])
    for alias, key in ALIASES.items():
        COLORS[alias] = MODES[mode][key]
    _current_mode = mode
    return mode


def current_mode() -> str:
    return _current_mode or DEFAULT_MODE


# Bis apply_mode() gerufen wird, gilt die Vorgabe. Ohne das wäre COLORS beim
# Import leer und jeder Zugriff ein KeyError.
apply_mode(DEFAULT_MODE)


def secondary_button() -> dict:
    """Stil für nachgeordnete Schaltflächen: Rahmen statt gefüllter Fläche.

    Als Funktion und nicht als Konstante, damit niemand versehentlich das
    zurückgegebene Dict verändert und damit alle anderen Knöpfe mit umfärbt --
    und damit der Stil nach einem Moduswechsel neu erfragt werden kann.
    """
    return {
        'fg_color': 'transparent',
        'hover_color': COLORS['surface_hover'],
        'text_color': COLORS['text'],
        'border_width': 1,
        'border_color': COLORS['border'],
    }


def danger_button() -> dict:
    """Stil für zerstörende Aktionen: gefüllte rote Fläche, heller Text.

    Vorher war das ein Rahmenknopf mit **roter Schrift**. Auf dunklem Grund
    wäre die nicht mehr lesbar gewesen, deshalb trägt jetzt die Fläche die
    Signalwirkung.
    """
    return {
        'fg_color': COLORS['primary'],
        'hover_color': COLORS['primary_hover'],
        'text_color': COLORS['on_primary'],
        'border_width': 0,
    }


THEME_FILE = 'rlp_justiz.json'


def theme_path() -> str:
    """Absoluter Pfad zur CustomTkinter-Theme-Datei.

    Bewusst über ``__file__`` statt ``importlib.resources``: im
    PyInstaller-Bundle liegt der Modulcode im Archiv, ``__file__`` zeigt aber
    auf ``_MEIPASS/noScribe/theme/`` -- genau dorthin kopiert die .spec die
    JSON-Datei.
    """
    return str(Path(__file__).parent / THEME_FILE)
