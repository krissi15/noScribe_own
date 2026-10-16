# Traudi - Messmodus für Vergleiche zwischen Versionen und Rechnern
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

"""`Traudi.exe <audio> <ausgabe.html> --no-gui --benchmark`

Schreibt neben das Transkript `<ausgabe>.benchmark.json`: Rechner (Prozessor,
Kerne, Arbeitsspeicher, Grafik), Traudi-Version, Einstellungen, Prüfsumme und
Länge der Aufnahme sowie die Dauer jedes Arbeitsschritts. Aus mehreren
solchen Dateien baut `scripts/benchmark_report.py` die Vergleichsseite.

Bewusst ohne schwere Importe und ohne Netz: Die Angaben stammen aus dem
Betriebssystem selbst. Fehlt eine, steht dort `null` -- der Messlauf
scheitert nie an der Beschreibung des Rechners.
"""

import datetime
import json
import os
import platform
import subprocess
from pathlib import Path

SCHEMA = 1


def cpu_name() -> str:
    system = platform.system()
    try:
        if system == 'Windows':
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r'HARDWARE\DESCRIPTION\System\CentralProcessor\0')
            return str(winreg.QueryValueEx(key, 'ProcessorNameString')[0]).strip()
        if system == 'Linux':
            for line in Path('/proc/cpuinfo').read_text().splitlines():
                if line.startswith('model name'):
                    return line.split(':', 1)[1].strip()
        if system == 'Darwin':
            return subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'],
                                  capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        pass
    return platform.processor() or ''


def ram_gb():
    system = platform.system()
    try:
        if system == 'Windows':
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                            ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                            ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                            ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                            ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]

            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return round(status.ullTotalPhys / 1024 ** 3, 1)
        if system == 'Linux':
            for line in Path('/proc/meminfo').read_text().splitlines():
                if line.startswith('MemTotal:'):
                    return round(int(line.split()[1]) / 1024 ** 2, 1)
    except Exception:
        pass
    return None


def gpu_names() -> list:
    try:
        if platform.system() == 'Windows':
            out = subprocess.run(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command',
                 '(Get-CimInstance Win32_VideoController).Name'],
                capture_output=True, text=True, timeout=15,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            names = [line.strip() for line in out.stdout.splitlines() if line.strip()]
            # Fernwartungs- und Spiegeltreiber (DameWare u. ä.) sind keine Grafikkarten.
            return [n for n in names if 'mirror' not in n.lower()]
        out = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                             capture_output=True, text=True, timeout=10)
        return [line.strip() for line in out.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def physical_cores():
    try:
        import cpufeature
        return int(cpufeature.CPUFeature['num_physical_cores'])
    except Exception:
        return None


def machine() -> dict:
    return {
        'cpu': cpu_name(),
        'cores_physical': physical_cores(),
        'cores_logical': os.cpu_count(),
        'ram_gb': ram_gb(),
        'gpus': gpu_names(),
        'os': platform.platform(),
    }


def audio_seconds(path):
    """Länge der Aufnahme laut Container; None, wenn PyAV sie nicht kennt."""
    try:
        import av
        with av.open(str(path)) as container:
            if container.duration:
                return round(container.duration / 1_000_000, 1)
    except Exception:
        pass
    return None


def phase_seconds(status_log) -> dict:
    """[(Status, Zeitpunkt), ...] -> {Status: Sekunden bis zum nächsten Status}."""
    out = {}
    for (name, start), (_, end) in zip(status_log, status_log[1:]):
        out[name] = round(out.get(name, 0.0) + (end - start), 1)
    return out


def report(job, version: str, settings: dict, audio_sha256: str = '') -> dict:
    phases = phase_seconds(getattr(job, 'status_log', []))
    work = {k: v for k, v in phases.items() if k not in ('waiting',)}
    total = round(sum(work.values()), 1)
    seconds = audio_seconds(job.audio_file)
    return {
        'schema': SCHEMA,
        'traudi_version': version,
        'measured_at': datetime.datetime.now().astimezone().replace(microsecond=0).isoformat(),
        'machine': machine(),
        'audio': {
            'file': Path(str(job.audio_file)).name,
            'sha256': audio_sha256,
            'seconds': seconds,
        },
        'settings': settings,
        'result': {
            'status': getattr(job.status, 'value', str(job.status)),
            'transcript': Path(str(job.transcript_file)).name,
        },
        'seconds': {
            'audio_conversion': work.get('audio_conversion'),
            'speaker_identification': work.get('speaker_identification'),
            'transcription': work.get('transcription'),
            'total': total,
        },
        # Wie viele Sekunden Rechenzeit je Sekunde Aufnahme: < 1 ist schneller
        # als Echtzeit.
        'realtime_factor': round(total / seconds, 2) if seconds else None,
    }


def write(path, data: dict) -> Path:
    path = Path(path)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    return path


def sidecar_path(transcript_file) -> Path:
    p = Path(str(transcript_file))
    return p.with_name(p.stem + '.benchmark.json')
