"""Traudi -- KI-gestuetzte Audiotranskription fuer die Justiz.

Bewusst schlank: hier wird **nicht** `main` importiert. Frueher stand hier
`from noScribe import main`, und damit zog schon ein `import noScribe` die
gesamte Anwendung mit -- AdvancedHTMLParser, customtkinter, torch,
faster-whisper, pyannote.

Das machte die Hilfsmodule unbenutzbar, die gerade ohne diesen Ballast
auskommen sollen. `scripts/fetch_models.py` etwa braucht nur
`huggingface_hub`, scheiterte aber mit einem ModuleNotFoundError auf
AdvancedHTMLParser -- ausgerechnet beim Einrichten, wo man die Gewichte
holt, bevor alles andere installiert ist.

Wer die Anwendung will, schreibt `from noScribe import main`.
"""

from noScribe._version import __version__, __year__

__all__ = ['__version__', '__year__']
