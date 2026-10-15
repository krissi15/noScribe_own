# Traudi - Einstellungen für die Rechenprozesse
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

"""Damit Windows die Rechenprozesse nicht ausbremst.

Whisper und pyannote laufen in eigenen Prozessen ohne Fenster. Windows 10/11
hält solche Prozesse für Hintergrundarbeit und drosselt sie
("Power Throttling" / EcoQoS): niedrigere Taktrate, und auf Prozessoren mit
Effizienzkernen (Intel ab 12. Generation) bevorzugt auf diesen langsamen
Kernen. Auf einem Notebook im Akku- oder Energiesparbetrieb kann das die
Sprechererkennung um ein Vielfaches verlangsamen.

`disable_power_throttling` meldet den Prozess bei Windows als
leistungsbedürftig ab -- dasselbe, was der Task-Manager beim Abschalten des
"Effizienzmodus" tut. Auf anderen Systemen geschieht nichts.
"""

import platform

# Aus processthreadsapi.h
_PROCESS_POWER_THROTTLING = 4            # PROCESS_INFORMATION_CLASS.ProcessPowerThrottling
_PROCESS_POWER_THROTTLING_CURRENT_VERSION = 1
_PROCESS_POWER_THROTTLING_EXECUTION_SPEED = 0x1


def disable_power_throttling() -> bool:
    """Schaltet die Drosselung für den laufenden Prozess ab.

    Gibt zurück, ob Windows die Einstellung angenommen hat; außerhalb von
    Windows (und vor Windows 8) immer False. Wirft nie.
    """
    if platform.system() != 'Windows':
        return False
    try:
        import ctypes
        from ctypes import wintypes

        class PROCESS_POWER_THROTTLING_STATE(ctypes.Structure):
            _fields_ = [('Version', wintypes.ULONG),
                        ('ControlMask', wintypes.ULONG),
                        ('StateMask', wintypes.ULONG)]

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        set_info = kernel32.SetProcessInformation
        set_info.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        set_info.restype = wintypes.BOOL
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE

        # ControlMask: diese Eigenschaft regeln wir selbst;
        # StateMask 0: und zwar "nicht drosseln".
        state = PROCESS_POWER_THROTTLING_STATE(
            _PROCESS_POWER_THROTTLING_CURRENT_VERSION,
            _PROCESS_POWER_THROTTLING_EXECUTION_SPEED,
            0)
        return bool(set_info(kernel32.GetCurrentProcess(), _PROCESS_POWER_THROTTLING,
                             ctypes.byref(state), ctypes.sizeof(state)))
    except Exception:
        return False


def thread_count(value):
    """Liest die gewünschte Thread-Zahl; None, wenn nichts Brauchbares kommt."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None
