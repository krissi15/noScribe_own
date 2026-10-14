"""`import noScribe` darf nicht die ganze Anwendung mitziehen.

Gemeldet beim Einrichten:

    File "scripts/fetch_models.py", line 23, in <module>
        from noScribe.model_download import (
    File "noScribe/__init__.py", line 2, in <module>
        from noScribe import main
    ModuleNotFoundError: No module named 'AdvancedHTMLParser'

`model_download.py` braucht nur `huggingface_hub`. Ueber das Paket importiert
kam aber `__init__.py` dazwischen und lud `main` -- und damit
AdvancedHTMLParser, customtkinter, torch, faster-whisper und pyannote.

Das traf genau die falsche Stelle: Die Modellgewichte holt man, **bevor** die
vollen Abhaengigkeiten installiert sind. Das Skript, das beim Einrichten
helfen soll, setzte das fertige Einrichten voraus.
"""

import ast

import pytest


@pytest.fixture(scope='module')
def init_source(root):
    return (root / 'noScribe' / '__init__.py').read_text(encoding='utf-8')


def _imported_names(source):
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.update(alias.name for alias in node.names)
            if node.module:
                names.add(node.module)
    return names


def test_the_package_does_not_pull_in_the_application(init_source):
    assert 'main' not in _imported_names(init_source), (
        'noScribe/__init__.py importiert wieder `main`. Damit zieht schon '
        '`import noScribe` torch, faster-whisper und die GUI mit, und die '
        'Hilfsskripte lassen sich vor der vollstaendigen Installation nicht '
        'mehr benutzen.')


def test_the_version_stays_available(init_source):
    """Sie wird von pyproject, den Specs und win_build gelesen."""
    assert '__version__' in _imported_names(init_source)


def test_importing_the_package_needs_nothing_but_the_standard_library(root):
    """Der Gegenbeweis in der Sache -- in einem eigenen Prozess, damit
    bereits geladene Module das Ergebnis nicht verfaelschen."""
    import subprocess
    import sys

    probe = (
        'import sys; import noScribe; '
        'assert "noScribe.main" not in sys.modules, "main wurde mitgeladen"; '
        'print(noScribe.__version__)'
    )
    result = subprocess.run([sys.executable, '-c', probe],
                            cwd=root, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()


def test_the_entry_point_still_imports_main(root):
    """`python -m noScribe` muss weiterhin starten -- `__init__` tut es ja
    nicht mehr fuer ihn."""
    source = (root / 'noScribe' / '__main__.py').read_text(encoding='utf-8')
    assert 'from noScribe import main' in source


def test_a_crash_exits_with_a_failure_code(root):
    """`SystemExit(1)` stand dort ohne `raise`: ein Absturz beendete das
    Programm mit Rueckgabewert 0, und eine Softwareverteilung haette ihn
    als Erfolg verbucht."""
    source = (root / 'noScribe' / '__main__.py').read_text(encoding='utf-8')
    assert 'sys.exit(1)' in source
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Name) and func.id == 'SystemExit':
                raise AssertionError(
                    'SystemExit wird wieder nur erzeugt statt ausgeloest -- '
                    'ein Absturz meldet dann Erfolg.')


def test_the_download_script_can_run_before_the_app_is_installed(root):
    """Es braucht nur huggingface_hub, sonst nichts."""
    import subprocess
    import sys

    result = subprocess.run([sys.executable, 'scripts/fetch_models.py', '--help'],
                            cwd=root, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert '--pyannote' in result.stdout
