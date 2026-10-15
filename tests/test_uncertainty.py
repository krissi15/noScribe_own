"""Unsichere Wörter werden im Transkript unterstrichen (Prüfung A1).

Whisper liefert je Wort eine Wahrscheinlichkeit; sie wurde bisher verworfen.
"""

import pytest

from conftest import load_module

unc = load_module('noScribe/uncertainty.py')

U, E = unc.UNDERLINE_OPEN, unc.UNDERLINE_CLOSE


def words(*pairs):
    return [{'word': w, 'prob': p} for w, p in pairs]


def test_marks_only_uncertain_words():
    html = unc.segment_html(' Herr Müller kam', words((' Herr', 0.9), (' Müller', 0.3),
                                                     (' kam', 0.8)), 0.5)
    assert html == f' Herr {U}Müller{E} kam'


def test_text_is_escaped_inside_and_outside_the_mark():
    html = unc.segment_html(' a<b & c', words((' a<b', 0.1), (' &', 0.9), (' c', 0.9)), 0.5)
    assert html == f' {U}a&lt;b{E} &amp; c'


def test_punctuation_stays_with_the_word():
    html = unc.segment_html(' Ja, gut.', words((' Ja,', 0.2), (' gut.', 0.9)), 0.5)
    assert html == f' {U}Ja,{E} gut.'


def test_leading_and_trailing_whitespace_of_the_segment_is_kept():
    html = unc.segment_html('  Ja ', words((' Ja', 0.2),), 0.5)
    assert html == f'  {U}Ja{E} '


@pytest.mark.parametrize('ws', [None, []])
def test_without_words_plain_text(ws):
    assert unc.segment_html(' a<b', ws, 0.5) == ' a&lt;b'


def test_mismatching_words_fall_back_to_plain_text():
    assert unc.segment_html(' Hallo Welt', words((' Hallo', 0.1), (' Wald', 0.1)), 0.5) \
        == ' Hallo Welt'


def test_threshold_zero_switches_marking_off():
    assert unc.segment_html(' Ja', words((' Ja', 0.01),), 0.0) == ' Ja'


def test_missing_probability_is_not_marked():
    assert unc.segment_html(' Ja', [{'word': ' Ja', 'prob': None}], 0.5) == ' Ja'


@pytest.mark.parametrize('value, expected', [
    ('0.5', 0.5), (0.3, 0.3), ('0,4', 0.4), (50, 0.5), ('0', 0.0),
    ('aus', 0.5), (None, 0.5), (-1, 0.0), (250, 1.0),
])
def test_threshold_from_config(value, expected):
    assert unc.threshold_from_config(value) == pytest.approx(expected)


def test_every_segment_branch_uses_the_marked_html(root):
    source = (root / 'noScribe' / 'main.py').read_text(encoding='utf-8')
    assert 'html.escape(seg_text' not in source
    assert 'uncertainty.segment_html(segment.text, segment.words' in source
