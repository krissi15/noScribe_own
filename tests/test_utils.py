"""Die reinen Hilfsfunktionen aus noScribe/utils.py.

Sie brauchen weder GUI noch Modelle und lassen sich deshalb als einzige
Programmlogik günstig absichern.
"""

import pytest


@pytest.mark.parametrize('text, expected', [
    ('00:00:00', 0),
    ('00:00:01', 1_000),
    ('00:01:00', 60_000),
    ('01:00:00', 3_600_000),
    ('1:2:3', 3_723_000),
])
def test_str_to_ms(utils, text, expected):
    assert utils.str_to_ms(text) == expected


@pytest.mark.parametrize('ms, expected', [
    (0, '00:00:00'),
    (1_000, '00:00:01'),
    (60_000, '00:01:00'),
    (3_600_000, '01:00:00'),
])
def test_ms_to_str(utils, ms, expected):
    assert utils.ms_to_str(ms) == expected


@pytest.mark.parametrize('ms', [0, 999, 1_000, 61_000, 3_661_000, 86_399_000])
def test_round_trip(utils, ms):
    """Ohne Millisekunden ist die Umwandlung auf volle Sekunden verlustbehaftet."""
    assert utils.str_to_ms(utils.ms_to_str(ms)) == ms - (ms % 1000)


def test_ms_to_str_with_milliseconds(utils):
    assert utils.ms_to_str(1_234, include_ms=True).endswith('.234')


def test_html_to_text_keeps_the_words(utils):
    html = '<html><body><p>Guten Tag.</p><p>Bitte nehmen Sie Platz.</p></body></html>'
    text = utils.html_to_text(html)
    assert 'Guten Tag.' in text
    assert 'Bitte nehmen Sie Platz.' in text
    assert '<p>' not in text


def test_html_to_text_resolves_entities(utils):
    assert 'Müller & Co.' in utils.html_to_text('<html><body><p>M&uuml;ller &amp; Co.</p></body></html>')


# So sieht ein von Traudi geschriebenes Transkript im Kern aus: eine
# Überschrift, ein Absatz mit den Angaben zur Aufnahme, dann die Segmente mit
# ihren Zeitmarken in `name="ts_<start>_<ende>_<sprecher>"`.
TRANSCRIPT_HTML = """<html><body>
<p>Traudi Transkript</p>
<p>aufnahme.mp3</p>
<p><a name="ts_0_1500_S1">Guten Tag.</a>
<a name="ts_1500_3000_S2">Nehmen Sie bitte Platz.</a></p>
</body></html>"""


def test_html_to_webvtt_starts_with_the_signature(utils):
    """Ohne die WEBVTT-Kopfzeile lehnen Abspielprogramme die Datei ab."""
    assert utils.html_to_webvtt(TRANSCRIPT_HTML).lstrip().startswith('WEBVTT')


def test_html_to_webvtt_carries_the_text_and_timings(utils):
    vtt = utils.html_to_webvtt(TRANSCRIPT_HTML)
    assert 'Guten Tag.' in vtt
    assert 'Nehmen Sie bitte Platz.' in vtt
    # 1500 ms Startzeit des zweiten Segments.
    assert '00:00:01.500' in vtt
