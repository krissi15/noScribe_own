# Traudi Editor

Editor für Transkripte aus Traudi.

Das Transkript steht links, die Aufnahme läuft dazu: die gerade gesprochene
Zeile ist hervorgehoben und scrollt mit, ein Klick in eine andere Zeile
springt in der Aufnahme dorthin — auch während die Wiedergabe läuft. Getippt
werden kann dabei die ganze Zeit.

| | |
|---|---|
| Wiedergabe starten und anhalten | `Strg` + `Leertaste` |
| Sprecher umbenennen | `Strg` + `Umschalt` + `S` |
| Suchen und Ersetzen | `Strg` + `F` |

## Herkunft

Veränderte Fassung des noScribe Editors von Kai Dröge, GNU GPL-3.0.
Was verändert wurde und warum, steht in [`NOTICE.md`](NOTICE.md).

## Bauen

Der Editor wird vom Hauptbau mitgebaut:

    python pyinstaller/win_build.py

Einzeln:

    pip install -r noScribeEdit/environments/requirements.txt
    pyinstaller noScribeEdit/noScribeEdit_win.spec

Die Farbdatei `traudi_colors.json` wird erzeugt, nicht gepflegt. Nach jeder
Änderung an `noScribe/theme/palette.py`:

    python scripts/make_theme.py
