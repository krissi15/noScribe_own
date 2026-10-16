#!/usr/bin/env python3
"""Baut eine deutsche Prüfaufnahme mit bekanntem Wortlaut aus VoxPopuli.

VoxPopuli (Meta AI, CC0) enthält Redebeiträge aus dem Europäischen Parlament,
in Sätze zerlegt, mit Wortlaut und Sprecherkennung. Dieses Skript nimmt aus
dem deutschen Testteil eine Plenarsitzung mit möglichst vielen Rednern,
reiht ihre Abschnitte in der Reihenfolge der Sitzung aneinander und schreibt

    benchmark.wav            16 kHz mono, die Prüfaufnahme
    reference.html           der Wortlaut im Traudi-Format (Zeitmarken, Sprecher)
    reference.txt            derselbe Wortlaut als Text
    benchmark_meta.json      Quelle, Lizenz, Sitzung, Sprecher, Länge

`reference.html` dient `scripts/benchmark_report.py` als Vergleichstext.

Läuft in GitHub Actions (.github/workflows/benchmark-data.yml); dort gibt es
Netz. Abhängigkeiten: huggingface_hub, soundfile, numpy.
"""

import argparse
import csv
import html
import io
import json
import re
import sys
import tarfile
from collections import OrderedDict
from pathlib import Path

REPO = 'facebook/voxpopuli'
RATE = 16000


def log(*args):
    print(*args, flush=True)


# --- Auswahl (ohne Netz testbar) --------------------------------------------

def session_of(utt_id: str) -> str:
    """'20180206-0900-PLENARY-15-de_20180206-15:35:53_0' -> '20180206-0900-PLENARY-15-de'"""
    return utt_id.split('_', 1)[0]


def natural_key(text: str):
    return [int(p) if p.isdigit() else p for p in re.split(r'(\d+)', text)]


def pick_session(rows, min_seconds: float, max_seconds: float, durations: dict):
    """Die Sitzung mit den meisten Rednern, die mindestens `min_seconds`
    Aufnahme hat; Abschnitte in Sitzungsreihenfolge, gekappt bei
    `max_seconds`. Reicht keine Sitzung, werden die stärksten aneinander-
    gehängt."""
    sessions = OrderedDict()
    for row in rows:
        if row['id'] in durations and row['text'].strip():
            sessions.setdefault(session_of(row['id']), []).append(row)
    ranked = sorted(sessions.items(),
                    key=lambda kv: (len({r['speaker'] for r in kv[1]}),
                                    sum(durations[r['id']] for r in kv[1])),
                    reverse=True)
    chosen, total = [], 0.0
    for _, rows_s in ranked:
        for row in sorted(rows_s, key=lambda r: natural_key(r['id'])):
            if total >= max_seconds:
                break
            chosen.append(row)
            total += durations[row['id']]
        if total >= min_seconds:
            break
    return chosen


def speaker_labels(rows) -> dict:
    labels = OrderedDict()
    for row in rows:
        labels.setdefault(row['speaker'], f'S{len(labels) + 1:02d}')
    return labels


def reference_html(rows, starts_ms, ends_ms, labels, title) -> str:
    paragraphs, current, last = [], [], None
    for row, a, b in zip(rows, starts_ms, ends_ms):
        spk = labels[row['speaker']]
        text = html.escape(row['text'].strip(), quote=False)
        if spk != last:
            if current:
                paragraphs.append('<p>' + ''.join(current) + '</p>')
            current = [f'<a name="ts_{a}_{b}_{spk}" >{spk}: {text}</a>']
            last = spk
        else:
            current.append(f'<a name="ts_{a}_{b}_{spk}" > {text}</a>')
    if current:
        paragraphs.append('<p>' + ''.join(current) + '</p>')
    return ('<!DOCTYPE html><html><head><meta charset="UTF-8" /></head><body>'
            f'<p>{html.escape(title)}</p><p>Vergleichstext (VoxPopuli, CC0)</p>'
            + ''.join(paragraphs) + '</body></html>\n')


# --- Laden (Netz) -----------------------------------------------------------

def read_tsv(text: str) -> list:
    reader = csv.DictReader(io.StringIO(text), delimiter='\t', quoting=csv.QUOTE_NONE)
    rows = []
    for r in reader:
        rows.append({
            'id': r.get('id') or r.get('audio_id') or '',
            'text': r.get('raw_text') or r.get('normalized_text') or '',
            'speaker': r.get('speaker_id') or '',
        })
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=Path('benchmark_data'))
    parser.add_argument('--split', default='test')
    parser.add_argument('--min-minutes', type=float, default=15)
    parser.add_argument('--max-minutes', type=float, default=20)
    parser.add_argument('--gap', type=float, default=0.6, help='Pause zwischen Abschnitten (s)')
    args = parser.parse_args(argv)

    import numpy as np
    import soundfile as sf
    from huggingface_hub import HfApi, hf_hub_download

    files = HfApi().list_repo_files(REPO, repo_type='dataset')
    de = [f for f in files if f.startswith('data/de/')]
    log('Dateien unter data/de:', *de[:40], sep='\n  ')
    tsv_name = next(f for f in de if f.endswith(f'asr_{args.split}.tsv'))
    tars = sorted(f for f in de if f'/{args.split}/' in f and f.endswith(('.tar.gz', '.tar')))
    if not tars:
        log('Kein Audio-Archiv gefunden.')
        return 1

    rows = read_tsv(Path(hf_hub_download(REPO, tsv_name, repo_type='dataset')).read_text(encoding='utf-8'))
    log(f'{len(rows)} Abschnitte im TSV, z. B. {rows[0]}')

    audio, durations = {}, {}
    for name in tars:
        path = hf_hub_download(REPO, name, repo_type='dataset')
        with tarfile.open(path) as tar:
            for member in tar:
                if not member.isfile():
                    continue
                key = Path(member.name).name.rsplit('.', 1)[0]
                data, rate = sf.read(io.BytesIO(tar.extractfile(member).read()), dtype='float32')
                if data.ndim > 1:
                    data = data.mean(axis=1)
                if rate != RATE:
                    log(f'Abtastrate {rate} bei {key} -- übersprungen')
                    continue
                audio[key] = data
                durations[key] = len(data) / RATE
        log(f'{name}: {len(audio)} Abschnitte geladen')

    chosen = pick_session(rows, args.min_minutes * 60, args.max_minutes * 60, durations)
    if not chosen:
        log('Keine passende Sitzung gefunden.')
        return 1
    labels = speaker_labels(chosen)

    gap = np.zeros(int(args.gap * RATE), dtype='float32')
    pieces, starts, ends, pos = [], [], [], 0
    for row in chosen:
        clip = audio[row['id']]
        starts.append(round(pos / RATE * 1000))
        pos += len(clip)
        ends.append(round(pos / RATE * 1000))
        pieces += [clip, gap]
        pos += len(gap)
    signal = np.concatenate(pieces)

    args.out.mkdir(parents=True, exist_ok=True)
    sf.write(args.out / 'benchmark.wav', signal, RATE, subtype='PCM_16')
    sessions = sorted({session_of(r['id']) for r in chosen})
    title = f"VoxPopuli de, {', '.join(sessions)}"
    (args.out / 'reference.html').write_text(
        reference_html(chosen, starts, ends, labels, title), encoding='utf-8')
    (args.out / 'reference.txt').write_text(
        '\n'.join(f"{labels[r['speaker']]}: {r['text'].strip()}" for r in chosen) + '\n',
        encoding='utf-8')
    meta = {
        'source': f'https://huggingface.co/datasets/{REPO}',
        'license': 'CC0 1.0 (VoxPopuli)',
        'split': args.split,
        'sessions': sessions,
        'segments': len(chosen),
        'speakers': len(labels),
        'seconds': round(len(signal) / RATE, 1),
        'words': sum(len(r['text'].split()) for r in chosen),
        'gap_seconds': args.gap,
    }
    (args.out / 'benchmark_meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                                                  encoding='utf-8')
    log(json.dumps(meta, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
