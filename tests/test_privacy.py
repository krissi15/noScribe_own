"""Was Traudi nicht nach außen geben und nicht liegen lassen darf.

Anlass: Die Prüfung vom Oktober 2026 fand,
- dass pyannote 4 bei jeder Sprechererkennung Nutzungsdaten an
  otel.pyannote.ai schickt (Voreinstellung der Bibliothek),
- dass jede Vernehmung als Klartext in einer nie gelöschten Logdatei landete,
- dass die WAV-Kopie einer Aufnahme nach Abbruch in %TEMP% liegen blieb,
- dass `force_pyannote_cpu: true` in der config.yml den Start wortlos
  verhinderte.
"""

import os
import subprocess
import sys
import time

import pytest

from conftest import load_module

privacy = load_module('noScribe/privacy.py')


def test_importing_the_package_switches_telemetry_off(root):
    """Auch gegen eine anderslautende Umgebung -- und vor jedem pyannote-Import,
    denn pyannote übernimmt seine Voreinstellung nur, wenn die Variable fehlt."""
    env = dict(os.environ, PYANNOTE_METRICS_ENABLED='true', PYTHONPATH=str(root))
    out = subprocess.run(
        [sys.executable, '-c',
         'import os, noScribe; print(os.environ["PYANNOTE_METRICS_ENABLED"], '
         'os.environ["HF_HUB_DISABLE_TELEMETRY"], os.environ["OTEL_SDK_DISABLED"])'],
        cwd=root, env=env, capture_output=True, text=True, check=True)
    assert out.stdout.split() == ['false', '1', 'true']


def test_workers_go_offline_first(root):
    for name in ('whisper_mp_worker.py', 'pyannote_mp_worker.py'):
        source = (root / 'noScribe' / name).read_text(encoding='utf-8')
        assert 'privacy.go_offline()' in source, name


def test_go_offline_blocks_hub_access(monkeypatch):
    monkeypatch.delenv('HF_HUB_OFFLINE', raising=False)
    privacy.go_offline()
    assert os.environ['HF_HUB_OFFLINE'] == '1'
    assert os.environ['PYANNOTE_METRICS_ENABLED'] == 'false'


@pytest.mark.parametrize('value, expected', [
    (True, True), (False, False), ('True', True), ('False', False),
    ('true', True), ('ja', True), ('nein', False), ('1', True), ('0', False),
    ('', False), (1, True), (0, False),
])
def test_as_bool_accepts_what_yaml_and_admins_write(value, expected):
    assert privacy.as_bool(value, default=not expected) is expected


def test_as_bool_falls_back_on_nonsense():
    assert privacy.as_bool('vielleicht', True) is True
    assert privacy.as_bool('vielleicht', False) is False


def test_remove_stale_keeps_fresh_and_removes_old(tmp_path):
    old_log = tmp_path / 'alt.log'
    new_log = tmp_path / 'neu.log'
    old_dir = tmp_path / 'tmpabc123noScribe'
    other = tmp_path / 'fremd.txt'
    for f in (old_log, new_log, other):
        f.write_text('x')
    old_dir.mkdir()
    (old_dir / 'tmp_audio.wav').write_bytes(b'RIFF')
    two_days_ago = time.time() - 48 * 3600
    for f in (old_log, old_dir, other):
        os.utime(f, (two_days_ago, two_days_ago))

    removed = privacy.remove_stale(tmp_path, '*.log', max_age_hours=24)
    removed += privacy.remove_stale(tmp_path, 'tmp*noScribe', max_age_hours=12)

    assert set(removed) == {old_log, old_dir}
    assert new_log.exists() and other.exists()
    assert not old_log.exists() and not old_dir.exists()


def test_remove_stale_tolerates_missing_directory(tmp_path):
    assert privacy.remove_stale(tmp_path / 'gibt-es-nicht', '*', 1) == []


def test_remove_tree(tmp_path):
    d = tmp_path / 'a' / 'b'
    d.mkdir(parents=True)
    (d / 'f').write_text('x')
    assert privacy.remove_tree(tmp_path / 'a')
    assert not (tmp_path / 'a').exists()
    assert privacy.remove_tree(tmp_path / 'a')  # schon weg ist auch gut


@pytest.fixture(scope='module')
def source(root):
    """main.py ist ohne GUI nicht importierbar; geprüft wird am Quelltext."""
    return (root / 'noScribe' / 'main.py').read_text(encoding='utf-8')


class TestMainSource:

    def test_transcript_text_goes_to_screen_only(self, source):
        assert "self.log(seg_text, where='screen')" in source
        assert "self.log(pause_str, where='screen')" in source
        assert 'self.log(seg_text)' not in source

    def test_log_file_is_not_named_after_the_transcript(self, source):
        assert "log/{Path(job.transcript_file).stem}.log" not in source

    def test_update_check_is_off_by_default(self, source):
        assert "get_flag('online_update_check', False)" in source
        assert "get_config('check_for_update', 'True')" not in source

    def test_old_logs_and_orphaned_audio_are_removed_at_start(self, source):
        assert "remove_stale(Path(config_dir) / 'log', '*.log'" in source
        assert "'tmp*noScribe'" in source
