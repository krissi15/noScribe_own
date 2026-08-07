#!/usr/bin/env python3
# Traudi - erzeugt die abgeleiteten Bilddateien
# Copyright (C) 2026
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Erzeugt img/traudi_logo.icns und img/traudi_splash.png aus dem Logo.

    python scripts/make_assets.py

Beide Dateien sind Ableitungen von img/traudi_logo.png und werden deshalb hier
erzeugt statt von Hand gepflegt: So bleibt das Logo die einzige Quelle, und ein
neues Logo zieht die anderen Dateien automatisch nach.

Die Ergebnisse gehören trotzdem eingecheckt -- der Windows- und der
Linux-Build referenzieren den Startbildschirm fest, und ein Bauvorgang soll
nicht von Pillow und einer vorhandenen Schriftart abhängen.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMG = PROJECT_ROOT / 'img'
LOGO = IMG / 'traudi_logo.png'

# Farben des Landeswappens, wie in noScribe/theme/__init__.py.
BLACK, WHITE, RED, GOLD, MUTED, BORDER = (
    '#1A1A1A', '#FFFFFF', '#DD0000', '#FFCE00', '#5A5A5A', '#D8D8D8')

# Schriftkandidaten je Plattform. Findet sich keiner, nimmt Pillow seine
# eingebaute Schrift -- unschön, aber kein Grund abzubrechen.
SANS = ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        'C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/arial.ttf']
SANS_BOLD = ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
             '/System/Library/Fonts/Helvetica.ttc',
             'C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/arialbd.ttf']


def _font(candidates, size):
    from PIL import ImageFont
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    print(f'  Hinweis: keine passende Schrift gefunden, nehme die eingebaute '
          f'(Größe {size} wird ignoriert).')
    return ImageFont.load_default()


def make_icns() -> None:
    """Das macOS-App-Bündel braucht ein .icns; eine .ico nimmt es nicht an."""
    from PIL import Image

    target = IMG / 'traudi_logo.icns'
    Image.open(LOGO).convert('RGBA').save(target, format='ICNS')
    print(f'  {target.relative_to(PROJECT_ROOT)}')


def make_splash() -> None:
    """Startbildschirm des PyInstaller-Bootloaders.

    Er wird gezeichnet, bevor Python startet -- deshalb ein fertiges Bild und
    kein Fenster aus CustomTkinter. Die Gestaltung folgt der Kopfzeile der
    Anwendung: schwarzes Band, darunter die Akzentlinie in Rot und Gold.
    """
    from PIL import Image, ImageDraw

    width, height = 460, 240
    img = Image.new('RGB', (width, height), WHITE)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, width, 96], fill=BLACK)
    draw.rectangle([0, 96, width // 2, 100], fill=RED)
    draw.rectangle([width // 2, 96, width, 100], fill=GOLD)

    logo = Image.open(LOGO).convert('RGBA').resize((64, 64), Image.LANCZOS)
    img.paste(logo, (28, 16), logo)

    draw.text((108, 28), 'Traudi', font=_font(SANS_BOLD, 30), fill=WHITE)
    draw.text((110, 66), 'Transkription für die Justiz',
              font=_font(SANS, 13), fill=BORDER)
    draw.text((28, 128), 'Ministerium der Justiz Rheinland-Pfalz',
              font=_font(SANS, 13), fill=BLACK)
    draw.text((28, 156), 'Die Anwendung wird gestartet …',
              font=_font(SANS, 13), fill=MUTED)
    draw.text((28, 196), 'Der erste Start dauert etwas länger.',
              font=_font(SANS, 11), fill=MUTED)

    target = IMG / 'traudi_splash.png'
    img.save(target)
    print(f'  {target.relative_to(PROJECT_ROOT)}')


def main() -> int:
    try:
        import PIL  # noqa: F401
    except ImportError:
        raise SystemExit('Pillow fehlt. Installieren mit: pip install Pillow')

    if not LOGO.is_file():
        raise SystemExit(f'Quelle fehlt: {LOGO}')

    print('Erzeuge abgeleitete Bilddateien aus img/traudi_logo.png:')
    make_icns()
    make_splash()
    return 0


if __name__ == '__main__':
    sys.exit(main())
