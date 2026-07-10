# -*- mode: python ; coding: utf-8 -*-
import os

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata

block_cipher = None
project_root = os.path.abspath(os.path.join(SPECPATH, '..'))

# noScribe:

noScribe_datas = [] 
noScribe_binaries = []
noScribe_hiddenimports = []

# The Whisper models (0.8 / 1.6 GB) are NOT bundled. Traudi fetches them into
# the user's data directory on first start; see noScribe/model_download.py.
# The diarization weights are only 32 MB and stay in the installer, because
# their HuggingFace repository is gated and end users have no token.
noScribe_datas += [
('../trans/', './trans/'),
# The model folders must exist in the bundle: WhisperModelManager resolves
# them with importlib.resources, which needs a real directory.
('../models/fast/NOSCRIBE_README.txt', './models/fast/'),
('../models/precise/NOSCRIBE_README.txt', './models/precise/'),
('../LICENSE.txt', '.'),
('../img/traudi_logo.ico', 'img/'),
('../img/traudi_logo.png', 'img/'),
('../noScribe/theme/rlp_justiz.json', 'noScribe/theme/'),
('../prompts/prompt.yml', 'prompts/'),
('../prompts/prompt_nd.yml', 'prompts/'),
('../README.md', '.')]

# The editor lives in a separate repository and may not be checked out.
if os.path.isdir(os.path.join(project_root, 'noScribeEdit')):
    noScribe_datas += [('../noScribeEdit/', './noScribeEdit/')]
noScribe_datas += collect_data_files('customtkinter')
noScribe_datas += copy_metadata('AdvancedHTMLParser')
noScribe_datas += collect_data_files('faster_whisper')

# for pyannote:
noScribe_datas += [('../pyannote/', './pyannote/')]
noScribe_datas += collect_data_files('lightning')
noScribe_datas += collect_data_files('gradio')
noScribe_datas += collect_data_files('lightning_fabric')
noScribe_datas += collect_data_files('librosa')
noScribe_datas += collect_data_files('pyannote')
noScribe_datas += copy_metadata('filelock')
noScribe_datas += copy_metadata('tqdm')
# noScribe_datas += copy_metadata('regex')
noScribe_datas += copy_metadata('requests')
noScribe_datas += copy_metadata('packaging')
noScribe_datas += copy_metadata('numpy')
noScribe_datas += copy_metadata('scipy')
noScribe_datas += copy_metadata('tokenizers')
noScribe_datas += copy_metadata('pyannote.audio')
noScribe_datas += copy_metadata('pyannote.core')
noScribe_datas += copy_metadata('pyannote.database')
noScribe_datas += copy_metadata('pyannote.metrics')
noScribe_datas += copy_metadata('pyannote.pipeline')
noScribe_binaries += collect_dynamic_libs('pyannote')
noScribe_hiddenimports += collect_submodules('pyannote')
noScribe_hiddenimports += collect_submodules('scipy')
# noScribe_hiddenimports += ['scipy._lib.array_api_compat.numpy.fft']
tmp_ret = collect_all('speechbrain')
noScribe_datas += tmp_ret[0]; noScribe_binaries += tmp_ret[1]; noScribe_hiddenimports += tmp_ret[2]

noScribe_a = Analysis(
    ['../noScribe/__main__.py'],
    pathex=[project_root],
    binaries=noScribe_binaries,
    datas=noScribe_datas,
    hiddenimports=noScribe_hiddenimports,   # <-- use them
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

noScribe_pyz = PYZ(noScribe_a.pure, noScribe_a.zipped_data, cipher=block_cipher)

noScribe_exe = EXE(
    noScribe_pyz,
    noScribe_a.scripts,
    [],
    exclude_binaries=True,
    name='Traudi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # console=False,
    hide_console="hide-late",
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['../img/traudi_logo.ico'],
)

# assemble the dist folder with all needed DLLs, datas, etc.
noScribe_coll = COLLECT(
    noScribe_exe,
    noScribe_a.binaries,
    noScribe_a.zipfiles,
    noScribe_a.datas,
    strip=False,
    upx=False,
    name='Traudi'
)
