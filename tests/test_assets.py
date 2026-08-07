"""Jeder im Code oder im Bau referenzierte Bildpfad muss existieren.

Ein fehlendes Icon fällt sonst erst auf, wenn der Installer fertig gebaut ist
oder -- schlimmer -- wenn die Anwendung beim Start darüber stolpert.
"""

import re

import pytest

# Pfade der Form '../img/xyz.png' in den Specs, 'img' / "datei.ico" im Code.
SPEC_PATH = re.compile(r'["\']\.\./(img/[\w./-]+)["\']')


def test_the_logo_assets_exist(root):
    for name in ('traudi_logo.ico', 'traudi_logo.png'):
        assert (root / 'img' / name).is_file(), f'img/{name} fehlt'


def test_readme_screenshots_exist(root):
    readme = (root / 'README.md').read_text(encoding='utf-8')
    for match in re.finditer(r'!\[[^\]]*\]\(([^)]+)\)', readme):
        target = match.group(1)
        if target.startswith('http'):
            continue
        assert (root / target).is_file(), f'README verweist auf {target}'


def test_spec_files_only_reference_existing_images(root):
    for spec in sorted((root / 'pyinstaller').glob('*.spec')):
        text = spec.read_text(encoding='utf-8')
        for match in SPEC_PATH.finditer(text):
            target = root / match.group(1)
            assert target.is_file(), f'{spec.name} verweist auf {match.group(1)}'


def test_main_references_the_bundled_icon_names(root):
    """Die Namen in main.py müssen zu den Dateien in img/ passen."""
    source = (root / 'noScribe' / 'main.py').read_text(encoding='utf-8')
    for name in re.findall(r'"(traudi_logo\.\w+)"', source):
        assert (root / 'img' / name).is_file(), f'main.py verweist auf img/{name}'
