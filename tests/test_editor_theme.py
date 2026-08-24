"""Der Editor muss dieselben Farben tragen wie Traudi -- und dieselbe Quelle.

Der uebernommene Editor kannte gar keine Farbwahl: Text war fest ``#000000``
auf fest ``#ffffff``, und das gesamte Transkript steht in Ankern, deren Farbe
per ``setDefaultStyleSheet`` ebenfalls fest auf Schwarz stand. Wer Traudi im
Dunkelmodus benutzte, bekam beim Oeffnen des Transkripts ein grelles weisses
Fenster -- oder, je nach Windows-Einstellung, schwarze Schrift auf dunklem
Grund.

Diese Tests halten zweierlei fest: dass die Farben aus der Palette kommen und
nicht aus dem Editor, und dass keine festen Werte zurueckkehren.
"""

import ast
import importlib.util
import json
import re

import pytest


@pytest.fixture(scope='module')
def theme(root):
    path = root / 'noScribeEdit' / 'traudi_theme.py'
    spec = importlib.util.spec_from_file_location('_traudi_editor_theme', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def palette(root):
    path = root / 'noScribe' / 'theme' / 'palette.py'
    spec = importlib.util.spec_from_file_location('_traudi_palette', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def editor_source(root):
    return (root / 'noScribeEdit' / 'noScribeEdit.py').read_text(encoding='utf-8')


def test_the_editor_colours_come_from_the_palette(root, palette):
    """Eine Quelle, zwei Programme. Wer die Palette aendert, aendert beide."""
    data = json.loads((root / 'noScribeEdit' / 'traudi_colors.json')
                      .read_text(encoding='utf-8'))
    assert data['light'] == palette.LIGHT
    assert data['dark'] == palette.DARK
    assert data['default_mode'] == palette.DEFAULT_MODE


def test_both_modes_are_complete(theme, palette):
    for mode in ('light', 'dark'):
        assert set(theme.colors_for(mode)) == set(palette.LIGHT)


def test_an_unknown_mode_falls_back_instead_of_failing(theme):
    """Eine beschaedigte Konfigurationsdatei darf den Editor nicht aufhalten."""
    assert theme.colors_for('lavendel') == theme.colors_for(theme.DEFAULT_MODE)


def test_the_stylesheet_uses_only_palette_colours(theme, palette):
    """Ein einzelner fest eingetragener Wert reicht, um in einem Modus
    unlesbar zu werden -- und faellt im anderen nicht auf."""
    for mode in ('light', 'dark'):
        colours = theme.colors_for(mode)
        allowed = {value.upper() for value in colours.values()}
        used = {m.upper() for m in re.findall(r'#[0-9A-Fa-f]{6}',
                                              theme.stylesheet(colours))}
        assert used <= allowed, f'Feste Farben im Stylesheet ({mode}): {used - allowed}'


def test_the_document_background_is_not_hard_coded(root):
    """Genau die Stellen, die den Dunkelmodus unmoeglich machten.

    Ohne Kommentare geprueft: dass in einer Begruendung ``#ffffff`` steht,
    ist ja gerade der Punkt.
    """
    import io
    import tokenize

    path = root / 'noScribeEdit' / 'noScribeEdit.py'
    with tokenize.open(path) as handle:
        tokens = list(tokenize.generate_tokens(handle.readline))
    code = ''.join(tok.string for tok in tokens
                   if tok.type not in (tokenize.COMMENT, tokenize.NL))

    assert '#ffffff' not in code.lower(), (
        'Im Editor steht wieder ein fester Weisswert.')
    assert 'color: #000000' not in code, (
        'Der Ankertext steht wieder fest auf Schwarz -- im Dunkelmodus ist '
        'damit das ganze Transkript unlesbar.')


def test_the_editor_reads_the_mode_from_traudi(editor_source):
    """Zwei Programme, die zusammengehoeren, sollen nicht in
    unterschiedlichen Farben aufgehen."""
    assert "appdirs.user_config_dir('Traudi')" in editor_source
    assert 'appearance_mode' in editor_source


def test_embedded_timestamps_are_recoloured_on_load(theme):
    """Die Zeitmarkenfarbe steht IM Transkript -- noScribe schreibt sie beim
    Speichern hinein. Ein im Dunkelmodus erzeugtes Transkript brachte im
    hellen Editor hellgraue Zeitmarken auf Weiss mit, rund 2:1."""
    html = ('<p>S01: <span style="color: #B6BDCA" >[00:01:02]</span>'
            'Guten Tag.</p>')
    result = theme.recolor_timestamps(html, '#3F4550')
    assert '#3F4550' in result
    assert '#B6BDCA' not in result
    assert 'Guten Tag.' in result


def test_recolouring_leaves_the_users_own_markup_alone(theme):
    """Wer im Editor etwas farbig hervorhebt, soll das behalten."""
    html = '<span style="color: #ff0000" >besonders wichtig</span>'
    assert theme.recolor_timestamps(html, '#000000') == html


def test_the_generated_colour_file_is_current(root):
    """Sonst laufen Palette und Editor auseinander, ohne dass es auffaellt."""
    import subprocess
    import sys
    result = subprocess.run([sys.executable, 'scripts/make_theme.py', '--check'],
                            cwd=root, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_the_editor_specs_ship_the_colour_file(root):
    """Fehlt sie im Buendel, faellt der Editor auf den Notnagel zurueck --
    still, und moeglicherweise im falschen Modus."""
    for name in ('noScribeEdit_win.spec', 'noScribeEdit-linux.spec'):
        spec = (root / 'noScribeEdit' / name).read_text(encoding='utf-8')
        assert 'traudi_colors.json' in spec, f'{name} liefert die Farbdatei nicht mit'
        assert 'traudi_logo' in spec, f'{name} traegt noch das alte Symbol'
