# Traudi - Über-Dialog
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

"""Der Dialog „Über Traudi".

Er ist nicht nur Zierde: Traudi ist eine Abwandlung von noScribe unter der
GPL-3.0. Deren §5 verlangt, dass ein verändertes Werk deutlich sichtbar
ausweist, dass es verändert wurde. Die Begrüßung im Protokoll nennt seit dem
Rebranding zuerst Traudi -- die Herkunft muss dafür hier stehen, vollständig
und auffindbar.

Der zweite Zweck ist praktischer Natur: eine Anlaufstelle für den Support. Der
Dialog nennt die Version und öffnet auf Knopfdruck das Protokoll- und das
Einstellungsverzeichnis -- die beiden Angaben, nach denen als Erstes gefragt
wird.
"""

import importlib.resources as impres
import logging
import os
import platform
import subprocess
import webbrowser
from pathlib import Path

import customtkinter as ctk
from PIL import Image
from i18n import t

from .._version import __version__, __year__
from ..theme import COLORS, secondary_button

logger = logging.getLogger(__name__)

PROJECT_URL = 'https://github.com/krissi15/noScribe_own'
UPSTREAM_URL = 'https://github.com/kaixxx/noScribe'
LICENSE_URL = 'https://www.gnu.org/licenses/gpl-3.0.html'


def open_in_file_manager(path) -> None:
    """Öffnet ein Verzeichnis im Dateimanager des Systems.

    Dieselbe Dreiteilung benutzt main.py schon für den Modell-Ordner.
    """
    path = str(path)
    try:
        if platform.system() == 'Windows':
            os.startfile(path)  # noqa: S606 - beabsichtigt, Pfad kommt von uns
        elif platform.system() == 'Darwin':
            subprocess.run(['open', path], check=False)
        else:
            subprocess.run(['xdg-open', path], check=False)
    except OSError:
        logger.warning('Konnte %s nicht öffnen', path, exc_info=True)


class AboutDialog(ctk.CTkToplevel):
    """Version, Herkunft, Lizenz und die Pfade, nach denen der Support fragt."""

    def __init__(self, master, config_dir: Path):
        super().__init__(master)
        self.config_dir = Path(config_dir)

        self.title(t('about_title'))
        self.geometry('560x520')
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        body = ctk.CTkFrame(self, fg_color='transparent')
        body.pack(fill='both', expand=True, padx=24, pady=24)

        self._build_head(body)
        self._build_origin(body)
        self._build_buttons(body)

        self.bind('<Escape>', lambda _event: self._close())

    # -- Aufbau -----------------------------------------------------------

    def _build_head(self, parent):
        head = ctk.CTkFrame(parent, fg_color='transparent')
        head.pack(fill='x')

        try:
            self._logo = ctk.CTkImage(
                light_image=Image.open(impres.files('img') / 'traudi_logo.png'),
                size=(72, 72))
            ctk.CTkLabel(head, image=self._logo, text='').pack(side='left', padx=(0, 16))
        except (OSError, ValueError):
            logger.warning('Logo im Über-Dialog konnte nicht geladen werden', exc_info=True)
            self._logo = None

        titles = ctk.CTkFrame(head, fg_color='transparent')
        titles.pack(side='left', anchor='w')
        ctk.CTkLabel(titles, text=t('app_name'), anchor='w',
                     font=ctk.CTkFont(size=26, weight='bold')).pack(anchor='w')
        ctk.CTkLabel(titles, text=t('about_version', v=__version__), anchor='w',
                     text_color=COLORS['text_muted']).pack(anchor='w')
        ctk.CTkLabel(titles, text=t('app_authority'), anchor='w',
                     text_color=COLORS['text_muted']).pack(anchor='w')

    def _build_origin(self, parent):
        text = ctk.CTkTextbox(parent, wrap='word', height=250,
                              fg_color=COLORS['white'],
                              border_width=1, border_color=COLORS['border'])
        text.pack(fill='both', expand=True, pady=(20, 16))
        text.insert('1.0', self._origin_text())
        text.configure(state='disabled')

    def _origin_text(self) -> str:
        """Herkunft, Danksagung und Lizenzhinweis.

        Bewusst als zusammenhängender Text und nicht als Aufzählung von
        Übersetzungsschlüsseln: Diese Angaben sind eine Rechtspflicht, und sie
        dürfen nicht davon abhängen, ob eine Sprachdatei gepflegt wurde.
        """
        return (
            f"Traudi {__version__} · Ministerium der Justiz Rheinland-Pfalz\n"
            f"{PROJECT_URL}\n"
            "\n"
            "Herkunft\n"
            "Traudi ist eine veränderte Fassung von noScribe von Kai Dröge\n"
            "(Hochschule Luzern / Institut für Sozialforschung Frankfurt).\n"
            f"{UPSTREAM_URL}\n"
            "Portierung nach macOS: Philipp Schneider.\n"
            "Portierung nach Linux: Eckhard Kadasch und Florian Dobener.\n"
            f"Diese Fassung wurde {__year__} für die Justiz Rheinland-Pfalz\n"
            "angepasst: eigene Gestaltung, Warteschlange, Installer.\n"
            "\n"
            "Verwendete Verfahren\n"
            "Whisper (OpenAI), faster-whisper (Guillaume Klein),\n"
            "pyannote.audio (Hervé Bredin), CustomTkinter, PyAV, PyTorch.\n"
            "\n"
            "Lizenz\n"
            "GPL-3.0. Traudi ist freie Software: Sie dürfen sie weitergeben\n"
            "und verändern. Es gibt KEINERLEI GARANTIE. Wer Traudi\n"
            "weitergibt, muss den Quellcode und diesen Hinweis mitgeben.\n"
            f"{LICENSE_URL}\n"
            "\n"
            "Landeswappen\n"
            "Das Wappen von Rheinland-Pfalz ist ein Hoheitszeichen und wird\n"
            "hier bewusst nicht abgebildet. Traudi verwendet nur die Farben\n"
            "des Wappens sowie eine eigene Wortmarke.\n"
            "\n"
            "Verzeichnisse\n"
            f"Einstellungen: {self.config_dir}\n"
            f"Protokolle:    {self.config_dir / 'log'}\n"
        )

    def _build_buttons(self, parent):
        secondary = secondary_button()
        row = ctk.CTkFrame(parent, fg_color='transparent')
        row.pack(fill='x')

        ctk.CTkButton(row, text=t('about_close'), width=110,
                      command=self._close).pack(side='right')
        ctk.CTkButton(row, text=t('about_open_logs'), width=130, **secondary,
                      command=lambda: open_in_file_manager(self.config_dir / 'log')
                      ).pack(side='right', padx=(0, 10))
        ctk.CTkButton(row, text=t('about_open_config'), width=150, **secondary,
                      command=lambda: open_in_file_manager(self.config_dir)
                      ).pack(side='right', padx=(0, 10))
        ctk.CTkButton(row, text=t('about_website'), width=110, **secondary,
                      command=lambda: webbrowser.open(PROJECT_URL)
                      ).pack(side='left')

    # -- Ende -------------------------------------------------------------

    def _close(self):
        if not self.winfo_exists():
            return
        self.grab_release()
        self.destroy()
