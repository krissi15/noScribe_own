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

**Anlass.** Die Erprobung von v0.7.3 brachte zwei Kontrastfehler zutage: der
Dateiname wurde weiß auf weiß gezeichnet (1,00:1), und der Platzhaltertext lag
bei 3,45:1. Für eine Anwendung der Justiz ist das nicht nur unschön -- die
BITV 2.0 verlangt 4,5:1. Die zweite Erprobung bestätigte den Kontrast,
bemängelte aber die Anmutung: die Grautöne wirkten „trist", Rot und Gold
störten.

**Anspruch: WCAG AAA (7:1)** für Fließtext, mit **einer** begründeten
Ausnahme (siehe ``AA_EXCEPTIONS``). 3:1 für Begrenzungen und Fortschritt nach
WCAG 1.4.11.

**Warum die Grautöne einen Blaustich haben.** Vollkommen neutrale Grauwerte
wirken tot. Ein paar Prozent Blau im Farbton ändern die Helligkeit kaum,
lassen dieselbe Fläche aber wertiger erscheinen. Das ist der ganze Unterschied
zwischen ``#232323`` und ``#1E2127``.

**Warum Rot nie Text ist.** Auf dunklem Grund erreicht das Wappen-Rot nur
3,38:1. Statt es aufzuhellen und damit die Wappenfarbe zu verfälschen,
erscheint Rot ausschließlich als gefüllte Fläche mit hellem Text darauf.
Fehler bekommen einen roten Balken, keine rote Schrift.

**Warum der Fortschritt je Modus eine andere Farbe hat.** Das Wappen-Gold
trägt auf dunklem Grund hervorragend (9,4:1), auf hellem aber überhaupt nicht
-- gegen eine helle Bahn kommt es auf **1,18:1** und wäre praktisch unsichtbar.
Ein Fortschrittsbalken, den man nicht sieht, ist keiner. Der helle Satz nimmt
deshalb ein dunkles Ocker, das dieselbe Herkunft hat und sich abhebt.

``tests/test_theme.py`` prüft jede hier festgelegte Kombination nach. Wer
Farben ändert, sieht sofort, ob sie noch tragen.
"""

# Wappenfarben von Rheinland-Pfalz als Bezugspunkt. Sie sind der Ursprung der
# Palette, aber nicht überall direkt verwendbar -- siehe Modulbeschreibung.
WAPPEN_ROT = '#DD0000'
WAPPEN_GOLD = '#FFCE00'

LIGHT = {
    # -- Flächen ---------------------------------------------------------
    # Leichter Blaustich statt neutraler Grauwerte.
    'bg': '#EFF1F5',            # Fensterhintergrund
    'surface': '#FFFFFF',       # Karten, Eingabefelder, Protokoll
    'surface_alt': '#E2E5EC',   # Warteschlangen-Zeilen, ungewählte Reiter
    'surface_hover': '#D2D6E0',

    # -- Schrift ---------------------------------------------------------
    'text': '#171A21',          # 17,41:1 auf surface
    'text_muted': '#3F4550',    # 9,64 auf surface, 8,52 auf bg, 7,64 auf alt
    # Ausgegraute Bedienelemente sind nach WCAG 1.4.3 von der
    # Kontrastanforderung ausgenommen -- sie sollen ja als "nicht benutzbar"
    # erkennbar sein.
    'text_disabled': '#8A909C',

    # -- Begrenzungen (WCAG 1.4.11 verlangt 3:1) -------------------------
    'border': '#7B8291',        # 3,86 auf surface, 3,41 auf bg
    'border_subtle': '#CFD3DC', # nur Dekoration, trennt keine Bedienelemente

    # -- Signalfarben ----------------------------------------------------
    # Das echte Wappen-Rot, siehe AA_EXCEPTIONS.
    'primary': WAPPEN_ROT,      # weisser Text darauf: 5,15:1
    'primary_hover': '#C00000',
    'on_primary': '#FFFFFF',
    'accent': '#96700F',        # Fortschritt: dunkles Ocker, 3,60:1 auf der Bahn
    'black': '#171A21',         # Kopfzeile
    'white': '#FFFFFF',

    # -- Rueckmeldungen --------------------------------------------------
    # Fehler sind eine Flaeche mit hellem Text, nie rote Schrift.
    'error_bg': '#B00000',
    'on_error': '#FFFFFF',
    'timestamp': '#3F4550',

    # -- Warteschlange ---------------------------------------------------
    'row_bg': '#E2E5EC',
    'row_btn': '#CFD3DC',
    'row_btn_hover': '#BCC1CD',
    'status_waiting': '#3F4550',   # 7,64:1 auf row_bg
    'status_running': '#5F3A00',   # 7,96:1
    'status_canceled': '#4F4000',  # 8,06:1
    'status_finished': '#0B5218',  # 7,45:1
    'status_error': '#8F0000',     # 7,68:1

    # -- Editor ----------------------------------------------------------
    # Die mitlaufende Zeilenmarkierung und die Suchtreffer muessen zweierlei
    # leisten: Text auf ihnen bleibt lesbar (7:1), und sie sind voneinander
    # unterscheidbar. Blau heisst "hier laeuft die Aufnahme", Gelb heisst
    # "hier steht das Gesuchte" -- das entspricht der Erwartung.
    'playback_line': '#CFE0F7',      # Text darauf: 12,98:1
    'playback_line_text': '#171A21',
    'search_hit': '#F5E39B',         # Text darauf: 13,55:1
    'search_hit_text': '#171A21',
}

DARK = {
    # -- Flächen ---------------------------------------------------------
    'bg': '#14161A',
    'surface': '#1E2127',
    'surface_alt': '#282C34',
    'surface_hover': '#333844',

    # -- Schrift ---------------------------------------------------------
    'text': '#E8EAF0',          # 13,41 auf surface, 11,64 auf alt
    'text_muted': '#B6BDCA',    # 8,54 auf surface, 9,59 auf bg, 7,41 auf alt
    'text_disabled': '#6E7686',

    # -- Begrenzungen ----------------------------------------------------
    'border': '#7A8194',        # 4,14 auf surface, 4,65 auf bg
    'border_subtle': '#333844',

    # -- Signalfarben ----------------------------------------------------
    # Dasselbe Rot wie im hellen Satz: als Flaeche mit weissem Text traegt es
    # unabhaengig vom Untergrund.
    'primary': WAPPEN_ROT,
    'primary_hover': '#C00000',
    'on_primary': '#FFFFFF',
    'accent': '#E8B93A',        # ruhiger als das reine Wappen-Gold, 7,62:1
    'black': '#0E1013',         # Kopfzeile, noch etwas tiefer als der Grund
    'white': '#E8EAF0',

    # -- Rueckmeldungen --------------------------------------------------
    'error_bg': '#8F0000',
    'on_error': '#FFFFFF',
    'timestamp': '#B6BDCA',

    # -- Warteschlange ---------------------------------------------------
    'row_bg': '#282C34',
    'row_btn': '#333844',
    'row_btn_hover': '#414857',
    'status_waiting': '#B6BDCA',   # 7,41:1 auf row_bg
    'status_running': '#E8B93A',   # 7,62:1
    'status_canceled': '#D9C07A',  # 7,85:1
    'status_finished': '#86D98F',  # 8,22:1
    'status_error': '#FFB0B0',     # 8,06:1

    # -- Editor ----------------------------------------------------------
    'playback_line': '#24405F',      # Text darauf: 8,85:1
    'playback_line_text': '#E8EAF0',
    'search_hit': '#5A4A12',         # Text darauf: 7,21:1
    'search_hit_text': '#E8EAF0',
}

MODES = {'light': LIGHT, 'dark': DARK}

DEFAULT_MODE = 'dark'

# Welche Kombinationen tragend sind und welches Verhaeltnis sie erreichen
# muessen. tests/test_theme.py arbeitet diese Liste ab.
#
# 7,0 = WCAG AAA fuer Fliesstext.
# 3,0 = WCAG 1.4.11 fuer Begrenzungen und Fortschrittsanzeigen.
CONTRACTS = [
    # (Vordergrund, Hintergrund, Mindestverhaeltnis, Beschreibung)
    ('text', 'surface', 7.0, 'Fliesstext auf Karten und im Protokoll'),
    ('text', 'bg', 7.0, 'Fliesstext auf dem Fensterhintergrund'),
    ('text', 'surface_alt', 7.0, 'Fliesstext auf abgesetzten Flaechen'),
    ('text_muted', 'surface', 7.0, 'Nebentext auf Karten'),
    ('text_muted', 'bg', 7.0, 'Nebentext auf dem Fensterhintergrund'),
    ('text_muted', 'surface_alt', 7.0, 'Nebentext auf abgesetzten Flaechen'),
    ('on_error', 'error_bg', 7.0, 'Fehlermeldung auf rotem Balken'),
    ('timestamp', 'surface', 7.0, 'Zeitmarken im Transkript'),
    ('status_waiting', 'row_bg', 7.0, 'Status "wartend" in der Warteschlange'),
    ('status_running', 'row_bg', 7.0, 'Status "laeuft"'),
    ('status_canceled', 'row_bg', 7.0, 'Status "abgebrochen"'),
    ('status_finished', 'row_bg', 7.0, 'Status "abgeschlossen"'),
    ('status_error', 'row_bg', 7.0, 'Status "Fehler"'),
    ('text', 'row_btn', 7.0, 'Beschriftung der Knoepfe in einer Zeile'),
    ('border', 'surface', 3.0, 'Begrenzung von Eingabefeldern'),
    ('border', 'bg', 3.0, 'Begrenzung auf dem Fensterhintergrund'),
    ('accent', 'surface_alt', 3.0, 'Fortschrittsbalken gegen seine Bahn'),
    ('playback_line_text', 'playback_line', 7.0,
     'Editor: Text der gerade gesprochenen Zeile'),
    ('search_hit_text', 'search_hit', 7.0, 'Editor: Text eines Suchtreffers'),
]

# Die einzige Stelle, an der AAA bewusst unterschritten wird.
#
# Fuer AAA muesste weisser Text auf Rot 7:1 erreichen, was das Rot auf
# #B00000 zwingt -- und damit deutlich schwerer und dunkler wirken laesst als
# das Wappen. Bei einer grossen, gefuellten Schaltflaeche ist das ein
# schlechter Tausch: die gesetzliche Anforderung der BITV 2.0 liegt bei
# 4,5:1, und die wird mit 5,15:1 uebertroffen.
#
# Ausdruecklich als Ausnahme gefuehrt, damit sie nicht stillschweigend zur
# Regel wird. Wer eine weitere eintraegt, muss sie hier begruenden.
AA_EXCEPTIONS = [
    ('on_primary', 'primary', 4.5,
     'Hauptschaltflaeche: das echte Wappen-Rot hat Vorrang vor AAA'),
    ('on_primary', 'primary_hover', 4.5,
     'Hauptschaltflaeche unter dem Zeiger'),
]
