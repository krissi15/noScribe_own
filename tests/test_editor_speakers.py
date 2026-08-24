"""Sprecher umbenennen: die Ersetzung darf die Zeitmarken nicht verlieren.

Die Sprechererkennung vergibt ``S01``, ``S02``. Wer ein Vernehmungsprotokoll
gegenliest, will dort Namen stehen haben -- und zwar an allen Stellen.

Die Falle liegt nicht im Ersetzen, sondern im **Format**: jedes Segment traegt
seine Zeitmarke als ``anchorHref``. Wird der Text ohne dieses Format
eingesetzt, verliert der Absatz seine Kopplung an die Aufnahme, und der
Editor kann dort nicht mehr hinspringen. Das faellt beim Tippen nicht auf,
sondern erst beim Abhoeren.
"""

import os

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

# Nicht `importorskip`: fehlt eine Systembibliothek (libEGL), wirft der
# Import einen ImportError, den `importorskip` nicht als "fehlt eben" wertet.
# Diese Tests sollen laufen, wo sie koennen, und nicht scheitern, wo nicht.
try:
    from PyQt6 import QtGui
    from PyQt6 import QtWidgets
except ImportError as missing:      # pragma: no cover
    pytest.skip(f'PyQt6 nicht verfuegbar: {missing}', allow_module_level=True)


@pytest.fixture(scope='module')
def app():
    existing = QtWidgets.QApplication.instance()
    yield existing or QtWidgets.QApplication([])


@pytest.fixture(scope='module')
def speaker_dialog(root):
    import sys
    sys.path.insert(0, str(root / 'noScribeEdit'))
    import speaker_dialog
    return speaker_dialog


TRANSCRIPT = (
    '<p><a name="ts_0_2000" href="ts_0_2000">S01: '
    '<span style="color: #B6BDCA">[00:00:00]</span>Guten Tag.</a></p>'
    '<p><a name="ts_2000_5000" href="ts_2000_5000">S02: '
    '<span style="color: #B6BDCA">[00:00:02]</span>Guten Tag auch.</a></p>'
    '<p><a name="ts_5000_9000" href="ts_5000_9000">S01: '
    '<span style="color: #B6BDCA">[00:00:05]</span>Zur Sache.</a></p>'
)


@pytest.fixture
def document(app):
    doc = QtGui.QTextDocument()
    doc.setHtml(TRANSCRIPT)
    return doc


def test_every_speaker_is_found_once_with_its_count(speaker_dialog, document):
    assert speaker_dialog.collect_speakers(document) == [('S01', 2), ('S02', 1)]


def test_renaming_reaches_every_paragraph(speaker_dialog, document):
    changed = speaker_dialog.apply_renames(document, {'S01': 'Zeugin Meier'})
    assert changed == 2
    text = document.toPlainText()
    assert 'Zeugin Meier: ' in text
    assert 'S01' not in text
    assert 'S02: ' in text, 'Nicht genannte Sprecher bleiben unangetastet'


def test_the_timestamp_survives_the_rename(speaker_dialog, document):
    """Der eigentliche Grund fuer diesen Test."""
    speaker_dialog.apply_renames(document, {'S01': 'Zeugin Meier'})

    cursor = QtGui.QTextCursor(document)
    cursor.setPosition(3) # mitten im neuen Namen des ersten Absatzes
    assert cursor.charFormat().anchorHref() == 'ts_0_2000', (
        'Der umbenannte Absatz hat seine Zeitmarke verloren -- der Editor '
        'kann dort nicht mehr in die Aufnahme springen.')


def test_the_whole_rename_is_one_undo_step(speaker_dialog, document):
    """Sonst braeuchte es fuer einen Tippfehler dreihundert Mal Strg+Z."""
    speaker_dialog.apply_renames(document, {'S01': 'Zeugin Meier', 'S02': 'Herr Schmitt'})
    document.undo()
    text = document.toPlainText()
    assert 'S01: ' in text and 'S02: ' in text


def test_a_sentence_with_a_colon_is_not_a_speaker(speaker_dialog, app):
    """`SPEAKER_PATTERN` begrenzt die Laenge -- sonst wuerde jeder Absatz mit
    Doppelpunkt als Sprecherangabe gelten."""
    doc = QtGui.QTextDocument()
    doc.setHtml(
        '<p>Der Zeuge fuehrte dazu aus, dass es aus seiner Sicht drei '
        'wesentliche Gruende gab, die er wie folgt benannte: erstens.</p>')
    assert speaker_dialog.collect_speakers(doc) == []


def test_an_unnamed_speaker_is_left_alone(speaker_dialog, document):
    """Ein leeres Feld im Dialog heisst 'nicht anfassen', nicht 'loeschen'."""
    changed = speaker_dialog.apply_renames(document, {'S01': ''})
    assert changed == 0
    assert 'S01: ' in document.toPlainText()
