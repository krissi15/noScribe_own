# Traudi

## Version 0.7.7
Datenschutz, Schutz vor Datenverlust und Tempo, nach einer Prüfung durch
sieben Fachperspektiven.

- Keine Nutzungsstatistik mehr an Dritte: pyannote 4 schickte bei jeder
  Sprechererkennung Sitzungskennung, Audiodauer und Sprecherzahl an
  otel.pyannote.ai. Abgeschaltet, ebenso die Telemetrie von huggingface_hub.
- Logdateien enthalten keinen Transkripttext mehr, heißen nach dem Zeitpunkt
  und werden nach 30 Tagen gelöscht.
- Die WAV-Arbeitskopie der Aufnahme wird nach jedem Auftrag gelöscht, Reste
  aus Abbrüchen beim nächsten Start.
- Die Online-Abfrage nach neuen Versionen ist standardmäßig aus.
- Ein vorhandenes Transkript wird nicht mehr überschrieben -- auch nicht, wenn
  dieselbe Aufnahme ein zweites Mal läuft.
- Editor: Speichern ersetzt die Datei erst, wenn die neue Fassung vollständig
  geschrieben ist; scheitert es, bleibt das Fenster offen. Vorher konnten beim
  Schließen alle Korrekturen verloren gehen.
- Ohne erkannte Sprache entsteht trotzdem eine Datei mit Hinweis, statt einer
  falschen Erfolgsmeldung.
- Während der Transkription entsteht nur noch eine Datei. Scheiterte das
  Zwischenspeichern kurz (Virenscanner, OneDrive), wechselte Traudi bisher
  dauerhaft auf einen neuen Namen; bei einer 74-Minuten-Aufnahme lagen am Ende
  sieben Dateien da, sechs davon unvollständig. Jetzt folgt einfach der nächste
  Versuch; nur der Endstand weicht nach mehreren Versuchen auf einen anderen
  Namen aus.
- Nachgelegte Diarisierungs-Gewichte im Benutzerordner funktionieren jetzt.
- Schalter in der config.yml dürfen auch `true`/`false` lauten, ohne dass
  Traudi wortlos nicht startet.
- Installer: 64-Bit nach `C:\Program Files\Traudi`, Registry in der
  64-Bit-Ansicht. Eine Altinstallation unter `Program Files (x86)` wird
  automatisch entfernt.

Schnellere Sprechererkennung auf dem Prozessor:

- Der teuerste Schritt („Embeddings“) ist etwa 3,5-mal so schnell.
  pyannote schickte jedes 10-Sekunden-Fenster dreimal durch das
  Stimmabdruck-Netz -- einmal je möglichem Sprecher, auch wenn dort niemand
  sprach. Traudi rechnet jedes Fenster einmal und Fenster ohne Sprache gar
  nicht. Die Sprecherzuordnung bleibt gleich (Abweichung nur durch Rundung in
  der achten Nachkommastelle); `--selftest` vergleicht beide Wege an einer
  Beispielaufnahme mit zwei Sprechern.
- Windows bremst die fensterlosen Rechenprozesse nicht mehr als
  „Hintergrundarbeit“ (Energiedrosselung, auf neueren Intel-Prozessoren die
  langsamen Effizienzkerne).
- Die Sprechererkennung hält sich an die eingestellte Thread-Zahl
  (`threads`) wie Whisper.
- Während der Sprechererkennung steht die geschätzte Restzeit im Protokoll.
- Weniger Arbeitsspeicher beim Einlesen der Aufnahme.
- `--selftest` meldet die Rechenzeit und die Thread-Zahl -- hilfreich, um
  einen langsamen Rechner einzuordnen.
- Jeder Bau liefert neben dem Installer ein ZIP zum Ausprobieren ohne
  Administratorrechte.

Nachprüfbarkeit des Transkripts:

- Unter dem Titel steht jetzt sichtbar „Maschineller Entwurf – nicht geprüft.
  Vor Verwendung vollständig mit der Aufnahme abgleichen.“ Als eigener Absatz,
  damit er nach der Prüfung im Editor mit einem Griff gelöscht werden kann.
- Der Kopf nennt Erstellungszeitpunkt, Modell samt Herkunft und die SHA-256-
  Prüfsumme der Original-Audiodatei. Damit lässt sich belegen, aus welcher
  Aufnahme der Text stammt, auch wenn die Datei umbenannt wurde
  (`certutil -hashfile <Datei> SHA256`). Dieselben Angaben stehen
  maschinenlesbar als `<meta name="traudi_…">` im HTML; der Editor behält sie
  beim Speichern bei.
- Wörter, bei denen sich die Spracherkennung unsicher war, sind unterstrichen
  (Erkennungssicherheit unter 50 %, einstellbar über `uncertain_word_threshold`).
  Der Kopf erklärt die Markierung; Strg+U im Editor nimmt sie nach der Prüfung
  weg. Das README behauptete bisher, erfundener Text falle beim Lesen auf.
- WebVTT: Die NOTE am Anfang enthält den ganzen Kopf, nicht nur dessen erste
  Zeile.

Sprache:

- Der Editor ist durchgehend deutsch: Menüs, Meldungen, „Suchen und
  Ersetzen“ und die Standardknöpfe (Speichern/Verwerfen/Abbrechen), die bisher
  englisch waren.
- Die deutsche Übersetzung spricht einheitlich mit „Sie“ an.

Lizenzen:

- Neue Datei `MODELLE_LIZENZEN.md` (liegt dem Installer bei): Urheber, Quellen
  und Lizenzen der Modelle -- pyannote community-1 und WeSpeaker (CC-BY-4.0),
  PLDA (BUT), Whisper (MIT). Offene Punkte sind ausdrücklich benannt. Der
  Über-Dialog nennt die Modelle und ihre Lizenzen.

Bau:

- Der Windows-CPU-Bau installiert festgeschriebene Paketfassungen
  (`environments/constraints_win_cpu.txt`, aus einem grünen Bau übernommen)
  und prüft die Umgebung mit `pip check`. Vorher waren u. a. faster-whisper, av
  und pyannote.audio offen. pyannote.audio ist in allen Listen auf 4.0.x
  begrenzt.
- Am Ende jedes Baus steht im Protokoll, welche Fassungen im Installer
  stecken.

## Version 0.7.6
- Behebt: Die Sprechererkennung scheiterte in 0.7.5 an „No module named
  'scipy._external.array_api_compat.numpy.fft'". Dem Windows-Paket fehlte ein
  Modul, das scipy erst zur Laufzeit lädt.
- Behebt: Die mitgelieferten Gewichte der Sprechererkennung wurden über einen
  temporären Pfad gesucht, der beim Benutzen schon wieder gelöscht war
  („HFValidationError: Repo id must use alphanumeric chars").
- Behebt: Die Sprechererkennung konnte im Windows-Paket keine Audiodatei lesen
  („Couldn't find appropriate backend to handle uri"). Traudi liest die intern
  erzeugte WAV-Datei jetzt selbst, ohne torchaudio.
- Neu: `Traudi.exe --selftest` lässt die Sprechererkennung einmal auf einem
  kurzen Rauschen laufen. Der Bau macht das bei jedem Installer.

## Version 0.7.5
- Behebt: 0.7.4 startete unter Windows nicht („No module named 'jaraco'"). Der
  Installer war mit einer zu alten PyInstaller-Fassung gebaut worden.
- Der Bau prüft jetzt, ob Traudi und der Editor nach dem Bauen tatsächlich
  starten.

## Version 0.7.4
Korrekturen nach der Erprobung von 0.7.3.

- Sprechererkennung: Der Installer bringt die Gewichte jetzt mit. Fehlen sie
  trotzdem, bricht die Transkription nicht mehr ab, sondern läuft ohne
  Sprecherangaben weiter.
- Lesbarkeit: Kontraste überarbeitet (Dateinamen waren weiß auf Weiß), neuer
  Dunkelmodus, umschaltbar ohne Neustart.
- Editor: wird jetzt mitinstalliert (Startmenü: „Traudi Editor"). Ein Klick
  ins Transkript springt an die Stelle in der Aufnahme, die laufende Zeile ist
  hervorgehoben, Sprecher lassen sich in einem Schritt umbenennen.
- `scripts/fetch_models.py` funktioniert wieder vor der vollständigen
  Einrichtung.
- Ein Absturz meldet jetzt Rückgabewert 1 statt 0 -- wichtig für die
  Softwareverteilung.

# noScribe Changelog

## version 0.7
- Batch transcription: process several files at once
- Improved speaker identification
- Improved handling of punctuation issues
- Command line interface for scripting
- many small fixes, improvements and updates

## version 0.6:
- 3x faster transcription
- new possibility to install custom models
- new option: include or leave out speech disfluencies and filler words
- Editor: Search & Replace feature to quickly change speaker names etc.
- improved pause detection
- many small fixes, improvements and updates

## version 0.5:
- new WebVTT output (video subtitle format), allows also importing noScribe transcripts into EXMARaLDA
- new plain text output (*.txt)
- new automatic update notification on new releases
- improved speaker detection: number of speakers can be defined beforehand
- reduced hallucination and looping by adding a VAD filter
- CUDA support now non-beta
- small fixes with hebrew language setting, chinese UI locale, requirements file, etc.  

## version 0.4.5:
- Windows: beta version to test CUDA support (acceleration with NVIDIA graphics cards) 

## version 0.4.2:
- MacOS: Solves a bug where speaker-detection would become unreliable with MPS-acceleration (a switch to torchaudio 2.1.0 rectified this).
- Windows: no changes

## version 0.4.1:
- Windows: bugfix, rectifies a problem in combination with NVIDIA graphics cards
- macOS: First beta release. Solved a bug with macOS Sonoma where noScribe would not react to the mouse. 

## version 0.4 beta:
- much improved **speaker detection/separation**
- new option to mark **pauses** (sections with no voice activity) in the transcript
- new option to mark **overlapping speech** (experimental)
- new option to include **timestamps** in the transcript
- new **noScribe Editor** app to check and correct transcripts (no MS Word-Macros anymore)
- noScribe now outputs an **HTML-file** which can be opened in every major word editor (MS Word, LibreOffice, OpenOffice...) or QDA-software package
- many changes under the hood to prepare for an upcoming macOS-version and improve reliability and quality of the transcription
- switched from "whisper.cpp" to "faster-whisper" as the basic framework (mainly because of the more precise timestamps)  
- macOS: First alpha release

## version 0.3:
**new:**
- Translations of the user interface into Spanish, French, Italian, Japanese, Portuguese, Russian, Chinese. Thank you, [mlynar-czyk]( https://github.com/mlynar-czyk), for this contribution! Be aware: These translations have been generated with a clever use of chatGPT. Please report any errors that you will find and make – if possible – a pull request with a better translation.
- Added hyperlinks to the main window. You can now open the finished transcript directly by clicking on the filename in the log.
- Improved speaker identification, especially in situations with quick changes (by reducing "max-len" in whisper to 30).  
- Installer now runs without admin rights. You should be able to install noScribe on a computer where you don’t have administrator privileges (i.e., because the machine is managed by the IT-department of your university). Thanks you, [BabyFnord](https://github.com/BabyFnord), for this suggestion!
 
**fixes:**
- To solve the problem described in issue https://github.com/kaixxx/noScribe/issues/2 (transcription failing with error 3221225794 or 3221225501), I have now included a version of whisper.cpp that supports older hardware (non AVX2). NoScribe selects automatically which version to use. Be aware though that using such old hardware will result in a very slow transcription.
- Corrected UTF-8 encoding error that resulted in a failing transcription in some languages (i.e., Japanese, Hungarian). Thank you to the two people reporting this problem via e-mail!
- fixed: Auto save was saving too often during transcription.
- fixed: Play along function in Word sometimes not finding the beginning of the transcription
- fixed: Funny mistake in readme ("sensible data" instead of "sensitive data"). Thanks [TheOnlyWayUp](https://github.com/TheOnlyWayUp)!


## version 0.2b: 
- initial beta release
