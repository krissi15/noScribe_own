# Traudi Editor - Sprecher umbenennen
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

"""Aus ``S01`` wird ``Zeugin Meier`` -- an allen Stellen auf einmal.

Die Sprechererkennung vergibt Kennungen wie ``S01``, ``S02``. Wer ein
Vernehmungsprotokoll gegenliest, will dort Namen stehen haben. Von Hand ist
das bei zwei Stunden Aufnahme dreistellig oft dieselbe Ersetzung.

Bewusst kein Suchen-und-Ersetzen: das griffe auch mitten im Text und wuerde
aus "S01" in einem Aktenzeichen ebenfalls einen Namen machen. Ersetzt wird
nur die Sprecherangabe **am Anfang eines Absatzes**.
"""

import re

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

# Eine Sprecherangabe steht am Absatzanfang und endet auf einem Doppelpunkt.
# Laengenbegrenzung, damit ein Satz mit Doppelpunkt nicht als Sprecher gilt.
SPEAKER_PATTERN = re.compile(r'^([^:\n]{1,40}):(?=\s|$)')


def collect_speakers(document):
    """Alle Sprecherangaben mit ihrer Haeufigkeit, in der Reihenfolge des Textes.

    Rueckgabe: Liste von (angabe, anzahl).
    """
    counts = {}
    order = []
    block = document.begin()
    while block.isValid():
        match = SPEAKER_PATTERN.match(block.text())
        if match:
            label = match.group(1).strip()
            if label:
                if label not in counts:
                    counts[label] = 0
                    order.append(label)
                counts[label] += 1
        block = block.next()
    return [(label, counts[label]) for label in order]


def apply_renames(document, mapping):
    """Benennt die Sprecher um. Rueckgabe: Anzahl geaenderter Absaetze.

    Ein einziger Rueckgaengig-Schritt fuer den ganzen Vorgang -- sonst muesste
    man dreihundertmal Strg+Z druecken, um einen Tippfehler zurueckzunehmen.
    """
    if not mapping:
        return 0

    edit = QtGui.QTextCursor(document)
    edit.beginEditBlock()
    changed = 0
    try:
        block = document.begin()
        while block.isValid():
            match = SPEAKER_PATTERN.match(block.text())
            if match:
                label = match.group(1).strip()
                new_name = mapping.get(label)
                if new_name:
                    cursor = QtGui.QTextCursor(document)
                    cursor.setPosition(block.position())
                    cursor.setPosition(block.position() + len(match.group(1)),
                                       QtGui.QTextCursor.MoveMode.KeepAnchor)
                    # Das Format mitnehmen: es traegt die Zeitmarke des
                    # Segments (anchorHref). Ohne sie verliert der Absatz
                    # seine Kopplung an die Aufnahme.
                    fmt = cursor.charFormat()
                    cursor.insertText(new_name, fmt)
                    changed += 1
            block = block.next()
    finally:
        edit.endEditBlock()
    return changed


class SpeakerRenameDialog(QtWidgets.QDialog):
    """Zeigt je Sprecher ein Eingabefeld, vorbelegt mit der Kennung."""

    def __init__(self, parent, speakers):
        super().__init__(parent)
        self.setWindowTitle("Sprecher umbenennen")
        self.setMinimumWidth(420)
        self._fields = {}

        layout = QtWidgets.QVBoxLayout(self)

        intro = QtWidgets.QLabel(
            "Die neuen Namen werden an allen Stellen des Transkripts "
            "eingesetzt. Leere Felder bleiben unveraendert.")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form_host = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(form_host)
        for label, count in speakers:
            field = QtWidgets.QLineEdit()
            field.setPlaceholderText(label)
            field.setClearButtonEnabled(True)
            self._fields[label] = field
            form.addRow(f'{label}  ({count}×)', field)

        # Bei vielen Sprechern soll der Dialog nicht ueber den Bildschirm
        # hinauswachsen.
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_host)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        layout.addWidget(scroll)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if speakers:
            self._fields[speakers[0][0]].setFocus(QtCore.Qt.FocusReason.OtherFocusReason)

    def renames(self):
        """Nur die tatsaechlich geaenderten Zuordnungen."""
        result = {}
        for label, field in self._fields.items():
            new_name = field.text().strip()
            if new_name and new_name != label:
                result[label] = new_name
        return result
