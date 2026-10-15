# Modelle und ihre Lizenzen

Traudi selbst steht unter der GPL-3.0 (siehe `LICENSE.txt`). Die
KI-Modelle, mit denen Traudi arbeitet, stammen von Dritten und haben eigene
Lizenzen. Diese Datei liegt dem Installer bei und erfüllt die Pflicht zur
Namensnennung (CC-BY-4.0). Die Gewichte werden **unverändert** weitergegeben.

## Sprechererkennung (im Installer enthalten)

### pyannote „speaker-diarization-community-1“

- **Urheber:** pyannoteAI / Hervé Bredin und Mitwirkende
- **Quelle:** https://huggingface.co/pyannote/speaker-diarization-community-1
- **Lizenz:** Creative Commons Namensnennung 4.0 International (CC-BY-4.0),
  https://creativecommons.org/licenses/by/4.0/
- **Ablage im Programm:** `_internal\pyannote\` (Segmentierung, Konfiguration)

### Stimmabdruck-Modell WeSpeaker ResNet34-LM

- **Urheber:** H. Wang, C. Liang, S. Wang u. a. (WeNet/WeSpeaker), trainiert
  auf VoxCeleb
- **Quelle:** https://huggingface.co/pyannote/wespeaker-voxceleb-resnet34-LM
- **Lizenz:** CC-BY-4.0 (folgt der Lizenz des VoxCeleb-Datensatzes, siehe
  https://github.com/wenet-e2e/wespeaker/blob/master/docs/pretrained.md)
- **Zitat:** Wang, H. et al. (2023). *Wespeaker: A research and production
  oriented speaker embedding learning toolkit.* ICASSP 2023.
- **Ablage im Programm:** `_internal\pyannote\embedding\`

### PLDA-Modell (VBx)

- **Urheber:** BUT Speech@FIT, https://speech.fit.vut.cz/
- **Quelle:** Bestandteil von „speaker-diarization-community-1“
- **Lizenz:** im Ursprung nicht eigens angegeben; es gilt vermutlich die
  Lizenz des Gesamtpakets (CC-BY-4.0). **Offen, rechtlich prüfen lassen.**
- **Ablage im Programm:** `_internal\pyannote\plda\`

## Spracherkennung (wird beim ersten Start heruntergeladen)

### Whisper large-v3-turbo

- **Urheber:** OpenAI
- **Quelle des Ausgangsmodells:** https://github.com/openai/whisper,
  https://huggingface.co/openai/whisper-large-v3-turbo
- **Lizenz des Ausgangsmodells:** MIT,
  https://github.com/openai/whisper/blob/main/LICENSE
- **Umgewandelte Fassungen (CTranslate2), die Traudi lädt:**
  - „precise“: https://huggingface.co/dropbox-dash/faster-whisper-large-v3-turbo
  - „fast“ (int8): https://huggingface.co/mukowaty/faster-whisper-int8
- **Lizenz der umgewandelten Fassungen:** auf den Seiten der Repositorys
  nicht verlässlich angegeben. Die Umwandlung ändert nach verbreiteter
  Auffassung nichts an der MIT-Lizenz des Ausgangsmodells. **Offen, vor einer
  zentralen Verteilung rechtlich prüfen lassen.**

MIT-Lizenzhinweis von Whisper:

    Copyright (c) 2022 OpenAI

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

## Beispielaufnahme für den Selbsttest

`pyannote\audio\sample\sample.wav` gehört zum Paket pyannote.audio (MIT-Lizenz)
und dient nur `Traudi.exe --selftest`.

## Offene Punkte

- Lizenz der PLDA-Gewichte (siehe oben).
- Lizenz der umgewandelten Whisper-Fassungen (siehe oben).
- Ob die Weitergabe der auf HuggingFace zugangsbeschränkten
  („gated“) pyannote-Gewichte im Installer mit den dortigen
  Zugangsbedingungen vereinbar ist. Die Gewichte selbst stehen unter
  CC-BY-4.0, das die Weitergabe erlaubt; die Zugangsbedingungen betreffen
  das Herunterladen.
