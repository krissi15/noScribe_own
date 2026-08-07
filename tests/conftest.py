"""Gemeinsame Hilfen für die Testsuite.

Die Tests laufen bewusst ohne torch, ohne Modellgewichte und ohne GUI, damit
sie in der CI in Sekunden durchlaufen. `noScribe/__init__.py` importiert
`noScribe.main` und damit faster-whisper -- ein schlichtes
``from noScribe import utils`` würde den gesamten Modellstapel nachziehen.
Deshalb werden einzelne Module hier direkt über ihren Dateipfad geladen.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def load_module(relative_path: str, name: str | None = None):
    """Lädt ein Modul über seinen Pfad, ohne das Paket `noScribe` zu berühren."""
    path = ROOT / relative_path
    name = name or ('_traudi_test_' + path.stem)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'Konnte {path} nicht laden')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='session')
def root() -> Path:
    return ROOT


@pytest.fixture(scope='session')
def utils():
    return load_module('noScribe/utils.py')


@pytest.fixture(scope='session')
def version_module():
    return load_module('noScribe/_version.py')
