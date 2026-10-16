"""Prüfaufnahme aus VoxPopuli: Auswahl und Vergleichstext (ohne Netz)."""

from conftest import load_module

vp = load_module('scripts/make_benchmark_voxpopuli.py')
report = load_module('scripts/benchmark_report.py')


def rows():
    def r(i, spk, text='Guten Tag.'):
        return {'id': i, 'speaker': spk, 'text': text}
    return [
        r('20180206-0900-PLENARY-15-de_20180206-15:35:53_10', 'a'),
        r('20180206-0900-PLENARY-15-de_20180206-15:35:53_2', 'b'),
        r('20180206-0900-PLENARY-15-de_20180206-15:35:53_1', 'a'),
        r('20190101-0900-PLENARY-3-de_20190101-10:00:00_0', 'c'),
        r('20180206-0900-PLENARY-15-de_20180206-15:40:00_0', 'd', ''),   # ohne Text
    ]


def test_session_of():
    assert vp.session_of('20180206-0900-PLENARY-15-de_20180206-15:35:53_0') == \
        '20180206-0900-PLENARY-15-de'


def test_pick_session_prefers_most_speakers_in_session_order():
    durations = {r['id']: 300.0 for r in rows()}
    chosen = vp.pick_session(rows(), min_seconds=600, max_seconds=1200, durations=durations)
    assert [c['id'][-2:] for c in chosen] == ['_1', '_2', '10']
    assert all(c['text'] for c in chosen)


def test_pick_session_fills_up_from_the_next_session():
    durations = {r['id']: 300.0 for r in rows()}
    chosen = vp.pick_session(rows(), min_seconds=1000, max_seconds=1200, durations=durations)
    assert len(chosen) == 4
    assert vp.session_of(chosen[-1]['id']).startswith('20190101')


def test_reference_html_is_readable_by_the_report():
    chosen = rows()[:3]
    labels = vp.speaker_labels(chosen)
    page = vp.reference_html(chosen, [0, 4000, 8000], [3000, 7000, 11000], labels, 'T')
    segs = report.segments(page)
    assert [s[2] for s in segs] == ['S01', 'S02', 'S01']
    assert report.normalize(segs[0][3]) == ['guten', 'tag']


def test_log_accepts_print_keywords(capsys):
    vp.log('a', 'b', sep='|')
    assert capsys.readouterr().out == 'a|b\n'


def test_is_german():
    assert vp.is_german('data/de/asr_test.tsv')
    assert vp.is_german('de/test/0000.parquet')
    assert vp.is_german('transcribed_data/de_test.tsv')
    assert not vp.is_german('data/en/asr_test.tsv')
    assert not vp.is_german('data/delta/x.tsv')
