"""Der Editor spricht Deutsch -- durchgehend und in der Sie-Form.

Anlass (Prüfung Oktober 2026): Menüs und Meldungen des Editors waren
englisch, der Sprecher-Dialog deutsch; die Standardknöpfe ("Save",
"Discard") blieben englisch, weil Qts eigene Übersetzung nicht geladen war.
In der deutschen Übersetzung des Hauptprogramms stand teils "du", teils "Sie".
"""

import re

import pytest

ENGLISH_UI = [
    '"&File"', '"&Edit"', '"Open file..."', '"Save As..."', '"Undo"', '"Redo"',
    '"Find and Replace"', '"Loading... please wait."', '"Untitled"',
    'The document has been modified', 'Audio source file not found',
    'Search text is empty', '"Find Next"', '"Replace All"', '"Close"',
]


@pytest.fixture(scope='module')
def editor_sources(root):
    return {name: (root / 'noScribeEdit' / name).read_text(encoding='utf-8')
            for name in ('noScribeEdit.py', 'search_and_replace_dialog.py')}


@pytest.mark.parametrize('needle', ENGLISH_UI)
def test_no_english_ui_strings_left(editor_sources, needle):
    for name, source in editor_sources.items():
        assert needle not in source, f'{needle} in {name}'


def test_qt_standard_buttons_are_translated(editor_sources):
    source = editor_sources['noScribeEdit.py']
    assert 'QtCore.QTranslator(' in source
    assert "'qtbase'" in source
    assert 'app.installTranslator(' in source


def test_german_translation_uses_sie(root):
    text = (root / 'trans' / 'noScribe.de.yml').read_text(encoding='utf-8')
    du_forms = re.findall(r'\b(du|dich|dein\w*|möchtest|kannst|willst|musst|hast)\b', text,
                          flags=re.IGNORECASE)
    assert du_forms == []
