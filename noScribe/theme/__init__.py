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

"""Farben des Landeswappens von Rheinland-Pfalz (Schwarz, Rot, Gold, Silber).

``rlp_justiz.json`` deckt alles ab, was CustomTkinter selbst zeichnet. Dieses
Modul liefert dieselben Werte für die Stellen, die am ThemeManager vorbeigehen:
``tk.Canvas`` (Queue-Fortschritt), Text-Tags der Textbox und die Tooltips.

In der Theme-Datei sind beide Einträge eines ``[hell, dunkel]``-Paares gleich,
damit die App unabhängig vom Appearance-Mode identisch aussieht. Sie darf keine
Kommentar-Schlüssel enthalten: der ThemeManager erwartet dort ausschließlich
Dicts.
"""

from pathlib import Path

COLORS = {
    'red': '#DD0000',           # Wappen-Rot, nur Primäraktion
    'red_hover': '#B00000',
    'gold': '#FFCE00',          # Wappen-Gold, nur als Fläche
    'black': '#1A1A1A',
    'white': '#FFFFFF',
    'bg': '#F2F2F2',
    'border': '#D8D8D8',
    'text_muted': '#5A5A5A',
    'error': '#B00000',         # dunkleres Rot: auf Weiß kontraststark
    'error_bg': '#FFE5E5',
    'timestamp': '#5A5A5A',

    # Zeilenfarben der Warteschlange. Alle >= 4.5:1 gegen den Zeilenhintergrund
    # #E1E1E1, deshalb durchweg abgedunkelt gegenüber den Signalfarben.
    'row_bg': '#E1E1E1',
    'row_btn': '#D8D8D8',
    'row_btn_hover': '#C4C4C4',
    'status_waiting': '#5A5A5A',
    'status_running': '#8A4B00',
    'status_canceled': '#7A5C00',
    'status_finished': '#146C14',
    'status_error': '#B00000',
}

def secondary_button() -> dict:
    """Stil für nachgeordnete Schaltflächen (heller Rahmen statt roter Fläche).

    Als Funktion und nicht als Konstante, damit niemand versehentlich das
    zurückgegebene Dict verändert und damit alle anderen Knöpfe mit umfärbt.
    """
    return {
        'fg_color': 'transparent',
        'hover_color': COLORS['bg'],
        'text_color': COLORS['black'],
        'border_width': 1,
        'border_color': COLORS['border'],
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
