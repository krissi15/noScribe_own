#!/usr/bin/env python3
# Traudi - Erzeugt die CustomTkinter-Theme-Datei aus der Palette
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

"""Schreibt ``noScribe/theme/rlp_justiz.json`` aus ``noScribe/theme/palette.py``.

    python scripts/make_theme.py           # Datei neu schreiben
    python scripts/make_theme.py --check   # nur pruefen, ob sie aktuell ist

CustomTkinter verlangt eine JSON-Datei mit ``[hell, dunkel]``-Paaren, die
Palette denkt dagegen in Bedeutungen (``text``, ``surface``, ``primary``).
Dieses Skript uebersetzt das eine ins andere. Beide Dateien liegen im
Repository -- die JSON, weil der Bau sie braucht, und die Palette, weil dort
die Begruendungen stehen. ``tests/test_theme.py`` prueft mit ``--check``, dass
sie nicht auseinanderlaufen.
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGET = PROJECT_ROOT / 'noScribe' / 'theme' / 'rlp_justiz.json'


def _load_palette():
    """Die Palette ueber ihren Pfad laden, nicht ueber das Paket.

    ``noScribe/__init__.py`` importiert ``main`` und damit tkinter, torch und
    faster-whisper. Dieses Skript braucht nichts davon und soll auch auf einem
    Rechner ohne GUI laufen.
    """
    path = PROJECT_ROOT / 'noScribe' / 'theme' / 'palette.py'
    spec = importlib.util.spec_from_file_location('_traudi_palette', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_palette = _load_palette()
LIGHT, DARK = _palette.LIGHT, _palette.DARK

# Grundschriftgroesse. 13 war fuer laengeres Gegenlesen knapp; 14 ist der
# groesste Schritt, der die Anordnung noch nicht sprengt.
FONT_SIZE = 14

# Welcher Bedeutungsschluessel welche CustomTkinter-Eigenschaft speist.
#
# Wichtig bei zusammengesetzten Bedienelementen: bei CTkCheckBox,
# CTkRadioButton und CTkSwitch ist `fg_color` die Fuellung des Kaestchens,
# NICHT der Hintergrund der Beschriftung -- die sitzt auf der Flaeche des
# Elternelements. Deshalb darf `text_color` dort nicht gegen `fg_color`
# geprueft werden.
WIDGETS = {
    'CTk': {'fg_color': 'bg'},
    'CTkToplevel': {'fg_color': 'bg'},
    'CTkFrame': {
        'corner_radius': 6, 'border_width': 0,
        'fg_color': 'surface', 'top_fg_color': 'surface',
        'border_color': 'border_subtle',
    },
    'CTkButton': {
        'corner_radius': 6, 'border_width': 0,
        'fg_color': 'primary', 'hover_color': 'primary_hover',
        'border_color': 'border', 'text_color': 'on_primary',
        'text_color_disabled': 'text_disabled',
    },
    'CTkLabel': {
        'corner_radius': 0, 'border_width': 0, 'fg_color': 'transparent',
        'border_color': 'border_subtle', 'text_color': 'text',
    },
    'CTkEntry': {
        'corner_radius': 6, 'border_width': 1,
        'fg_color': 'surface', 'border_color': 'border',
        'text_color': 'text',
        # Vorher #8A8A8A auf Weiss = 3,45:1 und damit unter dem gesetzlichen
        # Minimum. Platzhalter sind Text und muessen lesbar sein.
        'placeholder_text_color': 'text_muted',
    },
    'CTkCheckBox': {
        'corner_radius': 4, 'border_width': 2,
        'fg_color': 'primary', 'border_color': 'border',
        'hover_color': 'primary_hover', 'checkmark_color': 'on_primary',
        'text_color': 'text', 'text_color_disabled': 'text_disabled',
    },
    'CTkSwitch': {
        'corner_radius': 1000, 'border_width': 3, 'button_length': 0,
        'fg_color': 'surface_hover', 'progress_color': 'primary',
        'button_color': 'surface', 'button_hover_color': 'bg',
        'text_color': 'text', 'text_color_disabled': 'text_disabled',
    },
    'CTkRadioButton': {
        'corner_radius': 1000,
        'border_width_checked': 6, 'border_width_unchecked': 2,
        'fg_color': 'primary', 'border_color': 'border',
        'hover_color': 'primary_hover',
        'text_color': 'text', 'text_color_disabled': 'text_disabled',
    },
    'CTkProgressBar': {
        'corner_radius': 1000, 'border_width': 0,
        'fg_color': 'surface_alt', 'progress_color': 'accent',
        'border_color': 'border_subtle',
    },
    'CTkSlider': {
        'corner_radius': 1000, 'button_corner_radius': 1000,
        'border_width': 6, 'button_length': 0,
        'fg_color': 'surface_alt', 'progress_color': 'text_muted',
        'button_color': 'primary', 'button_hover_color': 'primary_hover',
    },
    'CTkOptionMenu': {
        'corner_radius': 6,
        'fg_color': 'surface', 'button_color': 'surface_alt',
        'button_hover_color': 'surface_hover',
        'text_color': 'text', 'text_color_disabled': 'text_disabled',
    },
    'CTkComboBox': {
        'corner_radius': 6, 'border_width': 1,
        'fg_color': 'surface', 'border_color': 'border',
        'button_color': 'surface_alt', 'button_hover_color': 'surface_hover',
        'text_color': 'text', 'text_color_disabled': 'text_disabled',
    },
    'CTkScrollbar': {
        'corner_radius': 1000, 'border_spacing': 4, 'fg_color': 'transparent',
        'button_color': 'border', 'button_hover_color': 'text_muted',
    },
    'CTkSegmentedButton': {
        'corner_radius': 6, 'border_width': 2,
        'fg_color': 'surface_alt',
        # Bewusst NICHT die Signalfarbe: eine einzige `text_color` muss auf
        # gewaehlten wie ungewaehlten Reitern lesbar sein. Rot als Flaeche
        # wuerde dunklen Text verschlucken.
        'selected_color': 'surface', 'selected_hover_color': 'surface',
        'unselected_color': 'surface_alt', 'unselected_hover_color': 'surface_hover',
        'text_color': 'text', 'text_color_disabled': 'text_disabled',
    },
    'CTkTextbox': {
        'corner_radius': 6, 'border_width': 0,
        'fg_color': 'surface', 'border_color': 'border_subtle',
        'text_color': 'text',
        'scrollbar_button_color': 'border',
        'scrollbar_button_hover_color': 'text_muted',
    },
    'CTkScrollableFrame': {'label_fg_color': 'surface_alt'},
    'DropdownMenu': {
        'fg_color': 'surface', 'hover_color': 'surface_hover',
        'text_color': 'text',
    },
}

FONTS = {
    'CTkFont': {
        'macOS': {'family': 'SF Display', 'size': FONT_SIZE, 'weight': 'normal'},
        'Windows': {'family': 'Segoe UI', 'size': FONT_SIZE, 'weight': 'normal'},
        'Linux': {'family': 'Roboto', 'size': FONT_SIZE, 'weight': 'normal'},
    },
}


def build() -> dict:
    theme = {}
    for widget, properties in WIDGETS.items():
        entry = {}
        for key, value in properties.items():
            if isinstance(value, int):
                entry[key] = value
            elif value == 'transparent':
                entry[key] = 'transparent'
            else:
                entry[key] = [LIGHT[value], DARK[value]]
        theme[widget] = entry
    theme.update(FONTS)
    return theme


def render() -> str:
    return json.dumps(build(), indent=2, ensure_ascii=False) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true',
                        help='nur pruefen, nichts schreiben')
    args = parser.parse_args()

    expected = render()
    if args.check:
        actual = TARGET.read_text(encoding='utf-8') if TARGET.is_file() else ''
        if actual != expected:
            print(f'{TARGET} ist nicht aktuell. Neu erzeugen mit:\n'
                  f'    python scripts/make_theme.py', file=sys.stderr)
            return 1
        print(f'{TARGET.name} ist aktuell.')
        return 0

    TARGET.write_text(expected, encoding='utf-8')
    print(f'Geschrieben: {TARGET}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
