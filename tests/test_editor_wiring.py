"""Die drei Stellen, die über den Editor Bescheid wissen, müssen sich einig sein.

Vor der Übernahme klafften sie auseinander: `noScribe_win.spec` kopierte das
**Quellverzeichnis** `../noScribeEdit/` in das Bündel, während
`pyinstaller/win_build.py` und `noScribe/main.py` dort eine fertig gebaute
`noScribeEdit.exe` erwarteten. Das passte nur zusammen, wenn jemand den Editor
vorher von Hand gebaut hatte — sonst fehlte er im Installer, und weil das
Ergebnis nur stillschweigend übersprungen wurde, fiel es niemandem auf.

Genau das prüfen diese Tests nach.
"""

import re

import pytest


@pytest.fixture(scope='module')
def spec(root):
    return (root / 'pyinstaller' / 'noScribe_win.spec').read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def build_source(root):
    return (root / 'pyinstaller' / 'win_build.py').read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def main_source(root):
    return (root / 'noScribe' / 'main.py').read_text(encoding='utf-8')


def test_the_editor_is_part_of_the_repository(root):
    """Er lag früher in einem fremden Repository und war deshalb meistens
    einfach nicht da."""
    editor = root / 'noScribeEdit'
    assert editor.is_dir(), 'noScribeEdit/ fehlt'
    assert (editor / 'noScribeEdit.py').is_file()
    assert (editor / 'noScribeEdit_win.spec').is_file()


def test_the_gpl_notice_is_present(root):
    """GPL-3.0 §5(a): ein verändertes Werk muss das ausweisen, mit Datum.

    Für eine Auslieferung durch eine öffentliche Stelle ist das keine
    Formalie.
    """
    notice = root / 'noScribeEdit' / 'NOTICE.md'
    assert notice.is_file(), 'noScribeEdit/NOTICE.md fehlt'
    text = notice.read_text(encoding='utf-8')
    assert 'kaixxx/noScribeEditor' in text, 'Der Ursprung muss genannt sein'
    assert re.search(r'\b20\d\d\b', text), 'Das Datum der Übernahme muss dastehen'
    assert 'GNU General Public License' in text


def test_the_licence_travelled_with_the_code(root):
    assert (root / 'noScribeEdit' / 'LICENSE').is_file()


def test_the_spec_bundles_the_built_editor_not_the_sources(spec):
    """Der alte Fehler: die Spec nahm den Quellordner, gesucht wurde eine .exe."""
    assert "'../noScribeEdit/'" not in spec, (
        'Die Spec bindet wieder das Quellverzeichnis ein statt des gebauten '
        'Editors — dann liegt im Bündel Python-Quelltext statt eines '
        'ausführbaren Programms.')
    assert "'dist', 'editor', 'noScribeEdit'" in spec


def test_build_and_spec_agree_on_where_the_editor_lands(spec, build_source):
    """Beide müssen denselben Ort meinen, sonst packt die Spec ins Leere."""
    assert "EDITOR_DIST = SCRIPT_DIR / 'dist' / 'editor'" in build_source
    assert "'dist', 'editor', 'noScribeEdit'" in spec


def test_the_build_fails_loudly_when_the_editor_is_missing(build_source):
    """Ein Installer ohne Editor soll eine Entscheidung sein, kein Unfall."""
    assert 'raise SystemExit' in build_source
    assert '--skip-editor' in build_source, (
        'Es braucht einen ausdrücklichen Schalter, um den Editor wegzulassen.')


def test_the_editor_is_built_before_the_main_run(build_source):
    """Der Hauptlauf packt das Ergebnis ein — er darf nicht zuerst laufen.

    Nur in main() gesucht: weiter oben steht die *Definition* von
    run_pyinstaller, und die kommt naturgemäß vor jedem Aufruf.
    """
    body = build_source[build_source.index('def main()'):]
    build_call = body.index('build_editor(clean=')
    main_call = body.index('run_pyinstaller(dist_dir')
    assert build_call < main_call


def test_the_app_looks_for_the_editor_where_the_build_puts_it(main_source):
    """main.py löst `noScribeEdit/noScribeEdit.exe` im Bündel auf; die Spec
    kopiert genau dorthin."""
    assert 'impres.files("noScribeEdit")' in main_source


def test_ci_installs_the_editor_dependencies(root):
    """Der Editor bringt PyQt6 mit. Fehlt es, bricht der Bau ab — was richtig
    ist, aber eben auch heißt, dass die CI es mitbringen muss."""
    workflow = (root / '.github' / 'workflows' / 'build-windows.yml').read_text(
        encoding='utf-8')
    assert 'noScribeEdit/environments/requirements.txt' in workflow


def test_the_editor_directory_is_not_ignored(root):
    """Eine Falle, die fast alles Weitere stillschweigend verschluckt haette.

    Die Wurzel-`.gitignore` schloss `noScribeEdit/*` aus -- der Editor lag
    frueher in einem eigenen Repository und wurde nur danebengelegt. Der
    `git subtree add` brachte die vorhandenen Dateien trotzdem herein, aber
    **jede neue** Datei dort waere unbemerkt nie eingecheckt worden: das
    Farbschema, der Sprecher-Dialog, die Symbole.
    """
    ignore = (root / '.gitignore').read_text(encoding='utf-8')
    lines = [line.strip() for line in ignore.splitlines()]
    assert 'noScribeEdit/*' not in lines, (
        'Die .gitignore schliesst das Editor-Verzeichnis wieder aus. Neue '
        'Dateien dort landen dann nicht im Repository und fehlen im Bau.')


def test_the_editor_extras_are_actually_tracked(root):
    """Der Gegenbeweis in der Sache: liegen die neuen Dateien wirklich im
    Repository, oder nur auf dieser Platte?"""
    import subprocess

    tracked = subprocess.run(
        ['git', 'ls-files', 'noScribeEdit/'],
        cwd=root, capture_output=True, text=True, check=True).stdout.split()
    for needed in ('noScribeEdit/traudi_theme.py',
                   'noScribeEdit/traudi_colors.json',
                   'noScribeEdit/speaker_dialog.py',
                   'noScribeEdit/traudi_logo.png',
                   'noScribeEdit/NOTICE.md'):
        assert needed in tracked, f'{needed} ist nicht versioniert'
