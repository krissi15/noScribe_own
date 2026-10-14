"""Wo die mitgelieferten Diarisierungs-Gewichte liegen.

Anlass: ``resolve_pyannote_dir()`` gab einen Pfad zurück, den
``importlib.resources.as_file`` in einem temporären Verzeichnis angelegt
hatte -- ``files("pyannote")`` trifft auf das Namespace-Paket der
pyannote-Bibliotheken, und für so etwas kopiert ``as_file``. Beim Verlassen
des ``with`` war der Ordner wieder gelöscht. pyannote hielt den toten Pfad
für einen HuggingFace-Namen:

    HFValidationError: Repo id must use alphanumeric chars ...:
    'C:\\Users\\RUNNER~1\\AppData\\Local\\Temp\\tmp6h3cqz6y\\pyannote'

Gefunden hat das erst ``Traudi.exe --selftest`` im Windows-Bau.
"""

import sys

from conftest import load_module


def test_source_tree_points_at_the_versioned_folder(root, monkeypatch):
    monkeypatch.delattr(sys, '_MEIPASS', raising=False)
    model_download = load_module('noScribe/model_download.py')
    folder = model_download.bundled_pyannote_dir()
    assert folder == root / 'pyannote'
    assert (folder / 'config.yaml').is_file()


def test_frozen_build_points_into_meipass(tmp_path, monkeypatch):
    """Die .spec legt den Ordner nach _MEIPASS/pyannote."""
    monkeypatch.setattr(sys, '_MEIPASS', str(tmp_path), raising=False)
    model_download = load_module('noScribe/model_download.py')
    assert model_download.bundled_pyannote_dir() == tmp_path / 'pyannote'


def test_spec_puts_the_folder_where_the_lookup_expects_it(root):
    spec = (root / 'pyinstaller' / 'noScribe_win.spec').read_text(encoding='utf-8')
    assert "('../pyannote/', './pyannote/')" in spec


def test_main_does_not_resolve_the_folder_through_importlib_resources(root):
    source = (root / 'noScribe' / 'main.py').read_text(encoding='utf-8')
    assert 'impres.files("pyannote")' not in source, (
        'files("pyannote") ist ein Namespace-Paket; as_file liefert dafür eine '
        'temporäre Kopie, die nach dem with gelöscht ist. '
        'model_download.bundled_pyannote_dir() benutzen.')
