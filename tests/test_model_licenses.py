"""Namensnennung für die Modelle (Prüfung C5).

Die Gewichte der Sprechererkennung (CC-BY-4.0) liegen im Installer. CC-BY
verlangt Urheber, Quelle und Lizenzhinweis; bisher nannte sie weder der
Über-Dialog noch eine Datei im Programmordner.
"""


def test_overview_names_every_bundled_model(root):
    text = (root / 'MODELLE_LIZENZEN.md').read_text(encoding='utf-8')
    for needle in ('speaker-diarization-community-1', 'wespeaker-voxceleb-resnet34-LM',
                   'BUT Speech@FIT', 'CC-BY-4.0', 'creativecommons.org/licenses/by/4.0',
                   'Copyright (c) 2022 OpenAI'):
        assert needle in text, needle


def test_overview_covers_the_whisper_sources_traudi_downloads(root):
    text = (root / 'MODELLE_LIZENZEN.md').read_text(encoding='utf-8')
    source = (root / 'noScribe' / 'model_download.py').read_text(encoding='utf-8')
    import re
    for repo in re.findall(r"repo_id='([^']+)'", source):
        assert repo in text, repo


def test_overview_ships_with_the_installer(root):
    spec = (root / 'pyinstaller' / 'noScribe_win.spec').read_text(encoding='utf-8')
    assert "'../MODELLE_LIZENZEN.md'" in spec


def test_about_dialog_names_the_model_licenses(root):
    about = (root / 'noScribe' / 'dialogs' / 'about.py').read_text(encoding='utf-8')
    assert 'CC-BY-4.0' in about
    assert 'MODELLE_LIZENZEN.md' in about
