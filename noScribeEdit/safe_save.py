"""Speichern, ohne das Original aufs Spiel zu setzen.

Bisher öffnete der Editor die Zieldatei mit `open(path, 'w')`. Das leert sie
sofort -- scheiterte das Schreiben danach (Netzfreigabe weg, Platte voll),
war auch die vorige Fassung verloren.

Jetzt entsteht die neue Fassung erst als Hilfsdatei im selben Verzeichnis und
ersetzt die alte in einem Schritt (`os.replace`). Ist die Zieldatei gesperrt,
etwa weil sie in Word offen ist, schlägt genau dieser Schritt fehl, und die
alte Datei bleibt, wie sie war.
"""

import os
import shutil
import tempfile


def write_text_atomic(path, text: str, encoding: str = 'utf-8') -> None:
    """Schreibt `text` nach `path` -- ganz oder gar nicht."""
    path = os.fspath(path)
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix='.~traudi-', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(path):
            # mkstemp legt die Hilfsdatei mit 0600 an; die ersetzte Datei
            # soll ihre bisherigen Rechte behalten.
            shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
