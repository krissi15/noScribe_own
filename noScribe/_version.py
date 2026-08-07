"""Einzige Quelle der Versionsnummer.

Absichtlich ein eigenes Modul ohne jeden Import: `pyproject.toml`, die drei
PyInstaller-Specs und `pyinstaller/win_build.py` lesen die Version hier aus,
ohne dabei `noScribe/main.py` (und damit torch, faster-whisper, pyannote)
laden zu müssen.

Wer die Version ändert, ändert sie nur hier -- `tests/test_version.py` prüft,
dass nirgends eine zweite Fassung stehen bleibt.
"""

__version__ = "0.7.3"
__year__ = "2026"
