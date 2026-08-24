# Traudi Editor - Farben und Qt-Stylesheet
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

"""Uebersetzt die Traudi-Palette in ein Qt-Stylesheet.

Die Farben stammen aus ``traudi_colors.json``. Diese Datei wird von
``scripts/make_theme.py`` aus ``noScribe/theme/palette.py`` erzeugt -- wer die
Palette aendert, aendert damit auch den Editor. Von Hand gepflegt wird hier
nur die Uebersetzung nach Qt, nicht die Farbe selbst.

Warum ueber eine Datei und nicht per Import: der Editor wird als eigenes
Programm gebaut. Ein ``from noScribe.theme.palette import ...`` zoege das
gesamte Hauptpaket samt torch in sein Buendel -- mehrere Gigabyte fuer eine
Handvoll Farbwerte.

Der Editor hatte zuvor ueberhaupt keine Farbwahl: Text war fest ``#000000``
auf fest ``#ffffff``. Wer Traudi im Dunkelmodus benutzte, bekam beim Oeffnen
des Transkripts ein grelles weisses Fenster.
"""

import json
import os
import re

_HERE = os.path.abspath(os.path.dirname(__file__))
_COLORS_FILE = os.path.join(_HERE, 'traudi_colors.json')

# Notnagel, falls die erzeugte Datei im Buendel fehlt. Bewusst der dunkle
# Satz: er ist die Vorgabe, und ein Editor in falschen Farben ist immer noch
# besser als einer, der nicht startet.
_FALLBACK = {
    'bg': '#14161A', 'surface': '#1E2127', 'surface_alt': '#282C34',
    'surface_hover': '#333844', 'text': '#E8EAF0', 'text_muted': '#B6BDCA',
    'text_disabled': '#6E7686', 'border': '#7A8194', 'border_subtle': '#333844',
    'primary': '#DD0000', 'primary_hover': '#C00000', 'on_primary': '#FFFFFF',
    'accent': '#E8B93A', 'black': '#0E1013', 'white': '#E8EAF0',
    'error_bg': '#8F0000', 'on_error': '#FFFFFF', 'timestamp': '#B6BDCA',
    'playback_line': '#24405F', 'playback_line_text': '#E8EAF0',
    'search_hit': '#5A4A12', 'search_hit_text': '#E8EAF0',
}


def _load():
    try:
        with open(_COLORS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'default_mode': 'dark', 'light': _FALLBACK, 'dark': _FALLBACK}


_DATA = _load()

MODES = ('light', 'dark')
DEFAULT_MODE = _DATA.get('default_mode', 'dark')


def colors_for(mode):
    """Der Farbsatz eines Modus. Unbekannte Namen fallen auf die Vorgabe."""
    if mode not in MODES:
        mode = DEFAULT_MODE
    return dict(_DATA.get(mode) or _FALLBACK)


def stylesheet(c):
    """Das Qt-Stylesheet zu einem Farbsatz.

    Bewusst vollstaendig statt nur ergaenzend: Qt mischt sonst die Farben des
    Betriebssystem-Themes hinein, und dann steht dunkler Text auf dunklem
    Grund, sobald jemand Windows auf Dunkel gestellt hat.
    """
    return f"""
    QWidget {{ background-color: {c['bg']}; color: {c['text']}; }}
    QMainWindow {{ background-color: {c['bg']}; }}

    QTextEdit {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 0px;
        selection-background-color: {c['primary']};
        selection-color: {c['on_primary']};
    }}

    QToolBar {{
        background-color: {c['bg']};
        border: 0px;
        spacing: 2px;
        padding: 2px;
    }}
    QToolBar::separator {{ background: {c['border_subtle']}; width: 1px; margin: 4px 6px; }}
    QToolButton {{ background: transparent; border: 0px; padding: 4px; border-radius: 4px; }}
    QToolButton:hover {{ background-color: {c['surface_hover']}; }}
    QToolButton:checked {{ background-color: {c['surface_alt']}; }}

    QMenuBar {{ background-color: {c['bg']}; color: {c['text']}; }}
    QMenuBar::item {{ background: transparent; padding: 4px 8px; }}
    QMenuBar::item:selected {{ background-color: {c['surface_hover']}; }}

    QMenu {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border_subtle']};
    }}
    QMenu::item:selected {{ background-color: {c['surface_hover']}; }}
    QMenu::item:disabled {{ color: {c['text_disabled']}; }}
    QMenu::separator {{ height: 1px; background: {c['border_subtle']}; margin: 4px 8px; }}

    QStatusBar {{ background-color: {c['bg']}; color: {c['text_muted']}; border: 0px; }}
    QStatusBar::item {{ border: 0px; }}

    QComboBox {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 2px 6px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['surface']};
        color: {c['text']};
        selection-background-color: {c['surface_hover']};
        selection-color: {c['text']};
        border: 1px solid {c['border_subtle']};
    }}

    QLineEdit {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 3px 6px;
    }}

    QPushButton {{
        background-color: {c['surface_alt']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 5px 12px;
    }}
    QPushButton:hover {{ background-color: {c['surface_hover']}; }}
    QPushButton:default {{
        background-color: {c['primary']};
        color: {c['on_primary']};
        border: 0px;
    }}
    QPushButton:default:hover {{ background-color: {c['primary_hover']}; }}

    QCheckBox {{ color: {c['text']}; }}
    QLabel {{ background: transparent; color: {c['text']}; }}

    QScrollBar:vertical {{ background: {c['bg']}; width: 12px; margin: 0px; }}
    QScrollBar::handle:vertical {{
        background: {c['border']};
        border-radius: 6px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {c['text_muted']}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0px; width: 0px; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

    QDialog {{ background-color: {c['bg']}; }}
    QMessageBox {{ background-color: {c['bg']}; }}
    """


# Die Zeitmarke steht als feste Farbe IM Transkript -- noScribe schreibt sie
# beim Speichern hinein (main.py, `job.timestamp_color`). Ein im Dunkelmodus
# erzeugtes Transkript brachte im hellen Editor also hellgraue Zeitmarken auf
# Weiss mit, rund 2:1. Deshalb wird die Farbe beim Laden auf den aktuellen
# Modus gezogen.
#
# Eng gefasst: nur ein `<span style="color: #xxxxxx">`, dessen Inhalt wie eine
# Zeitmarke aussieht. Eigene Hervorhebungen im Text bleiben unangetastet.
_TIMESTAMP_SPAN = re.compile(
    r'(<span\s+style\s*=\s*"[^"]*color\s*:\s*)(#[0-9A-Fa-f]{3,8})([^"]*"\s*>)'
    r'(\s*\[[\d:\.,\s\u2013\u2014-]+\]\s*)(</span>)')


def recolor_timestamps(html_str, color):
    """Faerbt die eingebetteten Zeitmarken auf `color` um. Gibt HTML zurueck."""
    return _TIMESTAMP_SPAN.sub(
        lambda m: m.group(1) + color + m.group(3) + m.group(4) + m.group(5),
        html_str)
