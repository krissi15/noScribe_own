"""Der Windows-Bau muss mit genau einer PyInstaller-Version laufen.

Anlass: Traudi 0.7.4 startete nicht. Der Bau installiert erst
`environments/requirements_win_*.txt` (``pyinstaller==6.14.1``) und danach die
Liste des Editors -- die stand auf ``pyinstaller<=6.4.0`` und stufte damit
die gemeinsame Umgebung herunter. 6.4.0 packt die jaraco-Pakete nicht ein,
die neuere setuptools-Fassungen nur noch intern mitliefern, und das Programm
brach im Laufzeit-Hook ab, bevor eine einzige Zeile von Traudi lief:

    File "pkg_resources/__init__.py", line 90, in <module>
    ModuleNotFoundError: No module named 'jaraco'

Kein Test sah das, weil beide Listen für sich genommen gültig waren.
"""

import re

import pytest

# Was build-windows.yml in dieselbe Umgebung installiert.
WINDOWS_BUILD_REQUIREMENTS = [
    'environments/requirements_win_cpu.txt',
    'environments/requirements_win_cuda.txt',
    'noScribeEdit/environments/requirements.txt',
]


def pyinstaller_requirement(path) -> str:
    lines = [
        line.split('#', 1)[0].strip()
        for line in path.read_text(encoding='utf-8').splitlines()
    ]
    found = [line for line in lines if re.match(r'(?i)pyinstaller\b(?!-)', line)]
    assert len(found) == 1, f'{path.name}: genau eine pyinstaller-Zeile erwartet, gefunden {found}'
    return found[0]


@pytest.mark.parametrize('relative', WINDOWS_BUILD_REQUIREMENTS)
def test_pyinstaller_is_pinned_exactly(root, relative):
    """Ein Bereich wie ``<=6.4.0`` lässt offen, welche Fassung am Ende gilt."""
    requirement = pyinstaller_requirement(root / relative)
    assert re.fullmatch(r'(?i)pyinstaller==\d+(\.\d+)*', requirement), (
        f'{relative}: PyInstaller muss mit == festgelegt sein, steht auf {requirement!r}')


def test_all_windows_build_lists_agree_on_pyinstaller(root):
    pins = {relative: pyinstaller_requirement(root / relative)
            for relative in WINDOWS_BUILD_REQUIREMENTS}
    assert len({pin.lower() for pin in pins.values()}) == 1, (
        'Die Listen, die der Windows-Bau in eine Umgebung installiert, '
        f'verlangen verschiedene PyInstaller-Fassungen: {pins}')


def test_workflow_installs_exactly_these_lists(root):
    """Kommt eine Liste dazu, muss sie auch oben in die Prüfung."""
    workflow = (root / '.github' / 'workflows' / 'build-windows.yml').read_text(encoding='utf-8')
    installed = set(re.findall(r'pip install -r (\S+)', workflow))
    expected = {'environments/requirements_win_$env:VARIANT.txt',
                'noScribeEdit/environments/requirements.txt'}
    assert installed == expected, (
        f'build-windows.yml installiert {sorted(installed)}; '
        'WINDOWS_BUILD_REQUIREMENTS in diesem Test anpassen.')
