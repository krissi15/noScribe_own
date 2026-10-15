# Traudi - unsichere Wörter im Transkript kennzeichnen
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

"""Unterstreicht Wörter, bei denen sich Whisper unsicher war.

Whisper liefert zu jedem Wort eine Wahrscheinlichkeit. Bisher wurde sie
verworfen; wer das Protokoll prüfte, sah nicht, wo sich das Nachhören lohnt.
Gerade bei Vernehmungsniederschriften ist das der wichtigste Prüfhinweis.

Unterstrichen, weil das ohne Umfärben überall lesbar bleibt: in Word, im
hellen und im dunklen Editor (die Linie hat die Textfarbe). Nach der Prüfung
nimmt Strg+U sie wieder weg.

Die Wahrscheinlichkeit ist ein Hinweis, kein Beweis: Auch sicher erkannte
Wörter können falsch sein, gerade bei erfundenem Text ("Halluzination").
"""

import html

UNDERLINE_OPEN = '<span style="text-decoration: underline" >'
UNDERLINE_CLOSE = '</span>'


def threshold_from_config(value, default: float = 0.5) -> float:
    """0 schaltet die Markierung ab; Prozentangaben (50) gehen auch."""
    try:
        number = float(str(value).replace(',', '.'))
    except (TypeError, ValueError):
        return default
    if number > 1:
        number /= 100
    return min(max(number, 0.0), 1.0)


def segment_html(text: str, words, threshold: float) -> str:
    """HTML für den Text eines Segments, unsichere Wörter unterstrichen.

    Passen die Wörter nicht zum Segmenttext, bleibt der Text unmarkiert --
    lieber kein Hinweis als ein verrutschter.
    """
    text = text or ''
    plain = html.escape(text, quote=False)
    if not words or threshold <= 0:
        return plain
    pieces = [str(w.get('word') or '') for w in words]
    if ''.join(pieces).strip() != text.strip():
        return plain

    out = [html.escape(text[:len(text) - len(text.lstrip())], quote=False)]
    last = len(pieces) - 1
    for i, (word, info) in enumerate(zip(pieces, words)):
        if i == 0:
            word = word.lstrip()
        if i == last:
            word = word.rstrip()
        core = word.strip()
        lead = word[:len(word) - len(word.lstrip())]
        trail = word[len(lead) + len(core):]
        prob = info.get('prob')
        if core and prob is not None and prob < threshold:
            out.append(html.escape(lead, quote=False) + UNDERLINE_OPEN
                       + html.escape(core, quote=False) + UNDERLINE_CLOSE
                       + html.escape(trail, quote=False))
        else:
            out.append(html.escape(word, quote=False))
    out.append(html.escape(text[len(text.rstrip()):], quote=False))
    return ''.join(out)
