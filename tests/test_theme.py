"""Die Farben müssen lesbar sein, und zwar nachweislich.

Anlass: In v0.7.3 wurde der Dateiname weiß auf weißem Feld gezeichnet —
Kontrast 1,00:1. Niemand hat es bemerkt, weil nichts es geprüft hat. Genau das
holen diese Tests nach.

Maßstab ist WCAG AAA (7:1) für Fließtext und WCAG 1.4.11 (3:1) für die
Begrenzung von Bedienelementen. Die BITV 2.0, die für öffentliche Stellen
gilt, verlangt mit 4,5:1 weniger — hier wird bewusst schärfer geprüft, weil
mit dieser Anwendung stundenlang Transkripte gegengelesen werden.
"""

import json
import re

import pytest

from conftest import load_module


def contrast(fg: str, bg: str) -> float:
    """Kontrastverhältnis nach WCAG 2.1, Abschnitt 1.4.3."""
    def relative_luminance(colour: str) -> float:
        colour = colour.lstrip('#')
        channels = (int(colour[i:i + 2], 16) / 255 for i in (0, 2, 4))
        linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                  for c in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted((relative_luminance(fg), relative_luminance(bg)),
                             reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


@pytest.fixture(scope='module')
def palette():
    return load_module('noScribe/theme/palette.py')


# -- Die Rechenvorschrift selbst ----------------------------------------

def test_contrast_formula_matches_known_values():
    """Ohne diese Probe könnte die Formel falsch sein und alles andere mit."""
    assert contrast('#000000', '#FFFFFF') == pytest.approx(21.0, abs=0.01)
    assert contrast('#FFFFFF', '#FFFFFF') == pytest.approx(1.0, abs=0.01)
    # Symmetrisch: die Reihenfolge darf nichts ändern.
    assert contrast('#1A1A1A', '#FFFFFF') == pytest.approx(
        contrast('#FFFFFF', '#1A1A1A'), abs=0.001)


# -- Die Zusagen der Palette --------------------------------------------

def test_every_contract_holds_in_both_modes(palette):
    failures = []
    for mode_name, colours in palette.MODES.items():
        for fg_key, bg_key, minimum, description in palette.CONTRACTS:
            actual = contrast(colours[fg_key], colours[bg_key])
            if actual < minimum:
                failures.append(
                    f'{mode_name}: {description} — {fg_key} auf {bg_key} '
                    f'({colours[fg_key]} auf {colours[bg_key]}) erreicht nur '
                    f'{actual:.2f}:1, verlangt sind {minimum}:1')
    assert not failures, '\n' + '\n'.join(failures)


def test_both_modes_define_the_same_keys(palette):
    """Ein Schlüssel, den nur ein Modus kennt, führt im anderen zum Absturz."""
    assert set(palette.LIGHT) == set(palette.DARK)


def test_every_colour_is_a_hex_triplet(palette):
    for mode_name, colours in palette.MODES.items():
        for key, value in colours.items():
            assert re.fullmatch(r'#[0-9A-F]{6}', value), \
                f'{mode_name}/{key}: {value!r} ist kein #RRGGBB'


def test_red_is_never_used_as_text(palette):
    """Ausdrückliche Vorgabe: Rot erscheint nur als Fläche.

    Auf dunklem Grund erreicht das Wappen-Rot nur 3,38:1 — als Schriftfarbe
    wäre es unzulässig, und ein aufgehelltes Rot wäre nicht mehr die
    Wappenfarbe.
    """
    for mode_name, colours in palette.MODES.items():
        for key in ('text', 'text_muted', 'timestamp'):
            value = colours[key].lstrip('#')
            r, g, b = (int(value[i:i + 2], 16) for i in (0, 2, 4))
            assert not (r > g + 40 and r > b + 40), \
                f'{mode_name}/{key} ist rötlich ({colours[key]})'


def test_the_dark_mode_is_actually_dark(palette):
    """Sonst wäre der Satz versehentlich eine Kopie des hellen."""
    def luminance(c):
        c = c.lstrip('#')
        return sum(int(c[i:i + 2], 16) for i in (0, 2, 4)) / 3
    assert luminance(palette.DARK['bg']) < 60
    assert luminance(palette.LIGHT['bg']) > 200


def test_default_mode_is_dark(palette):
    """So entschieden nach der Erprobung von v0.7.3."""
    assert palette.DEFAULT_MODE == 'dark'


# -- Die erzeugte CustomTkinter-Theme-Datei -----------------------------

@pytest.fixture(scope='module')
def theme_json(root):
    return json.loads(
        (root / 'noScribe' / 'theme' / 'rlp_justiz.json').read_text(encoding='utf-8'))


def test_theme_file_has_distinct_light_and_dark_values(theme_json):
    """Vor dieser Überarbeitung waren beide Einträge jedes Paares gleich —
    der Dunkelmodus war eine Attrappe."""
    differing = 0
    for widget, entries in theme_json.items():
        if widget == 'CTkFont':
            continue
        for key, value in entries.items():
            if isinstance(value, list) and len(value) == 2 and value[0] != value[1]:
                differing += 1
    assert differing > 10, (
        'Fast alle Farbpaare sind identisch — die Theme-Datei wurde '
        'offenbar nicht aus der Palette neu erzeugt.')


# Bedienelemente, bei denen `fg_color` tatsächlich der Hintergrund der
# Beschriftung ist. Bei CTkCheckBox, CTkRadioButton und CTkSwitch ist
# `fg_color` dagegen die Füllung des Kästchens beziehungsweise des Schiebers —
# die Beschriftung sitzt daneben auf der Fläche des Elternelements. Die dort
# gegeneinander zu prüfen, wäre schlicht falsch.
TEXT_ON_OWN_SURFACE = (
    'CTkButton', 'CTkEntry', 'CTkOptionMenu', 'CTkComboBox',
    'CTkTextbox', 'DropdownMenu',
)

# Beschriftungen, die auf der Fläche des Elternelements liegen. Sie müssen
# gegen jede Fläche tragen, auf der ein solches Bedienelement stehen kann.
LABEL_ON_PARENT = ('CTkLabel', 'CTkCheckBox', 'CTkRadioButton', 'CTkSwitch')


def test_theme_text_colours_are_readable(theme_json):
    """Jede Textfarbe gegen die Fläche, auf der sie tatsächlich liegt."""
    failures = []
    for widget in TEXT_ON_OWN_SURFACE:
        entries = theme_json[widget]
        fg, text = entries.get('fg_color'), entries.get('text_color')
        if not isinstance(fg, list) or not isinstance(text, list):
            continue
        for index, mode_name in enumerate(('hell', 'dunkel')):
            actual = contrast(text[index], fg[index])
            if actual < 7.0:
                failures.append(
                    f'{widget} ({mode_name}): Text {text[index]} auf '
                    f'{fg[index]} erreicht nur {actual:.2f}:1')
    assert not failures, '\n' + '\n'.join(failures)


def test_labels_are_readable_on_every_surface_they_sit_on(theme_json, palette):
    """Beschriftungen liegen auf dem Elternelement, nicht auf sich selbst."""
    surfaces = ('bg', 'surface', 'surface_alt')
    failures = []
    for widget in LABEL_ON_PARENT:
        text = theme_json[widget].get('text_color')
        if not isinstance(text, list):
            continue
        for index, (mode_name, colours) in enumerate(
                (('hell', palette.LIGHT), ('dunkel', palette.DARK))):
            for surface in surfaces:
                actual = contrast(text[index], colours[surface])
                if actual < 7.0:
                    failures.append(
                        f'{widget} ({mode_name}): Beschriftung {text[index]} '
                        f'auf {surface} ({colours[surface]}) erreicht nur '
                        f'{actual:.2f}:1')
    assert not failures, '\n' + '\n'.join(failures)


def test_the_selected_tab_stays_readable(theme_json):
    """CTkSegmentedButton hat nur EINE Textfarbe für gewählte und ungewählte
    Reiter. Beide Flächen müssen sie tragen — deshalb ist die Signalfarbe dort
    bewusst nicht verwendet."""
    entries = theme_json['CTkSegmentedButton']
    text = entries['text_color']
    for index, mode_name in enumerate(('hell', 'dunkel')):
        for key in ('selected_color', 'unselected_color'):
            actual = contrast(text[index], entries[key][index])
            assert actual >= 7.0, (
                f'{mode_name}/{key}: {text[index]} auf {entries[key][index]} '
                f'erreicht nur {actual:.2f}:1')


def test_theme_file_is_generated_from_the_palette(root):
    """Sonst laufen Palette und Theme-Datei auseinander, und die Begründungen
    in der Palette beschreiben etwas, das gar nicht mehr gilt."""
    import subprocess
    import sys
    # sys.executable statt 'python3': unter Windows gibt es den Namen nicht.
    result = subprocess.run(
        [sys.executable, str(root / 'scripts' / 'make_theme.py'), '--check'],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


# -- Der Fehler, der das alles ausgelöst hat ----------------------------

TRANSPARENT_BUTTON = re.compile(
    r'ctk\.CTkButton\((?:[^()]|\([^()]*\))*?\)', re.DOTALL)


def test_transparent_buttons_always_set_their_text_colour(root):
    """Der Fehler aus v0.7.3, als Regel festgehalten.

    Ein `CTkButton` mit `fg_color='transparent'` sitzt auf irgendeiner Fläche
    und erbt sonst die Textfarbe der roten Hauptschaltfläche — Weiß. Auf einer
    weissen Karte ergibt das 1,00:1, also unsichtbar.
    """
    source = (root / 'noScribe' / 'main.py').read_text(encoding='utf-8')
    offenders = []
    for match in TRANSPARENT_BUTTON.finditer(source):
        call = match.group(0)
        if "fg_color='transparent'" not in call and 'fg_color="transparent"' not in call:
            continue
        if 'text_color' in call:
            continue
        line = source[:match.start()].count('\n') + 1
        offenders.append(f'main.py:{line}')
    assert not offenders, (
        'Diese Schaltflächen sind transparent, legen aber keine Textfarbe '
        'fest und erben damit Weiss: ' + ', '.join(offenders))
