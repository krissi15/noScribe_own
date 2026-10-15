import importlib.resources as impres
import os
import platform
import time
import traceback
import wave

import numpy as np

if platform.system() == "Darwin" and platform.machine() == "x86_64":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("MKL_THREADING_LAYER", "GNU")
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")  # temp workaround for iomp5 dup

def read_pcm_wav(path) -> tuple:
    """Liest die von Traudi erzeugte WAV-Datei als (Kanäle, Frames), float32.

    Liefert dasselbe wie ``torchaudio.load``: Werte zwischen -1 und 1, Form
    (Kanäle, Frames). ``torchaudio.load`` selbst ist im Windows-Paket nicht
    benutzbar -- ab torchaudio 2.8 hängt es an torchcodec, und das findet dort
    seine DLLs nicht ("Couldn't find appropriate backend to handle uri ...").
    Einen Decoder braucht es hier aber gar nicht: ``audio/convert.py`` schreibt
    immer PCM, 16 Bit, 16 kHz, mono, und das liest die Standardbibliothek.
    """
    with wave.open(str(path), 'rb') as wav:
        channels = wav.getnchannels()
        width = wav.getsampwidth()
        rate = wav.getframerate()
        raw = wav.readframes(wav.getnframes())
    if width != 2:
        raise ValueError(f'{path}: erwartet 16-Bit-PCM, gefunden {8 * width} Bit')
    # In einem Schritt nach float32 und skaliert; bei mono ohne weitere Kopie.
    # Eine Stunde Audio sind so gut 0,2 GB statt 0,6 GB Spitzenbedarf mehr.
    pcm = np.frombuffer(raw, dtype='<i2')
    samples = np.empty(pcm.shape, dtype=np.float32)
    np.multiply(pcm, 1.0 / 32768.0, out=samples, casting='unsafe')
    del pcm, raw
    if channels == 1:
        return samples.reshape(1, -1), rate
    return samples.reshape(-1, channels).T.copy(), rate


def _prepare_process(args: dict, plog):
    """Gemeinsamer Anfang beider Einstiegspunkte: offline, ungedrosselt,
    Thread-Zahl. Gibt torch zurück."""
    # Erst hier importiert: die Tests laden diese Datei einzeln, ohne Paket.
    from . import privacy, proc_tuning
    privacy.go_offline()
    if proc_tuning.disable_power_throttling():
        plog("debug", "Windows-Energiedrosselung für diesen Prozess abgeschaltet")
    import torch
    if platform.system() == "Darwin" and platform.machine() == "x86_64":
        torch.set_num_threads(1)
    else:
        threads = proc_tuning.thread_count(args.get("threads"))
        if threads:
            torch.set_num_threads(threads)
    plog("debug", f"torch threads: {torch.get_num_threads()}")
    return torch


def _resolve_device(args: dict, torch) -> str:
    device = args.get("device", "")
    if device != 'cpu':
        if platform.system() == "Darwin":  # MAC
            device = 'mps' if platform.mac_ver()[0] >= '12.3' and torch.backends.mps.is_available() else 'cpu'
        elif platform.system() in ('Windows', 'Linux'):
            try:
                device = 'cuda' if torch.cuda.is_available() and torch.cuda.device_count() > 0 else 'cpu'
            except:
                device = 'cpu'
        else:
            raise Exception('Platform not supported yet.')
    return device


def _load_pipeline(args: dict, torch, device: str):
    from pyannote.audio import Pipeline
    # Der Elternprozess entscheidet, welche Ablage benutzt wird: das
    # Nutzerverzeichnis (dort darf ohne Administratorrechte nachgelegt
    # werden) oder das Programmverzeichnis. Fehlt die Angabe, gilt wie
    # bisher das gebündelte Verzeichnis.
    pyannote_dir = args.get("pyannote_dir") or ""
    if pyannote_dir:
        pipeline = Pipeline.from_pretrained(pyannote_dir)
    else:
        with impres.as_file(impres.files("pyannote")) as mypath:
            pipeline = Pipeline.from_pretrained(mypath)
    pipeline.to(torch.device(device))
    return pipeline


def _diarize(pipeline, waveform, sample_rate, num_speakers, hook):
    audio = {"waveform": waveform, "sample_rate": sample_rate}
    if num_speakers is not None:
        return pipeline(audio, hook=hook, num_speakers=num_speakers)
    return pipeline(audio, hook=hook)


def _segments(diarization) -> list:
    return [{'start': int(turn.start * 1000),
             'end': int(turn.end * 1000),
             'label': speaker}
            for turn, speaker in diarization.speaker_diarization]


def pyannote_proc_entrypoint(args: dict, q):
    """Runs diarization in a child process and streams progress/logs.
    Messages:
      {"type":"log","level":"info|warn|error|debug","msg":str}
      {"type":"progress","step":str,"pct":int}
      {"type":"result","ok":True,"segments":[{"start":ms,"end":ms,"label":str}],"seconds":float}
      {"type":"result","ok":False,"error":str,"trace":str}
    """
    device = ''

    def plog(level, msg):
        try:
            q.put({"type": "log", "level": level, "msg": str(msg)})
        except Exception:
            pass

    try:
        torch = _prepare_process(args, plog)

        class SimpleProgressHook:
            def __init__(self):
                self.step_name = None

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def __call__(self, step_name, step_artifact, file=None, total=None, completed=None):
                if completed is None:
                    completed = total = 1
                pct = int(completed / total * 100) if total else 100
                if pct > 100:
                    pct = 100
                try:
                    q.put({"type": "progress", "step": str(step_name), "pct": pct})
                except Exception:
                    pass

        audio_file = args.get("audio_path")
        num_speakers = args.get("num_speakers")
        if not os.path.exists(audio_file):
            raise FileNotFoundError(audio_file)

        plog("debug", "Subprocess (diarize) started. Initializing PyAnnote pipeline...")
        device = _resolve_device(args, torch)
        pipeline = _load_pipeline(args, torch, device)
        if args.get("skip_silent_embeddings", True):
            from . import diarization_speed
            diarization_speed.install(pipeline, log=lambda m: plog("debug", m))

        samples, sample_rate = read_pcm_wav(audio_file)
        waveform = torch.from_numpy(samples)

        started = time.perf_counter()
        with SimpleProgressHook() as hook:
            diarization = _diarize(pipeline, waveform, sample_rate, num_speakers, hook)
        seconds = time.perf_counter() - started
        plog("debug", f"diarization took {seconds:.1f} s")
        if hasattr(pipeline, 'traudi_passes'):
            ours, theirs = pipeline.traudi_passes
            plog("debug", f"embedding network passes: {ours} (pyannote: {theirs})")

        try:
            q.put({"type": "result", "ok": True, "segments": _segments(diarization),
                   "seconds": seconds})
        except Exception:
            pass

    except Exception as e:
        _put_error(q, e, device)


def pyannote_compare_entrypoint(args: dict, q):
    """Für ``--selftest``: dieselbe Aufnahme einmal mit dem Original-
    ``get_embeddings`` von pyannote und einmal mit der Abkürzung aus
    ``diarization_speed``. Beide Läufe benutzen dieselbe geladene Pipeline.

    Ergebnis: {"type":"result","ok":True,"identical":bool,"installed":bool,
               "segments":int,"speakers":int,"passes":int,"passes_original":int,
               "seconds_original":float,"seconds_fast":float,"centroid_diff":float}
    """
    device = ''

    def plog(level, msg):
        try:
            q.put({"type": "log", "level": level, "msg": str(msg)})
        except Exception:
            pass

    try:
        torch = _prepare_process(args, plog)
        import numpy as np
        from . import diarization_speed

        device = _resolve_device(args, torch)
        pipeline = _load_pipeline(args, torch, device)
        samples, sample_rate = read_pcm_wav(args["audio_path"])
        waveform = torch.from_numpy(samples)
        num_speakers = args.get("num_speakers")

        def nohook(*a, **k):
            pass

        # Aufwärmen, damit der erste gemessene Lauf nicht die Einrichtung
        # von torch mitbezahlt.
        _diarize(pipeline, waveform[:, :10 * sample_rate], sample_rate, None, nohook)

        started = time.perf_counter()
        reference = _diarize(pipeline, waveform, sample_rate, num_speakers, nohook)
        seconds_original = time.perf_counter() - started

        installed = diarization_speed.install(pipeline)
        started = time.perf_counter()
        fast = _diarize(pipeline, waveform, sample_rate, num_speakers, nohook)
        seconds_fast = time.perf_counter() - started
        passes, passes_original = getattr(pipeline, 'traudi_passes', (0, 0))

        ref_segments = _segments(reference)
        fast_segments = _segments(fast)
        try:
            a = np.asarray(reference.speaker_embeddings, dtype=np.float64)
            b = np.asarray(fast.speaker_embeddings, dtype=np.float64)
            centroid_diff = float(np.max(np.abs(a - b))) if a.size else 0.0
        except Exception:  # None oder andere Form
            centroid_diff = float('nan')
        q.put({
            "type": "result", "ok": True,
            "installed": installed,
            "identical": ref_segments == fast_segments,
            "segments": len(ref_segments),
            "speakers": len({s['label'] for s in ref_segments}),
            "passes": passes,
            "passes_original": passes_original,
            "seconds_original": seconds_original,
            "seconds_fast": seconds_fast,
            "centroid_diff": centroid_diff,
        })
    except Exception as e:
        _put_error(q, e, device)


def _put_error(q, e, device):
    try:
        error_str = f"{type(e).__name__}: {e}"
        error_str += f' (device_{device[:3]})' # device_cpu or device_cud or device_mps
        q.put({
            "type": "result",
            "ok": False,
            "error": error_str,
            "trace": traceback.format_exc(),
        })
    except Exception:
        pass
