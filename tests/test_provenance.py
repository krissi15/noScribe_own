"""Nachprüfbarkeit: Vermerk "maschineller Entwurf" und Herkunft im Transkript.

Anlass (Prüfung Oktober 2026, A3/A4): Ein Transkript gelangt als Entwurf in
die Akte. Es fehlte der sichtbare Hinweis, dass es ungeprüft ist, und es ließ
sich nicht nachweisen, aus welcher Aufnahme und mit welchem Modell es
entstand.
"""

import datetime
import hashlib
import re

from conftest import load_module

provenance = load_module('noScribe/provenance.py')


def test_sha256_matches_hashlib(tmp_path):
    data = b'RIFF' + bytes(range(256)) * 5000
    f = tmp_path / 'a.wav'
    f.write_bytes(data)
    assert provenance.sha256_file(f, chunk_size=1000) == hashlib.sha256(data).hexdigest()


def test_known_models_name_their_source():
    assert provenance.describe_model('precise') == \
        'precise (dropbox-dash/faster-whisper-large-v3-turbo)'
    assert provenance.describe_model('mein-modell') == 'mein-modell'


def test_known_models_match_the_downloader(root):
    """Die Liste hier darf nicht von model_download.py abweichen."""
    source = (root / 'noScribe' / 'model_download.py').read_text(encoding='utf-8')
    for name, repo in provenance.KNOWN_MODELS.items():
        assert f"repo_id='{repo}'" in source, name


def test_model_name_from_object_or_path():
    class M:
        name = 'fast'
    assert provenance.model_name_of(M()) == 'fast'
    assert provenance.model_name_of('/x/y/precise') == 'precise'


def test_local_time_has_no_colon_between_digits():
    moment = datetime.datetime(2026, 10, 15, 14, 3)
    text = provenance.format_local(moment)
    assert text.startswith('15.10.2026 14')
    assert not re.search(r'\d:\d', text)


def test_meta_tags():
    created = datetime.datetime(2026, 10, 15, 14, 3, tzinfo=datetime.timezone.utc)
    tags = provenance.meta_tags('0.7.7', created, 'precise', 'ab' * 32)
    assert tags['traudi_version'] == '0.7.7'
    assert tags['traudi_created'] == '2026-10-15T14:03:00+00:00'
    assert tags['traudi_audio_sha256'] == 'ab' * 32
    assert 'faster-whisper' in tags['traudi_whisper_model']
    assert all(name.startswith('traudi_') for name in tags)


def test_transcript_header_carries_notice_and_provenance(root):
    source = (root / 'noScribe' / 'main.py').read_text(encoding='utf-8')
    for needle in ("t('doc_draft_notice')", "'doc_header_provenance'",
                   "'doc_header_sha256'", 'provenance.meta_tags(',
                   'provenance.sha256_file(job.audio_file)'):
        assert needle in source, needle


def test_editor_keeps_provenance_meta_when_saving(root):
    """QTextEdit verwirft unbekannte <meta>; der Editor muss sie retten."""
    source = (root / 'noScribeEdit' / 'noScribeEdit.py').read_text(encoding='utf-8')
    assert "startswith('traudi_')" in source
    assert 'for name, content in self.provenance_meta:' in source
