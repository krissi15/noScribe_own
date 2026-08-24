# Herkunft und Änderungen

Dieses Verzeichnis enthält eine **veränderte Fassung** des noScribe Editors von
Kai Dröge.

- **Ursprung:** https://github.com/kaixxx/noScribeEditor
- **Übernommen am:** 24. August 2026
- **Übernommener Stand:** Commit `a4bc5ff`
  („More robust audio decoding with faulty files", 10. Juni 2026)
- **Lizenz:** GNU General Public License, Version 3 (siehe `LICENSE`)

## Warum dieser Hinweis hier steht

Die GPL-3.0 verlangt in Abschnitt 5 (a), dass ein verändertes Werk deutlich
sichtbar ausweist, dass es verändert wurde, und das Datum der Änderung nennt.
Für eine Anwendung, die von einer öffentlichen Stelle ausgeliefert wird, ist
das keine Formalie, sondern eine Rechtspflicht.

## Was verändert wurde

Die Änderungen sind in der Versionsgeschichte dieses Repositorys
nachvollziehbar. Der Übernahmestand liegt als eigener Commit vor, sodass sich
jede spätere Änderung davon abheben lässt:

    git log --oneline noScribeEdit/

Wesentliche Änderungen gegenüber dem Ursprung:

- **Wiedergabe auf einen Timer umgestellt.** `play_along()` war eine
  blockierende Schleife mit `processEvents()`. Solange sie lief, steckte der
  Slot fest — ein Klick ins Transkript konnte deshalb nur eines bewirken:
  die Wiedergabe anhalten.
- **Klick springt in die Aufnahme**, statt sie anzuhalten. Nur bei einem
  Wechsel des Segments, damit das Korrigieren während des Hörens nicht bei
  jedem Tastendruck an den Zeilenanfang zurückspringt.
- **Mitlaufende Zeilenmarkierung** über `ExtraSelection` statt über eine
  Textauswahl. Eine Auswahl wäre beim ersten Tastendruck samt Absatz weg
  gewesen; jetzt bleibt der Schreibcursor dort, wo gearbeitet wird.
- **Anhalten und Fortsetzen** an derselben Stelle. `QMediaPlayer.stop()`
  setzt die Position auf 0, der Stand wird deshalb vorher gemerkt.
- **Sprecher umbenennen** (`speaker_dialog.py`): aus `S01` wird an allen
  Stellen auf einmal ein Name. Bewusst kein Suchen-und-Ersetzen — ersetzt
  wird nur die Angabe am Absatzanfang, und das Zeichenformat wird
  mitgenommen, weil es die Zeitmarke des Segments trägt.
- **Traudi-Farbsystem einschließlich Dunkelmodus** (`traudi_theme.py`).
  Zuvor gab es überhaupt keine Farbwahl: Text stand fest auf `#000000` über
  fest `#ffffff`, und das gesamte Transkript liegt in Ankern, deren Farbe
  ebenfalls fest auf Schwarz gesetzt war. Die Werte stammen aus derselben
  Palette wie Traudi; `traudi_colors.json` wird von `scripts/make_theme.py`
  erzeugt. Der Modus wird aus Traudis Konfiguration gelesen.
- **Zeitmarken werden beim Laden umgefärbt.** Ihre Farbe steht im Transkript,
  weil noScribe sie beim Speichern hineinschreibt. Ein im Dunkelmodus
  erzeugtes Transkript brachte im hellen Editor sonst hellgraue Zeitmarken
  auf Weiß mit, rund 2:1.
- **Umbenennung auf Traudi Editor** samt Symbolen. Die ausführbare Datei
  heißt weiterhin `noScribeEdit.exe`, weil `noScribe/main.py`, die Spec und
  der Installer sich auf diesen Namen verständigt haben; sichtbar ist überall
  „Traudi Editor".
- **Einbindung in den Traudi-Installer.** Der Editor wurde zuvor
  stillschweigend weggelassen, wenn er nicht von Hand gebaut worden war: die
  Spec kopierte das Quellverzeichnis, während der Bau und die Anwendung eine
  fertige `noScribeEdit.exe` erwarteten.

## Was nicht übernommen wurde

Der Ursprung führt unter `Test/` eine Beispielaufnahme mit — eine
Podcast-Folge von rund 12 MB samt Transkript. Sie ist bewusst nicht
übernommen worden. Für eine Anwendung, die von einer öffentlichen Stelle
ausgeliefert wird, wäre fremdes Tonmaterial ohne geklärte
Weiterverbreitungsrechte im Repository nicht vertretbar, und jeder Klon
zahlte die 12 MB dauerhaft mit.

## Aktualisierung aus dem Ursprung

Das Verzeichnis ist als `git subtree` eingebunden. Neuerungen von dort lassen
sich übernehmen mit:

    git subtree pull --prefix noScribeEdit \
        https://github.com/kaixxx/noscribeeditor main --squash

Der Ursprung wird weiterentwickelt — die letzte Änderung zum Zeitpunkt der
Übernahme stammte vom Juni 2026.
