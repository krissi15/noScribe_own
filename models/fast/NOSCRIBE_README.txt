Das Modell "fast" ist Whisper large-v3-turbo in int8-Quantisierung
(ca. 0,8 GB). Auf CPU ist es rund 30 % schneller als "precise".

Es liegt nicht im Repository. Zum Herunterladen aus dem Projektverzeichnis:

    python scripts/fetch_models.py --only fast

Traudi lädt das Modell auch beim ersten Start automatisch in das
Nutzerverzeichnis, falls hier keines liegt. Das Skript zieht dabei den
Unterordner faster-whisper-large-v3-turbo-int8 an die richtige Stelle -- das
muss nicht mehr von Hand geschehen.

Quelle: https://huggingface.co/mukowaty/faster-whisper-int8
