"""Die Sprechererkennung liest ihre Eingabe ohne torchaudio.

Anlass: Im Windows-Paket scheiterte ``torchaudio.load`` an jeder Datei --
ab torchaudio 2.8 hängt es an torchcodec, und das findet im Paket seine DLLs
nicht:

    RuntimeError: Couldn't find appropriate backend to handle uri
    ...\\selftest.wav and format None.

``read_pcm_wav`` liest stattdessen das, was ``audio/convert.py`` immer
schreibt (PCM, 16 Bit, 16 kHz, mono), und liefert dieselbe Form wie
``torchaudio.load``: float32 zwischen -1 und 1, (Kanäle, Frames).
"""

import wave

import pytest

np = pytest.importorskip('numpy')

from conftest import load_module

worker = load_module('noScribe/pyannote_mp_worker.py')


def write_wav(path, samples, channels, rate=16000, width=2):
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(width)
        wav.setframerate(rate)
        wav.writeframes(samples.tobytes())


def test_mono_matches_torchaudio_conventions(tmp_path):
    pcm = np.array([0, 16384, -16384, 32767, -32768], dtype='<i2')
    write_wav(tmp_path / 'a.wav', pcm, channels=1)

    samples, rate = worker.read_pcm_wav(tmp_path / 'a.wav')

    assert rate == 16000
    assert samples.dtype == np.float32
    assert samples.shape == (1, 5)
    np.testing.assert_allclose(samples[0], [0.0, 0.5, -0.5, 32767 / 32768, -1.0])


def test_stereo_is_split_into_channels(tmp_path):
    # Verschränkt: L0 R0 L1 R1 ...
    pcm = np.array([1000, -1000, 2000, -2000, 3000, -3000], dtype='<i2')
    write_wav(tmp_path / 's.wav', pcm, channels=2, rate=44100)

    samples, rate = worker.read_pcm_wav(tmp_path / 's.wav')

    assert rate == 44100
    assert samples.shape == (2, 3)
    np.testing.assert_allclose(samples[0] * 32768, [1000, 2000, 3000])
    np.testing.assert_allclose(samples[1] * 32768, [-1000, -2000, -3000])


def test_other_sample_widths_are_rejected(tmp_path):
    write_wav(tmp_path / 'u8.wav', np.zeros(4, dtype=np.uint8), channels=1, width=1)
    with pytest.raises(ValueError, match='16-Bit'):
        worker.read_pcm_wav(tmp_path / 'u8.wav')


def test_worker_no_longer_calls_torchaudio_load(root):
    source = (root / 'noScribe' / 'pyannote_mp_worker.py').read_text(encoding='utf-8')
    assert 'torchaudio.load(' not in source
