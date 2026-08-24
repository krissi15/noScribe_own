# Traudi - Farbpalette
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

"""Die einzige Quelle aller Farben.

Zwei vollständige Sätze, hell und dunkel. Aus dieser Datei erzeugt
``scripts/make_theme.py`` die CustomTkinter-Theme-Datei ``rlp_justiz.json``;
dieselben Werte benutzen auch die Stellen, die am ThemeManager vorbeigehen
(``tk.Canvas`` der Warteschlange, Text-Markierungen, Kurzinfos).

**Anlass und Anspruch.** Die Erprobung von v0.7.3 brachte zwei Kontrastfehler
zutage: der Dateiname wurde weiß auf weiß gezeichnet (1,00:1), und der
Platzhaltertext lag bei 3,45:1. Für eine Anwendung der Justiz ist das nicht
nur unschön -- die BITV 2.0 verlangt 4,5:1. Diese Palette zielt bewusst
höher, auf **WCAG AAA (7:1)** für Fließtext, weil hier Menschen stundenlang
Transkripte gegenlesen.

**Warum das Rot dunkler wurde.** Weißer Text auf dem bisherigen Wappen-Rot
``#DD0000`` erreicht 5,15:1 -- genug für AA, zu wenig für AAA. Die
Hauptschaltfläche benutzt deshalb ``#B00000`` (7,38:1). Sie bleibt klar rot,
wirkt aber etwas satter.

**Warum Rot nie Text ist.** Auf dunklem Grund erreicht ``#DD0000`` nur
3,38:1. Statt es aufzuhellen und damit die Wappenfarbe zu verfälschen,
erscheint Rot ausschließlich als gefüllte Fläche mit hellem Text darauf.
Fehler bekommen einen roten Balken, keine rote Schrift.

``tests/test_theme.py`` prüft jede hier festgelegte Kombination nach. Wer
Farben ändert, sieht sofort, ob sie noch tragen.
"""

# Wappenfarben von Rheinland-Pfalz, unverändert als Bezugspunkt.
# Sie sind der Ursprung der Palette, aber nicht überall direkt verwendbar --
# siehe Modul-Beschreibung.
WAPPEN_ROT = '#DD0000'
WAPPEN_GOLD = '#FFCE00'

LIGHT = {
    # -- Flächen ---------------------------------------------------------
    'bg': '#F2F2F2',            # Fensterhintergrund
    'surface': '#FFFFFF',       # Karten, Eingabefelder, Protokoll
    'surface_alt': '#E4E4E4',   # Zeilen der Warteschlange, nicht gewählte Reiter
    'surface_hover': '#D6D6D6',

    # -- Schrift ---------------------------------------------------------
    'text': '#1A1A1A',          # 17,40:1 auf surface
    'text_muted': '#505050',    # 8,06:1 auf surface, 7,20:1 auf bg
    # Ausgegraute Bedienelemente sind nach WCAG 1.4.3 von der
    # Kontrastanforderung ausgenommen -- sie sollen ja als "nicht benutzbar"
    # erkennbar sein.
    'text_disabled': '#8A8A8A',

    # -- Begrenzungen (WCAG 1.4.11 verlangt 3:1) -------------------------
    'border': '#7E7E7E',        # 4,06:1 auf surface, 3,63:1 auf bg
    'border_subtle': '#D0D0D0', # nur Dekoration, trennt keine Bedienelemente

    # -- Signalfarben ----------------------------------------------------
    'primary': '#B00000',       # weisser Text darauf: 7,38:1
    'primary_hover': '#8F0000',
    'on_primary': '#FFFFFF',
    'accent': WAPPEN_GOLD,      # Fortschritt, Hervorhebung -- nie Text
    'black': '#1A1A1A',         # Kopfzeile
    'white': '#FFFFFF',

    # -- Rueckmeldungen --------------------------------------------------
    # Fehler sind eine Flaeche mit hellem Text, nie rote Schrift.
    'error_bg': '#B00000',
    'on_error': '#FFFFFF',
    'timestamp': '#505050',

    # -- Warteschlange ---------------------------------------------------
    'row_bg': '#E4E4E4',
    'row_btn': '#D0D0D0',
    'row_btn_hover': '#BEBEBE',
    'status_waiting': '#454545',   # 7,54:1 auf row_bg
    'status_running': '#6B3A00',
    'status_canceled': '#5C4600',
    'status_finished': '#0C4E0C',
    'status_error': '#8F0000',
}

DARK = {
    # -- Flächen ---------------------------------------------------------
    'bg': '#161616',
    'surface': '#232323',
    'surface_alt': '#2E2E2E',
    'surface_hover': '#3A3A3A',

    # -- Schrift ---------------------------------------------------------
    'text': '#F0F0F0',          # 13,90:1 auf surface
    'text_muted': '#B4B4B4',    # 7,58:1 auf surface, 8,73:1 auf bg
    'text_disabled': '#767676',

    # -- Begrenzungen ----------------------------------------------------
    'border': '#7A7A7A',        # 3,66:1 auf surface, 4,22:1 auf bg
    'border_subtle': '#3A3A3A',

    # -- Signalfarben ----------------------------------------------------
    # Dasselbe Rot wie im hellen Satz: als Flaeche mit weissem Text traegt es
    # unabhaengig vom Untergrund.
    'primary': '#B00000',
    'primary_hover': '#8F0000',
    'on_primary': '#FFFFFF',
    'accent': WAPPEN_GOLD,      # 11,67:1 auf bg -- die beste Lesbarkeit im Satz
    'black': '#0F0F0F',         # Kopfzeile, noch etwas tiefer als der Hintergrund
    'white': '#F0F0F0',

    # -- Rueckmeldungen --------------------------------------------------
    'error_bg': '#8F0000',
    'on_error': '#FFFFFF',
    'timestamp': '#B4B4B4',

    # -- Warteschlange ---------------------------------------------------
    'row_bg': '#2E2E2E',
    'row_btn': '#3A3A3A',
    'row_btn_hover': '#4A4A4A',
    'status_waiting': '#C2C2C2',
    'status_running': '#FFCE00',   # Gold traegt hier am besten
    'status_canceled': '#E2C05C',
    'status_finished': '#7BD97B',
    'status_error': '#FFACAC',
}

MODES = {'light': LIGHT, 'dark': DARK}

DEFAULT_MODE = 'dark'

# Welche Kombinationen tragend sind und welches Verhaeltnis sie erreichen
# muessen. tests/test_theme.py arbeitet diese Liste ab.
#
# 7,0 = WCAG AAA fuer Fliesstext.
# 3,0 = WCAG 1.4.11 fuer die Begrenzung von Bedienelementen.
CONTRACTS = [
    # (Vordergrund, Hintergrund, Mindestverhaeltnis, Beschreibung)
    ('text', 'surface', 7.0, 'Fliesstext auf Karten und im Protokoll'),
    ('text', 'bg', 7.0, 'Fliesstext auf dem Fensterhintergrund'),
    ('text', 'surface_alt', 7.0, 'Fliesstext auf abgesetzten Flaechen'),
    ('text_muted', 'surface', 7.0, 'Nebentext auf Karten'),
    ('text_muted', 'bg', 7.0, 'Nebentext auf dem Fensterhintergrund'),
    ('on_primary', 'primary', 7.0, 'Beschriftung der Hauptschaltflaeche'),
    ('on_primary', 'primary_hover', 7.0, 'Hauptschaltflaeche unter dem Zeiger'),
    ('on_error', 'error_bg', 7.0, 'Fehlermeldung auf rotem Balken'),
    ('timestamp', 'surface', 7.0, 'Zeitmarken im Transkript'),
    ('status_waiting', 'row_bg', 7.0, 'Status "wartend" in der Warteschlange'),
    ('status_running', 'row_bg', 7.0, 'Status "laeuft"'),
    ('status_canceled', 'row_bg', 7.0, 'Status "abgebrochen"'),
    ('status_finished', 'row_bg', 7.0, 'Status "abgeschlossen"'),
    ('status_error', 'row_bg', 7.0, 'Status "Fehler"'),
    ('border', 'surface', 3.0, 'Begrenzung von Eingabefeldern'),
    ('border', 'bg', 3.0, 'Begrenzung auf dem Fensterhintergrund'),
]
