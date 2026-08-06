# -*- mode: python ; coding: utf-8 -*-
import os
import re

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_all

# Version aus der einzigen Quelle lesen, statt sie hier ein zweites Mal zu
# pflegen -- genau das war hier auf 0.7.1 stehengeblieben.
_version_src = open(os.path.join('..', 'noScribe', '_version.py'), encoding='utf-8').read()
APP_VERSION = re.search(r'^__version__\s*=\s*"([^"]+)"', _version_src, re.M).group(1)

# macOS-App-Bündel erwarten ein .icns. Fehlt es, wird lieber gar kein Icon
# gesetzt als eine .ico übergeben, mit der PyInstaller nichts anfangen kann.
_icns = os.path.join('..', 'img', 'traudi_logo.icns')
BUNDLE_ICON = _icns if os.path.isfile(_icns) else None

datas = [('../img/traudi_logo.ico', 'img'), ('../img/traudi_logo.png', 'img'), ('../LICENSE.txt', '.'), ('../models/precise', 'models/precise/'), ('../models/fast', 'models/fast/'), ('../noScribe/theme/rlp_justiz.json', 'noScribe/theme/'), ('../prompts/prompt.yml', 'prompts'), ('../prompts/prompt_nd.yml', 'prompts/'),
('../prompts/vocab_justiz_de.txt', 'prompts/'), ('../pyannote', 'pyannote/'), ('../README.md', '.'), ('../trans', 'trans/')]
binaries = []
hiddenimports = ['noScribe.dialogs.about']
datas += collect_data_files('faster_whisper')
datas += collect_data_files('lightning_fabric')
tmp_ret = collect_all('pyannote')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('speechbrain')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['../noScribe/__main__.py'],
    pathex=['..'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Traudi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['../img/traudi_logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Traudi',
)
app = BUNDLE(
    coll,
    name='Traudi.app',
    icon=BUNDLE_ICON,
    bundle_identifier='de.rlp.justiz.traudi',
    info_plist={
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
    },
)
