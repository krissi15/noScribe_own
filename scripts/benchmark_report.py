#!/usr/bin/env python3
"""Vergleicht Transkriptionsläufe: Dauer, Fehlerquote, Sprecher.

Aufruf:

    python scripts/benchmark_report.py runs.json -o vergleich.html

`runs.json` beschreibt die Läufe und den Vergleichstext:

    {
      "title": "Simulierte Hauptverhandlung (74 min)",
      "reference": "referenz.html",          # geprüfter Text, s. u.
      "runs": [
        {"label": "noScribe 0.7",  "machine": "Dienstlaptop",
         "transcript": "noscribe.html", "seconds_total": 9120},
        {"label": "Traudi 0.7.7", "machine": "Dienstlaptop",
         "transcript": "traudi.html", "benchmark": "traudi.benchmark.json"}
      ]
    }

Pfade gelten relativ zu `runs.json`. Für Versionen ohne Messmodus
(`--benchmark`) genügt `seconds_total` aus der Zeile "Gesamte
Verarbeitungszeit" im Protokoll.

Der Vergleichstext ist entweder
- ein im Traudi-Editor GEPRÜFTES Transkript (HTML mit Zeitmarken) -- dann
  wird nur der Zeitraum verglichen, den es abdeckt (z. B. 10 Minuten), oder
- eine Textdatei mit dem wortgetreuen Wortlaut der ganzen Aufnahme.

Fehlerquote = Wortfehlerrate (WER): (vertauschte + fehlende + zusätzliche
Wörter) / Wörter im Vergleichstext. Groß-/Kleinschreibung, Satzzeichen,
Sprecherkennungen ("S01:"), Pausenmarken und Zeitmarken zählen nicht.
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

SEGMENT = re.compile(r'<a\s+name="ts_(\d+)_(\d+)_([^"]*)"\s*>(.*?)</a>', re.S)
SPEAKER_PREFIX = re.compile(r'^\s*/{0,2}S\d{2}:\s*')
PAUSE = re.compile(r'\((?:\.+|\d+\s*\w+)\)')
TIMESTAMP = re.compile(r'\[\d{1,2}:\d{2}:\d{2}\]')


# --- Text -------------------------------------------------------------------

def segments(html_text: str) -> list:
    """[(start_ms, end_ms, sprecher, text)] aus einem Traudi-/noScribe-HTML."""
    out = []
    for m in SEGMENT.finditer(html_text):
        text = html.unescape(re.sub(r'<[^>]+>', '', m.group(4)))
        out.append((int(m.group(1)), int(m.group(2)), m.group(3).strip('/'), text))
    return out


def normalize(text: str) -> list:
    text = TIMESTAMP.sub(' ', text)
    text = PAUSE.sub(' ', text)
    text = text.replace('//', ' ')
    text = SPEAKER_PREFIX.sub(' ', text)
    text = re.sub(r'\bS\d{2}:', ' ', text)
    text = text.lower()
    # Zahlen wie 24.03.1994 oder 3,5 zusammenhalten, sonst Satzzeichen weg.
    text = re.sub(r'(?<=\d)[.,:](?=\d)', '', text)
    text = re.sub(r'[^\w§ ]+', ' ', text)
    return text.split()


def words_in_window(segs, start_ms, end_ms) -> list:
    words = []
    for a, b, _, t in segs:
        mid = (a + b) / 2
        if start_ms <= mid <= end_ms:
            words += normalize(t)
    return words


# --- Wortfehlerrate ---------------------------------------------------------

def wer(reference: list, hypothesis: list) -> dict:
    """Levenshtein auf Wortebene; zählt Ersetzungen, Auslassungen, Einfügungen."""
    n, m = len(reference), len(hypothesis)
    if n == 0:
        return {'wer': None, 'words': 0, 'sub': 0, 'del': 0, 'ins': m}
    # Zeilenweise DP mit Zählern je Zelle: (Kosten, sub, del, ins)
    prev = [(j, 0, 0, j) for j in range(m + 1)]
    for i in range(1, n + 1):
        cur = [(i, 0, i, 0)]
        r = reference[i - 1]
        for j in range(1, m + 1):
            if r == hypothesis[j - 1]:
                cur.append(prev[j - 1])
                continue
            s = prev[j - 1]
            d = prev[j]
            ins = cur[j - 1]
            best = min((s[0], 0), (d[0], 1), (ins[0], 2))
            if best[1] == 0:
                cur.append((s[0] + 1, s[1] + 1, s[2], s[3]))
            elif best[1] == 1:
                cur.append((d[0] + 1, d[1], d[2] + 1, d[3]))
            else:
                cur.append((ins[0] + 1, ins[1], ins[2], ins[3] + 1))
        prev = cur
    cost, sub, dele, ins = prev[m]
    return {'wer': round(cost / n, 4), 'words': n, 'sub': sub, 'del': dele, 'ins': ins}


# --- Läufe ------------------------------------------------------------------

def load_reference(path: Path):
    """-> (Wörter, Zeitfenster oder None, Sprecherwechsel oder None)."""
    text = path.read_text(encoding='utf-8')
    segs = segments(text)
    if segs:
        start, end = segs[0][0], segs[-1][1]
        words = []
        for s in segs:
            words += normalize(s[3])
        speakers = len({s[2] for s in segs})
        return words, (start, end), speakers
    return normalize(text), None, None


def evaluate(config_path: Path) -> dict:
    config = json.loads(config_path.read_text(encoding='utf-8'))
    base = config_path.parent
    ref_words, window, ref_speakers = (None, None, None)
    if config.get('reference'):
        ref_words, window, ref_speakers = load_reference(base / config['reference'])

    rows = []
    for run in config['runs']:
        row = {k: run.get(k) for k in ('label', 'machine', 'note')}
        bench = {}
        if run.get('benchmark'):
            bench = json.loads((base / run['benchmark']).read_text(encoding='utf-8'))
            row['seconds'] = bench.get('seconds', {})
            row['realtime_factor'] = bench.get('realtime_factor')
            row['hardware'] = bench.get('machine', {})
            row['version'] = bench.get('traudi_version')
            audio_s = (bench.get('audio') or {}).get('seconds')
        else:
            row['seconds'] = {'total': run.get('seconds_total')}
            audio_s = config.get('audio_seconds')
            row['realtime_factor'] = (round(run['seconds_total'] / audio_s, 2)
                                      if run.get('seconds_total') and audio_s else None)
        segs = segments((base / run['transcript']).read_text(encoding='utf-8'))
        row['segments'] = len(segs)
        row['speakers'] = len({s[2] for s in segs})
        row['audio_covered_s'] = round(segs[-1][1] / 1000) if segs else 0
        if ref_words is not None:
            hyp = (words_in_window(segs, *window) if window
                   else [w for s in segs for w in normalize(s[3])])
            row['wer'] = wer(ref_words, hyp)
        rows.append(row)
    return {'title': config.get('title', 'Vergleich'), 'reference_words': len(ref_words or []),
            'reference_window_ms': window, 'reference_speakers': ref_speakers,
            'audio_seconds': config.get('audio_seconds'), 'runs': rows}


# --- Ausgabe ----------------------------------------------------------------

def _fmt_s(seconds):
    if seconds is None:
        return '–'
    seconds = int(round(seconds))
    return f'{seconds // 60}:{seconds % 60:02d} min'


def render_html(result: dict) -> str:
    e = html.escape
    rows = []
    for r in result['runs']:
        sec = r.get('seconds') or {}
        w = r.get('wer') or {}
        hw = r.get('hardware') or {}
        wer_text = f"{w['wer'] * 100:.1f} %" if w.get('wer') is not None else '–'
        rows.append(
            '<tr>'
            f"<td>{e(r.get('label') or '')}</td>"
            f"<td>{e(r.get('machine') or '')}<br><small>{e(hw.get('cpu') or '')}</small></td>"
            f"<td class=n>{_fmt_s(sec.get('total'))}</td>"
            f"<td class=n>{_fmt_s(sec.get('speaker_identification'))}</td>"
            f"<td class=n>{_fmt_s(sec.get('transcription'))}</td>"
            f"<td class=n>{r.get('realtime_factor') if r.get('realtime_factor') is not None else '–'}</td>"
            f"<td class=n>{wer_text}</td>"
            f"<td class=n>{r.get('speakers')}</td>"
            '</tr>')
    window = result.get('reference_window_ms')
    ref_note = ''
    if result['reference_words']:
        ref_note = f"Vergleichstext: {result['reference_words']} Wörter"
        if window:
            ref_note += f", Ausschnitt {_fmt_s(window[0] / 1000)} bis {_fmt_s(window[1] / 1000)}"
        if result.get('reference_speakers'):
            ref_note += f", {result['reference_speakers']} Sprecher"
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(result['title'])}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 980px; padding: 0 16px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #ccc; padding: .5rem; text-align: left; vertical-align: top; }}
td.n {{ text-align: right; font-variant-numeric: tabular-nums; }}
small {{ color: #666; }}
</style></head><body>
<h1>{e(result['title'])}</h1>
<p>{e(ref_note)}</p>
<table>
<tr><th>Version</th><th>Rechner</th><th>Gesamt</th><th>Sprecher&shy;erkennung</th>
<th>Sprach&shy;erkennung</th><th>Faktor*</th><th>Fehlerquote</th><th>Sprecher</th></tr>
{''.join(rows)}
</table>
<p><small>* Rechenzeit je Minute Aufnahme; unter 1 ist schneller als Echtzeit.
Fehlerquote = Wortfehlerrate gegenüber dem Vergleichstext (vertauschte,
fehlende und zusätzliche Wörter je Wort im Vergleichstext).</small></p>
</body></html>
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('config', type=Path)
    parser.add_argument('-o', '--output', type=Path, default=Path('vergleich.html'))
    parser.add_argument('--json', type=Path, help='Ergebnis zusätzlich als JSON')
    args = parser.parse_args(argv)
    result = evaluate(args.config)
    args.output.write_text(render_html(result), encoding='utf-8')
    if args.json:
        args.json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    for r in result['runs']:
        w = (r.get('wer') or {}).get('wer')
        print(f"{r['label']:<28} {r.get('machine') or '':<16} "
              f"gesamt {_fmt_s((r.get('seconds') or {}).get('total')):>10}  "
              f"WER {('%.1f %%' % (w * 100)) if w is not None else '–':>7}  "
              f"Sprecher {r['speakers']}")
    print(f'-> {args.output}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
