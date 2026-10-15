"""Die Rechenprozesse dürfen von Windows nicht als Hintergrundarbeit gedrosselt
werden (Power Throttling/EcoQoS, auf Hybrid-CPUs: Effizienzkerne)."""

import platform

import pytest

from conftest import load_module

tuning = load_module('noScribe/proc_tuning.py')


@pytest.mark.parametrize('value, expected', [
    (8, 8), ('4', 4), (0, None), (-1, None), ('auto', None), (None, None), ('', None),
])
def test_thread_count(value, expected):
    assert tuning.thread_count(value) == expected


@pytest.mark.skipif(platform.system() == 'Windows', reason='nur außerhalb von Windows')
def test_power_throttling_is_a_no_op_elsewhere():
    assert tuning.disable_power_throttling() is False


@pytest.mark.skipif(platform.system() != 'Windows', reason='nur unter Windows')
def test_power_throttling_is_accepted_on_windows():
    assert tuning.disable_power_throttling() is True


def test_both_workers_opt_out_of_throttling(root):
    for name in ('whisper_mp_worker.py', 'pyannote_mp_worker.py'):
        source = (root / 'noScribe' / name).read_text(encoding='utf-8')
        assert 'disable_power_throttling()' in source, name


def test_diarization_gets_the_thread_count(root):
    source = (root / 'noScribe' / 'main.py').read_text(encoding='utf-8')
    assert '"threads": number_threads' in source
    worker = (root / 'noScribe' / 'pyannote_mp_worker.py').read_text(encoding='utf-8')
    assert 'torch.set_num_threads(threads)' in worker
