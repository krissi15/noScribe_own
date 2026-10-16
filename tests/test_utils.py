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


def test_html_to_webvtt_note_covers_the_whole_header(utils):
    """Seit 0.7.7 stehen zwischen Titel und Text mehrere Absätze (Vermerk
    "maschineller Entwurf", Programm, Herkunft). Alle gehören in die NOTE."""
    html_str = """<html><body>
<p>Vernehmung</p>
<p>Maschineller Entwurf – nicht geprüft.</p>
<p>Audiodatei: a.mp3<br/>SHA-256 der Audiodatei: abc</p>
<p></p>
<p><a name="ts_0_1500_S1">Guten Tag.</a></p>
<p>Nachsatz ohne Zeitmarke</p>
</body></html>"""
    vtt = utils.html_to_webvtt(html_str)
    note = vtt.split('\n\n')[1]
    assert note.startswith('NOTE')
    assert 'Maschineller Entwurf' in note
    assert 'SHA-256 der Audiodatei: abc' in note
    assert 'Nachsatz' not in note


# --- Speichern während der Transkription ---------------------------------------
#
# Anlass: Bei einer 74-Minuten-Aufnahme legte 0.7.6 sieben Dateien an
# (..._1, ..._1_1, ...), sechs davon unvollständig. Jeder kurz gescheiterte
# Zwischenstand (Virenscanner/OneDrive halten die Datei fest) wechselte
# dauerhaft auf einen neuen Namen.

def test_write_with_retry_writes(utils, tmp_path):
    target = tmp_path / 't.html'
    assert utils.write_text_with_retry(target, 'Ä', attempts=1)
    assert target.read_text(encoding='utf-8') == 'Ä'


def test_write_with_retry_survives_a_short_lock(utils, tmp_path, monkeypatch):
    target = tmp_path / 't.html'
    real_open = open
    calls = []

    def flaky_open(path, *args, **kwargs):
        calls.append(path)
        if len(calls) < 3:
            raise PermissionError('gesperrt')
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr('builtins.open', flaky_open)
    assert utils.write_text_with_retry(target, 'x', attempts=5, delay=0)
    assert len(calls) == 3


def test_write_with_retry_gives_up_without_raising(utils, tmp_path):
    # Ein Verzeichnis lässt sich nicht als Datei öffnen.
    assert utils.write_text_with_retry(tmp_path, 'x', attempts=2, delay=0) is False


def test_autosave_does_not_switch_to_a_new_file(root):
    source = (root / 'noScribe' / 'main.py').read_text(encoding='utf-8')
    assert 'save_doc(final=False)' in source
    assert 'attempts=10 if final else 1' in source
