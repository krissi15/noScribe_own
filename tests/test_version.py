"""Die Versionsnummer darf nur an einer Stelle stehen.

Anlass: `pyinstaller/noScribe_macOS.spec` stand auf 0.7.1, während die
Anwendung 0.7.2 war. Solche Abweichungen fallen sonst erst beim Bau auf --
oder gar nicht.
"""

import re
import tomllib

from conftest import load_module


def test_version_looks_like_a_version(version_module):
    assert re.fullmatch(r'\d+\.\d+(\.\d+)?', version_module.__version__)


def test_pyproject_takes_the_version_from_the_module(root):
    data = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf-8'))
    project = data['project']
    assert 'version' not in project, (
        'pyproject.toml darf keine eigene Version festschreiben -- sonst gibt '
        'es wieder zwei Quellen.')
    assert 'version' in project.get('dynamic', [])
    attr = data['tool']['setuptools']['dynamic']['version']['attr']
    assert attr == 'noScribe._version.__version__'


def test_win_build_reads_the_same_version(version_module, monkeypatch, root):
    win_build = load_module('pyinstaller/win_build.py', '_traudi_test_win_build')
    assert win_build.app_version() == version_module.__version__


def test_no_spec_file_hardcodes_a_version(root):
    """Die Specs sollen die Version lesen, nicht wiederholen."""
    for spec in sorted((root / 'pyinstaller').glob('*.spec')):
        text = spec.read_text(encoding='utf-8')
        for match in re.finditer(r'["\'](\d+\.\d+\.\d+)["\']', text):
            raise AssertionError(
                f'{spec.name} enthält die feste Version {match.group(1)}. '
                f'Bitte aus noScribe/_version.py lesen.')


def test_nsis_version_has_four_segments():
    win_build = load_module('pyinstaller/win_build.py', '_traudi_test_win_build2')
    assert win_build.format_version('0.7.3') == '0.7.3.0'
    assert win_build.format_version('1.2.3.4') == '1.2.3.4'
    assert win_build.format_version('1.2') == '1.2.0.0'
