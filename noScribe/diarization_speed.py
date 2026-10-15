# Traudi - schnellere Sprechererkennung auf dem Prozessor
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

"""Spart der Sprechererkennung doppelte und leere Arbeit.

pyannote zerlegt die Aufnahme in 10-Sekunden-Fenster (Abstand 1 s) und sieht
in jedem Fenster drei Plätze für Sprecher vor. Für JEDEN Platz schickt es das
ganze Fenster einmal durch das Stimmabdruck-Netz ("embeddings" in der
Fortschrittsanzeige, der mit Abstand teuerste Schritt) -- dreimal dasselbe
Fenster, auch für Plätze, auf denen niemand spricht. Bei 1 h 14 min Aufnahme
sind das gut 13 000 Durchläufe.

Dabei wirkt der Platz erst ganz am Ende: Das Netz berechnet Merkmale für das
ganze Fenster, und erst die abschließende Mittelung (``StatsPool``) gewichtet
sie mit den Frames, in denen der jeweilige Sprecher redet. pyannote kann diese
Mittelung für mehrere Plätze auf einmal (``forward_embedding`` mit Gewichten
der Form (Stapel, Plätze, Frames)). Hier läuft deshalb jedes Fenster nur
EINMAL durch das Netz -- und Fenster ohne Sprache gar nicht.

Leere Plätze bekommen denselben Abdruck wie bei pyannote: bei Gewicht null
liefert die Mittelung exakt 0, danach folgt eine feste Rechnung; das Ergebnis
hängt nicht von der Aufnahme ab. pyannote wirft diese Plätze ohnehin weg
(``filter_embeddings``, ``hard_clusters[inactive_speakers] = -2``).

Abweichung zum Original: nur Rundung in der achten Nachkommastelle, weil die
Rechenstapel anders zusammengesetzt sind -- dieselbe Schwankung, die auch das
Original je nach Stapelgröße zeigt. ``traudi --selftest`` vergleicht beide
Wege an der Beispielaufnahme von pyannote und schlägt fehl, wenn sich die
Sprecherzuordnung unterscheidet.

Gilt nur für pyannote.audio 4.0.x -- für diese Fassung ist der Ersatz von
``get_embeddings`` geschrieben. Bei jeder anderen bleibt alles beim Original.
Andere Abdruck-Modelle als WeSpeaker-ResNet: ein Durchlauf je besetztem Platz.
"""

import math
import types

SUPPORTED_PREFIX = '4.0.'


def supported_version(version: str) -> bool:
    return str(version).startswith(SUPPORTED_PREFIX)


def active_slots(data):
    """(Fenster, Plätze) -> True, wo im Fenster jemand auf dem Platz spricht.

    `data` ist die binarisierte Segmentierung, Form (Fenster, Frames, Plätze);
    NaN zählt wie bei pyannote als 0.
    """
    import numpy as np
    return np.any(np.nan_to_num(data, nan=0.0) != 0, axis=1)


def install(pipeline, log=None) -> bool:
    """Ersetzt `pipeline.get_embeddings` -- nur bei passender pyannote-Fassung.

    Gibt zurück, ob der Ersatz aktiv ist.
    """
    try:
        import pyannote.audio
        version = pyannote.audio.__version__
    except Exception:
        version = '?'
    needed = ('get_embeddings', '_embedding', '_audio', 'embedding_batch_size')
    if not supported_version(version) or not all(hasattr(pipeline, a) for a in needed):
        if log:
            log(f'Embedding-Abkürzung aus (pyannote.audio {version} nicht unterstützt)')
        return False
    pipeline._traudi_original_get_embeddings = pipeline.get_embeddings
    pipeline.get_embeddings = types.MethodType(get_embeddings_skipping_silence, pipeline)
    if log:
        log(f'Embedding-Abkürzung aktiv (pyannote.audio {version})')
    return True


def uninstall(pipeline) -> None:
    original = getattr(pipeline, '_traudi_original_get_embeddings', None)
    if original is not None:
        pipeline.get_embeddings = original
        del pipeline._traudi_original_get_embeddings


def _chunkwise_model(embedding):
    """Das Netz hinter `embedding`, wenn es Merkmale und Mittelung getrennt
    anbietet (WeSpeaker-ResNet aus pyannote.audio 4) -- sonst None."""
    model = getattr(embedding, 'model_', None)
    if model is None:
        return None
    if not all(hasattr(model, a) for a in ('forward_frames', 'forward_embedding')):
        return None
    resnet = getattr(model, 'resnet', None)
    if resnet is None or getattr(resnet, 'two_emb_layer', True):
        # Mit zweiter Ausgabeschicht (BatchNorm) ginge die Form
        # (Stapel, Plätze, Merkmale) nicht durch.
        return None
    return model


def get_embeddings_skipping_silence(self, file, binary_segmentations,
                                    exclude_overlap: bool = False, hook=None):
    """Wie ``SpeakerDiarization.get_embeddings`` aus pyannote.audio 4.0, aber

    1. ohne Rechnung für Fenster, in denen niemand spricht, und
    2. bei WeSpeaker-Modellen mit EINEM Netzdurchlauf je Fenster statt einem je
       Platz: Das Netz sieht ohnehin das ganze 10-Sekunden-Fenster; der Platz
       wirkt erst beim abschließenden Mitteln (`StatsPool`), und das kann
       pyannote für mehrere Plätze auf einmal (`forward_embedding` mit
       Gewichten der Form (Stapel, Plätze, Frames)).

    Bei anderen Modellen: ein Durchlauf je besetztem Platz.
    """
    import numpy as np
    import torch
    from einops import rearrange
    from pyannote.core import SlidingWindowFeature

    if self.training:
        # Beim Training des Modells: unverändert (dort gibt es einen Cache).
        return self._traudi_original_get_embeddings(
            file, binary_segmentations, exclude_overlap=exclude_overlap, hook=hook)

    duration = binary_segmentations.sliding_window.duration
    num_chunks, num_frames, num_speakers = binary_segmentations.data.shape

    if exclude_overlap:
        min_num_samples = self._embedding.min_num_samples
        num_samples = duration * self._embedding.sample_rate
        min_num_frames = math.ceil(num_frames * min_num_samples / num_samples)
        clean_frames = 1.0 * (
            np.sum(binary_segmentations.data, axis=2, keepdims=True) < 2
        )
        clean_segmentations = SlidingWindowFeature(
            binary_segmentations.data * clean_frames,
            binary_segmentations.sliding_window,
        )
    else:
        min_num_frames = -1
        clean_segmentations = SlidingWindowFeature(
            binary_segmentations.data, binary_segmentations.sliding_window
        )

    # Welche Plätze sind besetzt? Gerechnet wird mit `mask` oder dem Teil
    # `clean_mask` davon; beide sind genau dann ganz null, wenn `mask` es ist.
    active = active_slots(binary_segmentations.data)
    active_chunks = active.any(axis=1)
    model = _chunkwise_model(self._embedding)
    batch_size = self.embedding_batch_size

    def iter_chunks():
        """(Fenster-Nr., Ausschnitt (1, Samples), Gewichte (Plätze, Frames))
        für jedes Fenster mit mindestens einem besetzten Platz -- Gewichte
        genau wie bei pyannote gewählt."""
        for c, ((chunk, masks), (_, clean_masks)) in enumerate(
            zip(binary_segmentations, clean_segmentations)
        ):
            if not active_chunks[c]:
                continue
            waveform, _ = self._audio.crop(file, chunk, mode="pad")
            masks = np.nan_to_num(masks, nan=0.0).astype(np.float32)
            clean_masks = np.nan_to_num(clean_masks, nan=0.0).astype(np.float32)
            used = np.empty((num_speakers, num_frames), dtype=np.float32)
            for s, (mask, clean_mask) in enumerate(zip(masks.T, clean_masks.T)):
                used[s] = clean_mask if np.sum(clean_mask) > min_num_frames else mask
            yield c, waveform, used

    if model is not None:
        def items():
            for c, waveform, used in iter_chunks():
                yield [c * num_speakers + s for s in range(num_speakers)], waveform, used

        def compute(waveforms, weights):
            device = self._embedding.device
            with torch.inference_mode():
                frames = model.forward_frames(torch.vstack(waveforms).to(device))
                emb = model.forward_embedding(frames, weights=torch.stack(weights).to(device))
            return emb.cpu().numpy().reshape(-1, emb.shape[-1])
        passes = int(active_chunks.sum())
    else:
        def items():
            for c, waveform, used in iter_chunks():
                for s in range(num_speakers):
                    if active[c, s]:
                        yield [c * num_speakers + s], waveform, used[s]

        def compute(waveforms, weights):
            return self._embedding(torch.vstack(waveforms), masks=torch.stack(weights))
        passes = int(active.sum())

    # Für den Selbsttest und das Protokoll: Netzdurchläufe statt pyannotes.
    self.traudi_passes = (passes, num_chunks * num_speakers)

    # Der Fortschritt zählt nur die Stapel, die wirklich gerechnet werden.
    batch_count = math.ceil(passes / batch_size)
    if hook is not None:
        hook("embeddings", None, total=batch_count, completed=0)

    rows, results = [], []
    pending_rows, pending_w, pending_m = [], [], []
    done = 0
    first_waveform = None

    def run_batch():
        nonlocal done
        embedding_batch = compute(pending_w, pending_m)
        rows.extend(pending_rows)
        results.append(embedding_batch)
        pending_rows.clear()
        pending_w.clear()
        pending_m.clear()
        done += 1
        if hook is not None:
            hook("embeddings", embedding_batch, total=batch_count, completed=done)

    for row, waveform, weights in items():
        if first_waveform is None:
            first_waveform = waveform
        pending_rows.extend(row)
        pending_w.append(waveform[None])
        pending_m.append(torch.from_numpy(weights))
        if len(pending_w) == batch_size:
            run_batch()
    if pending_w:
        run_batch()

    # Der Abdruck für leere Plätze -- so gerechnet, wie pyannote es für jeden
    # einzelnen davon getan hätte (Ausschnitt mit Gewicht null).
    if first_waveform is None:
        first_waveform = torch.zeros(1, int(round(duration * self._embedding.sample_rate)))
    silent = self._embedding(first_waveform[None],
                             masks=torch.zeros(1, num_frames, dtype=torch.float32))[0]

    flat = np.empty((num_chunks * num_speakers, silent.shape[-1]), dtype=silent.dtype)
    flat[:] = silent
    if results:
        flat[np.asarray(rows)] = np.vstack(results)
    return rearrange(flat, "(c s) d -> c s d", c=num_chunks)
