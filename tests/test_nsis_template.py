"""Die NSIS-Vorlage und win_build.py müssen zusammenpassen.

Ein vergessener Platzhalter oder eine fehlende Icon-Definition fällt sonst
erst auf, wenn der Installer-Bau nach dem kompletten PyInstaller-Lauf
abbricht -- oder gar nicht, weil das Ergebnis nur hässlich statt kaputt ist.
"""

import re

import pytest

PLACEHOLDER = re.compile(r'#\*([a-z_]+)\*#')


@pytest.fixture(scope='module')
def template(root):
    return (root / 'pyinstaller' / 'nsis_template.txt').read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def build_source(root):
    return (root / 'pyinstaller' / 'win_build.py').read_text(encoding='utf-8')


def test_every_placeholder_is_substituted(template, build_source):
    """Sonst landet ein `#*...*#` woertlich im erzeugten Skript."""
    in_template = set(PLACEHOLDER.findall(template))
    substituted = set(PLACEHOLDER.findall(build_source))
    missing = in_template - substituted
    assert not missing, f'win_build.py ersetzt diese Platzhalter nicht: {sorted(missing)}'


def test_no_substitution_without_a_placeholder(template, build_source):
    in_template = set(PLACEHOLDER.findall(template))
    substituted = set(PLACEHOLDER.findall(build_source))
    # Der Test selbst bringt keine Platzhalter mit; alles, was win_build.py
    # ersetzt, muss auch in der Vorlage vorkommen.
    orphaned = substituted - in_template
    assert not orphaned, f'win_build.py ersetzt unbekannte Platzhalter: {sorted(orphaned)}'


def test_installer_and_uninstaller_carry_the_logo(template):
    assert '!define MUI_ICON' in template
    assert '!define MUI_UNICON' in template
    # MUI wertet die Definitionen beim Einfuegen der Seiten aus.
    assert template.index('!define MUI_ICON') < template.index('!insertmacro MUI_PAGE_WELCOME')


def test_elevation_is_requested_explicitly(template):
    """Ohne diese Zeile entscheidet Windows anhand des Dateinamens, und diese
    Heuristik laesst sich per Gruppenrichtlinie abschalten."""
    assert 'RequestExecutionLevel admin' in template


def test_shortcuts_are_machine_wide(template):
    """Dateien und Registry liegen maschinenweit -- die Verknuepfungen auch,
    sonst sieht Traudi nur der installierende Administrator."""
    assert '!define INSTALL_TYPE "SetShellVarContext all"' in template


def test_there_is_a_desktop_shortcut(template):
    assert '$DESKTOP\\${APP_NAME}.lnk' in template
    # ... und sie muss beim Deinstallieren wieder verschwinden.
    assert 'Delete "$DESKTOP\\${APP_NAME}.lnk"' in template


def test_unattended_uninstall_is_possible(template):
    """Zentrale Softwareverteilung braucht das zum Zurueckrollen."""
    assert 'QuietUninstallString' in template


def test_display_version_is_the_real_version(template):
    """VERSION ist vierstellig (VIProductVersion verlangt das). Wuerde
    DisplayVersion daraus gespeist, stuende in der Registry "0.7.3.0", waehrend
    eine Erkennungsregel der Softwareverteilung gegen "0.7.3" prueft."""
    line = next(l for l in template.splitlines() if '"DisplayVersion"' in l)
    assert '${DISPLAY_VERSION}' in line, line
    assert '${VERSION}' not in line, line


def test_the_wizard_starts_in_german(template):
    german = template.index('!insertmacro MUI_LANGUAGE "German"')
    english = template.index('!insertmacro MUI_LANGUAGE "English"')
    assert german < english, 'Die erste MUI_LANGUAGE ist die Vorgabe.'


def test_format_version_always_has_four_segments():
    from conftest import load_module
    win_build = load_module('pyinstaller/win_build.py', '_traudi_test_nsis_build')
    for value in ('0.7.3', '1.2', '1.2.3.4'):
        assert len(win_build.format_version(value).split('.')) == 4


class TestSixtyFourBit:
    """Bis 0.7.6 baute makensis einen reinen 32-Bit-Installer: Traudi lag in
    "C:\\Program Files (x86)", die Registry unter WOW6432Node, und die
    Erkennungsregel aus dem README fand die Installation nicht."""

    def test_installs_into_the_64_bit_program_folder(self, template):
        assert 'InstallDir "$PROGRAMFILES64\\Traudi"' in template
        assert 'InstallDir "$PROGRAMFILES\\Traudi"' not in template

    def test_no_install_dir_from_the_32_bit_registry(self, template):
        """InstallDirRegKey laeuft vor .onInit in der 32-Bit-Ansicht und
        wuerde den alten (x86)-Ordner wieder vorschlagen."""
        code = [l for l in template.splitlines() if not l.lstrip().startswith(';')]
        assert not any('InstallDirRegKey' in l for l in code)

    def test_registry_view_is_64_bit_for_install_and_uninstall(self, template):
        assert '!include "x64.nsh"' in template
        for function in ('Function .onInit', 'Function un.onInit'):
            body = template.split(function, 1)[1].split('FunctionEnd', 1)[0]
            assert 'SetRegView 64' in body, function

    def test_refuses_32_bit_windows(self, template):
        body = template.split('Function .onInit', 1)[1].split('FunctionEnd', 1)[0]
        assert '${IfNot} ${RunningX64}' in body and 'Abort' in body

    def test_removes_a_legacy_32_bit_installation_first(self, template):
        section = template.split('Section -MainProgram', 1)[1]
        legacy = section.index('SetRegView 32')
        assert section.index('ExecWait', legacy) < section.index('#*install_entries*#')
        # ... und kehrt danach in die 64-Bit-Ansicht zurueck.
        assert 'SetRegView 64' in section[legacy:section.index('legacyDone:')]
