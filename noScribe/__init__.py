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

Eines passiert hier aber doch, und zwar absichtlich: die Telemetrie der
Bibliotheken wird abgeschaltet. Jeder Prozess, der irgendetwas aus diesem
Paket lädt -- die Anwendung, die Kindprozesse für Whisper und pyannote,
`scripts/fetch_models.py` --, läuft durch diese Datei, und zwar bevor
pyannote importiert wird. Siehe noScribe/privacy.py.
"""

from noScribe import privacy as _privacy
from noScribe._version import __version__, __year__

_privacy.disable_telemetry()

__all__ = ['__version__', '__year__']
