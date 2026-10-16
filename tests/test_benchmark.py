"""Messmodus (--benchmark) und Auswertung (scripts/benchmark_report.py).

Ziel: Versionen und Rechner vergleichbar machen -- Dauer je Arbeitsschritt,
Wortfehlerrate gegenüber einem geprüften Vergleichstext, Sprecherzahl.
"""

import json

import pytest

from conftest import load_module

bench = load_module('noScribe/benchmark.py')
report = load_module('scripts/benchmark_report.py')


# --- Messmodus ---------------------------------------------------------------

def test_phase_seconds_from_status_log():
    log = [('waiting', 0.0), ('audio_conversion', 10.0), ('speaker_identification', 15.0),
           ('transcription', 115.0), ('finished', 415.0)]
    assert bench.phase_seconds(log) == {'waiting': 10.0, 'audio_conversion': 5.0,
                                        'speaker_identification': 100.0, 'transcription': 300.0}


def test_machine_description_never_fails():
    m = bench.machine()
    assert set(m) == {'cpu', 'cores_physical', 'cores_logical', 'ram_gb', 'gpus', 'os'}
    assert isinstance(m['gpus'], list)


def test_sidecar_name(tmp_path):
    assert bench.sidecar_path(tmp_path / 'a.html').name == 'a.benchmark.json'


def test_report_totals_exclude_waiting(tmp_path):
    class Job:
        audio_file = tmp_path / 'x.mp3'
        transcript_file = tmp_path / 'x.html'
        status = 'finished'
        status_log = [('waiting', 0.0), ('audio_conversion', 100.0),
                      ('transcription', 110.0), ('finished', 170.0)]
    data = bench.report(Job(), '0.7.7', {'model': 'precise'})
    assert data['seconds']['total'] == 70.0
    assert data['seconds']['transcription'] == 60.0
    assert data['seconds']['speaker_identification'] is None
    json.dumps(data)


def test_job_records_every_status_change(root):
    source = (root / 'noScribe' / 'main.py').read_text(encoding='utf-8')
    assert 'self.status_log.append((' in source
    assert "parser.add_argument('--benchmark'" in source
    assert '_write_benchmark(job, args)' in source


# --- Auswertung --------------------------------------------------------------

def test_normalize_drops_labels_pauses_timestamps_and_punctuation():
    assert report.normalize('S01: Guten Tag, Herr Fischer! (..) [00:01:02] Am 24.03.1994.') == \
        ['guten', 'tag', 'herr', 'fischer', 'am', '24031994']


def test_wer_counts():
    r = report.wer('der angeklagte schweigt heute'.split(), 'der angeklagte schwieg'.split())
    assert r == {'wer': 0.5, 'words': 4, 'sub': 1, 'del': 1, 'ins': 0}
    assert report.wer(['a'], ['a'])['wer'] == 0.0
    assert report.wer(['a'], ['a', 'b'])['ins'] == 1


def test_segments_and_window():
    page = ('<p><a name="ts_0_1000_S01" >S01: Guten <span style="text-decoration: underline" >Tag</span>.</a>'
            '<a name="ts_1000_2000_S01" > Bitte.</a><a name="ts_5000_6000_S02" >S02: Danke.</a></p>')
    segs = report.segments(page)
    assert [s[2] for s in segs] == ['S01', 'S01', 'S02']
    assert report.words_in_window(segs, 0, 2500) == ['guten', 'tag', 'bitte']


def test_evaluate_end_to_end(tmp_path):
    ref = '<a name="ts_0_2000_S01" >S01: Guten Tag Herr Fischer.</a>'
    hyp = '<a name="ts_0_2000_S01" >S01: Guten Tag, Herr Fischer.</a><a name="ts_9000_9500_S02" >Später.</a>'
    (tmp_path / 'ref.html').write_text(ref, encoding='utf-8')
    (tmp_path / 'hyp.html').write_text(hyp, encoding='utf-8')
    (tmp_path / 'runs.json').write_text(json.dumps({
        'reference': 'ref.html', 'audio_seconds': 10,
        'runs': [{'label': 'v', 'machine': 'm', 'transcript': 'hyp.html', 'seconds_total': 5}]}),
        encoding='utf-8')
    result = report.evaluate(tmp_path / 'runs.json')
    run = result['runs'][0]
    assert run['wer']['wer'] == 0.0          # "Später" liegt außerhalb des Ausschnitts
    assert run['realtime_factor'] == 0.5
    assert run['speakers'] == 2
    assert '<table>' in report.render_html(result)


def test_cuda_info_never_fails():
    info = bench.cuda_info()
    assert set(info) == {'available', 'device'}
