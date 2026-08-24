"""Baut die Windows-Fassung von Traudi: PyInstaller, dann der NSIS-Installer.

    python pyinstaller/win_build.py              # CPU-Variante
    python pyinstaller/win_build.py --cuda       # CUDA-Variante
    python pyinstaller/win_build.py --skip-nsis  # nur den dist-Ordner bauen

Läuft mit dem Python, das das Skript startet -- also einfach die aktivierte
venv. NSIS wird über PATH gesucht (`choco install nsis`) oder über --nsis.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


def app_version() -> str:
    """Einzige Quelle der Version ist `__version__` in noScribe/_version.py.

    Bewusst per Regex und nicht per Import: ein `import noScribe` würde über
    das Paket-`__init__` main.py und damit torch/faster-whisper mitladen.
    """
    source = (PROJECT_ROOT / 'noScribe' / '_version.py').read_text(encoding='utf-8')
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', source, re.MULTILINE)
    if not match:
        raise SystemExit('Konnte __version__ nicht aus noScribe/_version.py lesen.')
    return match.group(1)


def find_nsis(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    found = shutil.which('makensis')
    if found:
        return Path(found)
    default = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'NSIS' / 'makensis.exe'
    if default.is_file():
        return default
    raise SystemExit('makensis wurde nicht gefunden. Installiere NSIS oder nutze --nsis.')


EDITOR_DIR = PROJECT_ROOT / 'noScribeEdit'
EDITOR_DIST = SCRIPT_DIR / 'dist' / 'editor'


def build_editor(clean: bool) -> Path:
    """Baut den Editor, damit der Hauptlauf ihn einpacken kann.

    Muss VOR run_pyinstaller() laufen: noScribe_win.spec bindet das Ergebnis
    ein, und `main.py` sucht zur Laufzeit eine fertige noScribeEdit.exe.

    Frueher gab es diesen Schritt nicht. Die Spec kopierte stattdessen das
    Quellverzeichnis, waehrend hier eine gebaute .exe erwartet wurde -- der
    Editor fehlte also im Installer, und niemand bemerkte es, weil das
    Ergebnis nur stillschweigend uebersprungen wurde.
    """
    spec = EDITOR_DIR / 'noScribeEdit_win.spec'
    if not spec.is_file():
        raise SystemExit(
            f'Editor-Spec nicht gefunden: {spec}\n'
            'Der Editor liegt als git-subtree unter noScribeEdit/.')

    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm',
           str(spec), '--distpath', str(EDITOR_DIST),
           '--workpath', str(SCRIPT_DIR / 'build' / 'editor')]
    if clean:
        cmd.append('--clean')
    print('>', ' '.join(cmd))
    subprocess.run(cmd, cwd=EDITOR_DIR, check=True)

    built = EDITOR_DIST / 'noScribeEdit' / 'noScribeEdit.exe'
    if not built.is_file():
        # Zusicherung statt stillem Ueberspringen: ein Installer ohne Editor
        # soll eine bewusste Entscheidung sein, kein Unfall.
        raise SystemExit(f'Editor wurde nicht gebaut, erwartet: {built}')
    print(f'Editor fertig: {built}')
    return built


def run_pyinstaller(dist_dir: Path, clean: bool) -> None:
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm',
           str(SCRIPT_DIR / 'noScribe_win.spec'), '--distpath', str(dist_dir)]
    if clean:
        cmd.append('--clean')
    print('>', ' '.join(cmd))
    subprocess.run(cmd, cwd=SCRIPT_DIR, check=True)


def format_version(version: str) -> str:
    """NSIS' VIProductVersion braucht genau vier Segmente."""
    segments = version.split('.')
    segments += ['0'] * (4 - len(segments))
    return '.'.join(segments[:4])


def build_file_lists(base: Path) -> tuple:
    install_entries = []
    uninstall_entries = []
    directories = []

    for root, _dirs, files in sorted(os.walk(base, topdown=True), key=lambda x: x[0]):
        rel = os.path.relpath(root, base)
        if rel == '.':
            rel = ''
            install_entries.append('SetOutPath "$INSTDIR"')
        else:
            rel = rel.replace(os.sep, '\\')
            install_entries.append(f'SetOutPath "$INSTDIR\\{rel}"')
            directories.append(rel)

        for filename in files:
            install_entries.append('File "{}"'.format(str(Path(root) / filename)))
            target = f'{rel}\\{filename}' if rel else filename
            uninstall_entries.append(f'Delete "$INSTDIR\\{target}"')

    for directory in reversed(directories):
        uninstall_entries.append(f'RMDir "$INSTDIR\\{directory}"')

    return '\n'.join(install_entries), '\n'.join(uninstall_entries)


def estimated_size_kb(base: Path) -> int:
    """Installierte Größe in KB für den Eintrag in "Apps & Features".

    Windows zeigt dort sonst gar nichts an, und eine zentrale
    Softwareverteilung kann den Platzbedarf nicht abschätzen.
    """
    total = sum(f.stat().st_size for f in base.rglob('*') if f.is_file())
    return max(1, total // 1024)


def run_nsis(dist_dir: Path, version: str, cuda: bool, nsis: Path) -> Path:
    out_dir = SCRIPT_DIR / 'win_installer'
    out_dir.mkdir(exist_ok=True)
    installer_name = 'Traudi_setup_' + version.replace('.', '_') + ('_cuda' if cuda else '') + '.exe'
    installer_path = out_dir / installer_name

    template = (SCRIPT_DIR / 'nsis_template.txt').read_text(encoding='utf-8')
    base = dist_dir / 'Traudi'
    install_entries, uninstall_entries = build_file_lists(base)

    # The editor comes from a separate repository and may be absent.
    has_editor = (base / '_internal' / 'noScribeEdit' / 'noScribeEdit.exe').is_file()
    editor_shortcut = (
        'CreateShortCut "$SMPROGRAMS\\$SM_Folder\\Traudi Editor.lnk" '
        '"$INSTDIR\\_internal\\noScribeEdit\\noScribeEdit.exe"' if has_editor else '')
    editor_delete = (
        'Delete "$SMPROGRAMS\\$SM_Folder\\Traudi Editor.lnk"' if has_editor else '')

    script = (template
              .replace('#*version*#', format_version(version))
              .replace('#*display_version*#', version)
              .replace('#*year*#', str(datetime.now().year))
              .replace('#*license_txt*#', str(PROJECT_ROOT / 'LICENSE.txt'))
              .replace('#*installer_name*#', str(installer_path))
              .replace('#*app_icon*#', str(PROJECT_ROOT / 'img' / 'traudi_logo.ico'))
              .replace('#*estimated_size_kb*#', str(estimated_size_kb(base)))
              .replace('#*editor_shortcut*#', editor_shortcut)
              .replace('#*editor_shortcut_delete*#', editor_delete)
              .replace('#*install_entries*#', install_entries, 1)
              .replace('#*uninstall_entries*#', uninstall_entries, 1))

    # Ein vergessener Platzhalter erzeugt sonst ein .nsi, das erst makensis
    # ablehnt -- nach dem kompletten PyInstaller-Lauf.
    leftover = sorted(set(re.findall(r'#\*[a-z_]+\*#', script)))
    if leftover:
        raise SystemExit(f'Nicht ersetzte Platzhalter in der NSIS-Vorlage: {leftover}')

    script_path = SCRIPT_DIR / 'nsis_tmp.nsi'
    script_path.write_text(script, encoding='utf-8')

    print('>', nsis, '/V4', script_path)
    subprocess.run([str(nsis), '/V4', str(script_path)], cwd=out_dir, check=True)
    return installer_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--cuda', action='store_true', help='als CUDA-Variante kennzeichnen')
    parser.add_argument('--skip-nsis', action='store_true', help='keinen Installer bauen')
    parser.add_argument('--no-clean', action='store_true', help='PyInstaller-Cache behalten')
    parser.add_argument('--nsis', help='Pfad zu makensis.exe')
    parser.add_argument('--skip-editor', action='store_true',
                        help='ohne den Editor bauen (er fehlt dann im Installer)')
    args = parser.parse_args()

    version = app_version()
    dist_dir = SCRIPT_DIR / 'dist' / ('Traudi_cuda' if args.cuda else 'Traudi_cpu')

    # Zuerst der Editor: der Hauptlauf packt sein Ergebnis mit ein.
    if args.skip_editor:
        print('Editor wird uebersprungen (--skip-editor).')
    else:
        build_editor(clean=not args.no_clean)

    run_pyinstaller(dist_dir, clean=not args.no_clean)
    print(f'PyInstaller fertig: {dist_dir}')

    if args.skip_nsis:
        return 0

    installer = run_nsis(dist_dir, version, args.cuda, find_nsis(args.nsis))
    print(f'Installer fertig: {installer}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
