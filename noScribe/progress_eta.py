# Traudi - Restzeit für lange Arbeitsschritte
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

"""Schätzt, wie lange ein Schritt der Sprechererkennung noch dauert.

Der teure Schritt ("embeddings") arbeitet gleich große Stapel ab; eine
lineare Hochrechnung aus dem bisherigen Tempo trifft daher gut. Geschätzt
wird erst, wenn genug gemessen ist -- eine Zahl, die in den ersten Sekunden
wild springt, verunsichert mehr, als sie hilft.
"""

import math
import time


class RemainingTime:
    def __init__(self, clock=time.monotonic, min_seconds: float = 20, min_pct: float = 2):
        self._clock = clock
        self._min_seconds = min_seconds
        self._min_pct = min_pct
        self._step = None
        self._start = 0.0
        self._start_pct = 0.0

    def update(self, step: str, pct: float):
        """Neuer Stand; gibt die geschätzte Restzeit in Sekunden zurück oder
        None, solange noch keine verlässliche Schätzung möglich ist."""
        now = self._clock()
        if step != self._step:
            self._step, self._start, self._start_pct = step, now, pct
            return None
        elapsed = now - self._start
        progressed = pct - self._start_pct
        if pct >= 100 or elapsed < self._min_seconds or progressed < self._min_pct:
            return None
        return elapsed * (100 - pct) / progressed


def format_duration(seconds: float) -> str:
    """`45 min`, `1 h 5 min` -- auf volle Minuten aufgerundet."""
    minutes = max(1, math.ceil(seconds / 60))
    if minutes < 60:
        return f'{minutes} min'
    hours, minutes = divmod(minutes, 60)
    return f'{hours} h {minutes} min' if minutes else f'{hours} h'
