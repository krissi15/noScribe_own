"""Der Windows-CPU-Bau installiert festgeschriebene Fassungen.

Anlass: faster-whisper, av und pyannote.audio (>=4.0) waren offen; jeder Bau
konnte andere Fassungen ausliefern. Die Abkürzung der Sprechererkennung
(diarization_speed.py) gilt nur für pyannote.audio 4.0.x -- eine 4.1 hätte
sie still abgeschaltet.
"""

import re

import pytest


@pytest.fixture(scope='module')
def pins(root):
    pins = {}
    for line in (root / 'environments' / 'constraints_win_cpu.txt').read_text(
            encoding='utf-8').splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        name, _, version = line.partition('==')
        assert version, f'nicht exakt festgelegt: {line}'
        pins[re.sub(r'[-_.]+', '-', name).lower()] = version
    return pins


@pytest.mark.parametrize('name', ['faster-whisper', 'av', 'pyannote-audio', 'torch',
                                  'torchaudio', 'ctranslate2', 'pyinstaller', 'pyqt6'])
def test_key_packages_are_pinned(pins, name):
    assert name in pins


def test_pyannote_is_the_version_the_speedup_was_written_for(pins, root):
    speed = (root / 'noScribe' / 'diarization_speed.py').read_text(encoding='utf-8')
    prefix = re.search(r"SUPPORTED_PREFIX = '([^']+)'", speed).group(1)
    assert pins['pyannote-audio'].startswith(prefix)


def test_pyinstaller_pin_matches_requirements(pins, root):
    req = (root / 'environments' / 'requirements_win_cpu.txt').read_text(encoding='utf-8')
    assert f"pyinstaller=={pins['pyinstaller']}" in req


def test_torch_is_the_cpu_build(pins):
    assert pins['torch'].endswith('+cpu')
    assert pins['torchaudio'].endswith('+cpu')


def test_runner_tools_are_not_pinned(pins):
    for tool in ('pip', 'setuptools', 'pipx'):
        assert tool not in pins


def test_build_uses_the_constraints(root):
    workflow = (root / '.github' / 'workflows' / 'build-windows.yml').read_text(encoding='utf-8')
    assert 'environments/constraints_win_$env:VARIANT.txt' in workflow
    assert workflow.count('@pins') >= 3
