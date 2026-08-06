#!/usr/bin/env python3
# Traudi - Laufzeitmessung der Transkription
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

"""Misst, was eine Änderung an der Transkription wirklich bringt.

    python scripts/benchmark.py aufnahme.mp3
    python scripts/benchmark.py aufnahme.mp3 --compute-type float32 --label vorher
    python scripts/benchmark.py aufnahme.mp3 --runs 3

Ausgegeben werden Laufzeit, das Verhältnis zur Aufnahmedauer (der Wert, den
man im Alltag spürt: "eine Stunde Audio braucht drei Stunden") und der
erzeugte Text. Der Text wird mitgeschrieben, damit sich prüfen lässt, ob eine
schnellere Einstellung die Qualität kostet -- eine Zeitangabe allein sagt
darüber nichts.

Die Sprechererkennung bleibt außen vor: sie läuft in einem eigenen Prozess und
würde die Messung nur verrauschen.
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from noScribe.whisper_args import build_prompt, load_vocabulary_file, resolve_compute_type  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('audio', type=Path, help='Testaufnahme')
    parser.add_argument('--model', default='precise',
                        help='Modellname unter models/ (Vorgabe: precise)')
    parser.add_argument('--models-dir', type=Path, default=PROJECT_ROOT / 'models')
    parser.add_argument('--device', default='cpu', choices=['cpu', 'cuda', 'auto'])
    parser.add_argument('--compute-type', default='auto',
                        help="'auto' wählt int8 auf der CPU, float16 auf der GPU")
    parser.add_argument('--beam-size', type=int, default=1)
    parser.add_argument('--threads', type=int, default=0,
                        help='0 = alle verfügbaren Kerne')
    parser.add_argument('--language', default='de')
    parser.add_argument('--condition-on-previous-text', action='store_true',
                        help='Wiederholungsschleifen zulassen (zum Vergleich)')
    parser.add_argument('--no-vocabulary', action='store_true',
                        help='ohne den Justiz-Wortschatz messen')
    parser.add_argument('--runs', type=int, default=1,
                        help='mehrfach messen und den Median ausgeben')
    parser.add_argument('--label', default='',
                        help='Bezeichnung für die Zeile in der Ausgabe')
    parser.add_argument('--json', type=Path,
                        help='Ergebnis zusätzlich als JSON ablegen')
    return parser.parse_args()


def transcribe_once(args, model, audio) -> tuple:
    """Eine Messung. Gibt (Sekunden, Text) zurück."""
    vocabulary = []
    if not args.no_vocabulary:
        vocabulary = load_vocabulary_file(PROJECT_ROOT / 'prompts' / 'vocab_justiz_de.txt')
    prompt = build_prompt('', vocabulary)

    started = time.perf_counter()
    segments, _info = model.transcribe(
        audio,
        language=args.language,
        beam_size=args.beam_size,
        word_timestamps=True,
        initial_prompt=prompt or None,
        condition_on_previous_text=args.condition_on_previous_text,
        vad_filter=True,
    )
    # segments ist ein Generator -- die Arbeit passiert erst beim Auslesen.
    text = ' '.join(segment.text.strip() for segment in segments)
    return time.perf_counter() - started, text


def main() -> int:
    args = parse_args()
    if not args.audio.is_file():
        raise SystemExit(f'Aufnahme nicht gefunden: {args.audio}')

    model_path = args.models_dir / args.model
    if not (model_path / 'model.bin').is_file():
        raise SystemExit(
            f'Modell nicht gefunden: {model_path}\n'
            f'Laden mit: python scripts/fetch_models.py --only {args.model}')

    from faster_whisper import WhisperModel
    from faster_whisper.audio import decode_audio

    device = args.device
    if device == 'auto':
        try:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        except ImportError:
            device = 'cpu'

    compute_type = resolve_compute_type(args.compute_type, device)
    threads = args.threads or 0

    print(f'Aufnahme:          {args.audio}')
    print(f'Modell:            {model_path.name}')
    print(f'Gerät:             {device}')
    print(f'Rechengenauigkeit: {compute_type}')
    print(f'beam_size:         {args.beam_size}')
    print(f'Wiederholungen:    {"zugelassen" if args.condition_on_previous_text else "unterbunden"}')
    print()

    load_started = time.perf_counter()
    model = WhisperModel(str(model_path), device=device, compute_type=compute_type,
                         cpu_threads=threads, local_files_only=True)
    load_seconds = time.perf_counter() - load_started
    print(f'Modell geladen in  {load_seconds:6.1f} s')

    # Einmal dekodieren und wiederverwenden: gemessen werden soll die
    # Transkription, nicht das Einlesen der Datei.
    audio = decode_audio(str(args.audio), sampling_rate=model.feature_extractor.sampling_rate)
    audio_seconds = len(audio) / model.feature_extractor.sampling_rate
    print(f'Aufnahmedauer      {audio_seconds:6.1f} s')
    print()

    durations = []
    text = ''
    for run in range(1, args.runs + 1):
        seconds, text = transcribe_once(args, model, audio)
        durations.append(seconds)
        print(f'Durchlauf {run}:       {seconds:6.1f} s '
              f'({seconds / audio_seconds:.2f}× Aufnahmedauer)')

    median = statistics.median(durations)
    print()
    print(f'{"Median":<18} {median:6.1f} s  =  {median / audio_seconds:.2f}× Aufnahmedauer')
    print(f'Wörter im Ergebnis: {len(text.split())}')
    print()
    print('--- Transkript (gekürzt) ---')
    print(text[:600] + (' …' if len(text) > 600 else ''))

    if args.json:
        args.json.write_text(json.dumps({
            'label': args.label,
            'audio': str(args.audio),
            'audio_seconds': audio_seconds,
            'model': model_path.name,
            'device': device,
            'compute_type': compute_type,
            'beam_size': args.beam_size,
            'condition_on_previous_text': args.condition_on_previous_text,
            'load_seconds': load_seconds,
            'durations': durations,
            'median_seconds': median,
            'realtime_factor': median / audio_seconds,
            'text': text,
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'\nErgebnis abgelegt: {args.json}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
