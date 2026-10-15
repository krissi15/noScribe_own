"""Die Abkürzung für leere Sprecherplätze muss dasselbe liefern wie pyannote.

Anlass: Bei 1 h 14 min Aufnahme stand die Sprechererkennung nach zwei Stunden
bei "Embeddings 69 %". pyannote rechnet für jedes Fenster drei Plätze, auch
leere; deren Stimmabdruck ist immer derselbe.

Der Vergleich hier ruft pyannotes eigenes ``get_embeddings`` und den Ersatz
mit demselben Modell auf: einem Spielzeug (Weg "je besetzter Platz") und dem
echten WeSpeaker-ResNet34 mit Zufallsgewichten (Weg "ein Durchlauf je
Fenster"). Er läuft nur, wo torch und pyannote
installiert sind (lokal, nicht im schlanken CI-Lauf); im Windows-Bau prüft
``Traudi.exe --selftest`` dasselbe mit dem echten Modell.
"""

import math
from types import SimpleNamespace

import pytest

np = pytest.importorskip('numpy')

from conftest import load_module

speed = load_module('noScribe/diarization_speed.py')


def test_only_the_version_the_replacement_was_written_for():
    assert speed.supported_version('4.0.7')
    assert speed.supported_version('4.0.0')
    assert not speed.supported_version('4.1.0')
    assert not speed.supported_version('3.3.2')


def test_active_slots_treats_nan_as_silence():
    data = np.zeros((2, 4, 3))
    data[0, 1, 0] = 1
    data[1, :, 2] = np.nan
    data[1, 3, 1] = 1
    assert speed.active_slots(data).tolist() == [[True, False, False],
                                                 [False, True, False]]


# --- Vergleich mit pyannote ---------------------------------------------------

SR = 160          # Abtastrate des Spielzeugs
FRAMES = 10       # Frames je Fenster
DURATION = 1.0    # Fensterlänge in s -> 160 Samples, 16 je Frame
DIM = 4


class ToyEmbedding:
    """Verhält sich wie das echte Modell, wo es darauf ankommt: gewichtetes
    Mittel über Frames, bei Gewicht null exakt 0, danach eine feste Rechnung.
    Jede Zeile wird einzeln gerechnet, damit die Stapelgröße nichts ändert."""

    sample_rate = SR
    min_num_samples = 32
    dimension = DIM

    def __init__(self):
        rng = np.random.default_rng(1)
        self.w = rng.standard_normal((2, DIM)).astype(np.float32)
        self.b = rng.standard_normal(DIM).astype(np.float32)
        self.calls = []

    def __call__(self, waveforms, masks=None):
        waveforms = waveforms.numpy()
        masks = masks.numpy()
        self.calls.append(masks.copy())
        out = []
        for wav, m in zip(waveforms, masks):
            frames = wav[0].reshape(FRAMES, -1)
            feats = np.stack([frames.mean(axis=1), np.abs(frames).mean(axis=1)], axis=1)
            pooled = (feats * m[:, None]).sum(axis=0) / (m.sum() + 1e-8)
            out.append(np.tanh(pooled @ self.w + self.b))
        return np.stack(out).astype(np.float32)


class ToyAudio:
    def crop(self, file, segment, mode='pad'):
        import torch
        start = int(round(segment.start * SR))
        wav = file['waveform'][:, start:start + int(DURATION * SR)]
        if wav.shape[1] < DURATION * SR:
            wav = torch.nn.functional.pad(wav, (0, int(DURATION * SR) - wav.shape[1]))
        return wav, SR


def make_case(seed, num_chunks=23):
    torch = pytest.importorskip('torch')
    core = pytest.importorskip('pyannote.core')
    rng = np.random.default_rng(seed)
    data = (rng.random((num_chunks, FRAMES, 3)) > 0.6).astype(np.float32)
    data[:, :, 2] *= rng.random((num_chunks, 1)) > 0.7   # dritter Platz meist leer
    data[3] = 0                                          # Fenster ganz ohne Sprache
    data[5, 2:, :] = np.nan                              # angestückelt
    data[7, :, 0] = 1                                    # ein Platz durchgehend
    segs = core.SlidingWindowFeature(
        data, core.SlidingWindow(start=0.0, duration=DURATION, step=0.5))
    samples = (num_chunks + 2) * SR // 2 + SR
    file = {'waveform': torch.from_numpy(rng.standard_normal((1, samples)).astype(np.float32)),
            'sample_rate': SR}
    return file, segs


def fake_pipeline(batch_size):
    return SimpleNamespace(training=False, _embedding=ToyEmbedding(), _audio=ToyAudio(),
                           embedding_batch_size=batch_size)


@pytest.mark.parametrize('exclude_overlap', [True, False])
@pytest.mark.parametrize('batch_size', [1, 3, 32])
@pytest.mark.parametrize('seed', [0, 1, 2])
def test_same_embeddings_as_pyannote(exclude_overlap, batch_size, seed):
    sd = pytest.importorskip('pyannote.audio.pipelines.speaker_diarization')
    file, segs = make_case(seed)

    original = fake_pipeline(batch_size)
    expected = sd.SpeakerDiarization.get_embeddings(
        original, file, segs, exclude_overlap=exclude_overlap)

    fast = fake_pipeline(batch_size)
    progress = []
    got = speed.get_embeddings_skipping_silence(
        fast, file, segs, exclude_overlap=exclude_overlap,
        hook=lambda step, art, total=None, completed=None: progress.append((total, completed)))

    assert got.shape == expected.shape == (segs.data.shape[0], 3, DIM)
    np.testing.assert_array_equal(got, expected)

    # Gerechnet wird nur für besetzte Plätze -- plus einmal der leere Abdruck.
    active = speed.active_slots(segs.data)
    rows = np.concatenate(fast._embedding.calls)
    assert len(rows) == active.sum() + 1
    assert (rows.sum(axis=1) == 0).sum() == 1
    assert fast.traudi_passes == (int(active.sum()), active.size)

    # Fortschritt: von 0 bis zur Zahl der wirklich gerechneten Stapel.
    total = math.ceil(active.sum() / batch_size)
    assert progress[0] == (total, 0)
    assert progress[-1] == (total, total)
    assert len(progress) == total + 1


def test_all_slots_empty():
    # pyannote selbst kommt hier nicht hin (es bricht vorher ab, wenn niemand
    # spricht); der Ersatz soll trotzdem nicht stolpern.
    pytest.importorskip('pyannote.audio')
    file, segs = make_case(0, num_chunks=8)
    segs.data[:] = 0
    pipeline = fake_pipeline(32)
    got = speed.get_embeddings_skipping_silence(pipeline, file, segs)
    assert got.shape == (8, 3, DIM)
    assert len(pipeline._embedding.calls) == 1
    np.testing.assert_array_equal(got, np.broadcast_to(got[0, 0], got.shape))


def test_install_only_on_supported_version(monkeypatch):
    pa = pytest.importorskip('pyannote.audio')
    pipeline = fake_pipeline(4)
    pipeline.get_embeddings = lambda *a, **k: 'original'
    monkeypatch.setattr(pa, '__version__', '4.1.0')
    assert speed.install(pipeline) is False
    assert pipeline.get_embeddings() == 'original'
    monkeypatch.setattr(pa, '__version__', '4.0.7')
    assert speed.install(pipeline) is True
    assert pipeline.get_embeddings.__func__ is speed.get_embeddings_skipping_silence
    speed.uninstall(pipeline)
    assert pipeline.get_embeddings() == 'original'


# --- echtes WeSpeaker-Netz, ein Durchlauf je Fenster -------------------------

def test_one_network_pass_per_window_with_wespeaker():
    torch = pytest.importorskip('torch')
    core = pytest.importorskip('pyannote.core')
    sd = pytest.importorskip('pyannote.audio.pipelines.speaker_diarization')
    from pyannote.audio.models.embedding import WeSpeakerResNet34
    from pyannote.audio.pipelines.speaker_verification import (
        PyannoteAudioPretrainedSpeakerEmbedding)

    torch.manual_seed(0)
    model = WeSpeakerResNet34()
    embedding = PyannoteAudioPretrainedSpeakerEmbedding(model, device=torch.device('cpu'))
    assert speed._chunkwise_model(embedding) is not None

    rate, duration, frames, chunks = 16000, 2.0, 50, 7
    rng = np.random.default_rng(3)
    data = (rng.random((chunks, frames, 3)) > 0.5).astype(np.float32)
    data[:, :, 2] = 0           # dritter Platz leer
    data[2] = 0                 # Fenster ohne Sprache
    data[4, :, 1] = 0           # nur ein Sprecher
    segs = core.SlidingWindowFeature(
        data, core.SlidingWindow(start=0.0, duration=duration, step=1.0))
    samples = int((chunks + 1) * rate)
    file = {'waveform': torch.from_numpy(
                (rng.standard_normal((1, samples)) * 0.1).astype(np.float32)),
            'sample_rate': rate}

    class Audio:
        def crop(self, file, segment, mode='pad'):
            start = int(round(segment.start * rate))
            return file['waveform'][:, start:start + int(duration * rate)], rate

    def pipeline():
        return SimpleNamespace(training=False, _embedding=embedding, _audio=Audio(),
                               embedding_batch_size=4)

    expected = sd.SpeakerDiarization.get_embeddings(pipeline(), file, segs,
                                                    exclude_overlap=True)
    fast = pipeline()
    got = speed.get_embeddings_skipping_silence(fast, file, segs, exclude_overlap=True)

    active = speed.active_slots(data)
    assert fast.traudi_passes == (int(active.any(axis=1).sum()), chunks * 3)
    # Leere Plätze: bitgleich. Besetzte: gleich bis auf Rundung -- die
    # Stapel sind anders zusammengesetzt, das ändert die letzte Stelle.
    np.testing.assert_array_equal(got[~active], expected[~active])
    np.testing.assert_allclose(got[active], expected[active], rtol=0, atol=1e-5)
