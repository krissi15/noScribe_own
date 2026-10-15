"""Der Editor darf beim Speichern nichts verlieren.

Anlass: `open(path, 'w')` leerte die Datei, bevor geschrieben wurde, und
`closeEvent` schloss das Fenster auch dann, wenn das Speichern scheiterte
(Datei in Word offen, Freigabe weg) -- alle Korrekturen waren verloren.
"""

import os

import pytest

from conftest import load_module

safe_save = load_module('noScribeEdit/safe_save.py', '_traudi_test_safe_save')


def test_writes_new_file(tmp_path):
    target = tmp_path / 'protokoll.html'
    safe_save.write_text_atomic(target, '<p>Zeugin Müller</p>')
    assert target.read_text(encoding='utf-8') == '<p>Zeugin Müller</p>'


def test_replaces_existing_file(tmp_path):
    target = tmp_path / 'protokoll.html'
    target.write_text('alt', encoding='utf-8')
    safe_save.write_text_atomic(target, 'neu')
    assert target.read_text(encoding='utf-8') == 'neu'


def test_original_survives_a_failed_save(tmp_path, monkeypatch):
    target = tmp_path / 'protokoll.html'
    target.write_text('korrigierte Fassung', encoding='utf-8')

    def locked(src, dst):
        raise PermissionError('in Word geöffnet')
    monkeypatch.setattr(safe_save.os, 'replace', locked)

    with pytest.raises(PermissionError):
        safe_save.write_text_atomic(target, 'neue Fassung')

    assert target.read_text(encoding='utf-8') == 'korrigierte Fassung'
    assert [p.name for p in tmp_path.iterdir()] == ['protokoll.html'], \
        'die Hilfsdatei muss wieder weg sein'


@pytest.mark.skipif(os.name == 'nt', reason='POSIX-Rechte')
def test_keeps_permissions(tmp_path):
    target = tmp_path / 'protokoll.html'
    target.write_text('alt', encoding='utf-8')
    target.chmod(0o644)
    safe_save.write_text_atomic(target, 'neu')
    assert (target.stat().st_mode & 0o777) == 0o644


def test_editor_uses_it_and_keeps_window_open_on_failure(root):
    source = (root / 'noScribeEdit' / 'noScribeEdit.py').read_text(encoding='utf-8')
    assert 'write_text_atomic(path, file_txt)' in source
    assert "with open(path, 'w'" not in source
    # closeEvent und file_open: nur weiter, wenn wirklich gesichert
    assert source.count('if not self.file_save():') == 2
    assert 'dlg.exec()' in source.split('def dialog_critical', 1)[1].split('def ', 1)[0]
