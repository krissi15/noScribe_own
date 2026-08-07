import importlib.resources as impres
import logging
import gc
import os
import platform
import traceback
from dataclasses import asdict, is_dataclass
from i18n import t

from .whisper_args import build_prompt, resolve_compute_type

logger = logging.getLogger(__name__)


def whisper_proc_entrypoint(args: dict, q):
    """
    Runs in a child process. Streams progress/logs to parent via `q`.
    Messages put on `q` are dicts with one of the following shapes:
      {"type": "log", "level": "info"|"warn"|"error"|"debug", "msg": "..."}
      {"type": "progress", "pct": float, "detail": "..."}   # optional
      {"type": "result", "ok": True, "segments": [...], "info": {...}}
      {"type": "result", "ok": False, "error": str, "trace": str}
    """
    try:
        # Import heavy libs only in the child
        from faster_whisper import WhisperModel
        from faster_whisper.audio import decode_audio
        from faster_whisper.vad import VadOptions, get_speech_timestamps
        import torch
        import yaml
        import i18n

        def plog(level, msg):
            try:
                q.put({"type": "log", "level": level, "msg": str(msg)})
            except Exception:
                pass

        # Initialize python-i18n in child process (PyInstaller uses spawn; no
        # globals shared).
        #
        # TODO: python-i18n is unmaintained for more than five years.
        #
        # See the main file for more information on python-i18n and the
        # approach. Here nothing should actually fail as any possible
        # exceptions were already handled/checked in the main app.
        i18n.set("filename_format", "{locale}.{format}")
        i18n.set("enable_memoization", True)
        i18n.set("fallback", "en")
        i18n.set("locale", args.get("locale", "en"))

        with impres.as_file(impres.files("trans")) as mypath:
            i18n.load_path.append(mypath)

            # Using `t` once here to load the localization files into memory.
            # As there is no `print`, nothing happens really.
            t("app_header")
        
        # determine device
        device = args.get("device", "")
        if device != 'cpu':
            if platform.system() == "Darwin":  # MAC
                device = 'auto'
            elif platform.system() in ('Windows', 'Linux'):
                try:
                    device = 'cuda' if torch.cuda.is_available() and torch.cuda.device_count() > 0 else 'cpu'
                except:
                    device = 'cpu'
            else:
                raise Exception('Platform not supported yet.')
            
        # Die Rechengenauigkeit hängt vom tatsächlich gewählten Gerät ab, und
        # das steht erst jetzt fest: bei device='auto' hat der Elternprozess
        # geraten. int8 ist auf der CPU zwei- bis dreifach schneller als
        # float32, bei einem für Sprachaufnahmen unerheblichen Unterschied.
        compute_type = resolve_compute_type(args.get("compute_type_configured"), device)
        plog("debug", f"device={device} compute_type={compute_type}")

        # Build model in child using provided options
        model = WhisperModel(
            str(args["whisper_model"].path),
            device=device,
            compute_type=compute_type,
            cpu_threads=args["cpu_threads"],
            local_files_only=args.get("local_files_only", True),
        )

        # Define callbacks that forward to parent via queue (not used by faster-whisper directly, but kept for parity)
        def log_cb(level, msg):
            plog(level, msg)

        # Prepare audio and VAD
        audio_path = args.get("audio_path")
        if not audio_path or not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio path does not exist: {audio_path}")

        sampling_rate = model.feature_extractor.sampling_rate
        audio = decode_audio(audio_path, sampling_rate=sampling_rate)
        duration = audio.shape[0] / sampling_rate
        log_cb("info", t('vad'))

        # VAD options
        vad_threshold = float(args.get("vad_threshold", 0.5))
        try:
            vad_parameters = VadOptions(min_silence_duration_ms=500, threshold=vad_threshold, speech_pad_ms=50)
        except TypeError:
            vad_parameters = VadOptions(min_silence_duration_ms=500, onset=vad_threshold, speech_pad_ms=50)

        # Language handling
        language_name = args.get("language_name")
        language_code = args.get("language_code")
        multilingual = False
        whisper_lang = None
        
        if not model.model.is_multilingual and language_code != 'en':
            language_name = 'English'
            language_code = 'en'
            log_cb("info", t('language_en_only'))
        
        if language_name == "Multilingual":
            multilingual = True
            whisper_lang = None
        elif language_name == "Auto":
            whisper_lang = None
        else:
            whisper_lang = language_code

        # Detect language if requested (Auto)
        if language_name == "Auto":
            whisper_lang, language_probability, _ = model.detect_language(
                audio, vad_filter=True, vad_parameters=vad_parameters
            )
            log_cb("info", t('language_detect', lang=whisper_lang, prob=f'{language_probability:.2f}'))

        # Das Beispiel steuert, ob Füllworte ("ähm") erhalten bleiben. Es gibt
        # es je Sprache, deshalb wird es erst hier geladen -- bei "Auto" steht
        # die Sprache erst nach der Erkennung fest.
        style_example = ""
        if args.get("disfluencies", False):
            prompt_file = impres.files("prompts") / "prompt.yml"
        else:
            prompt_file = impres.files("prompts") / "prompt_nd.yml"
        try:
            with prompt_file.open("r", encoding="utf-8") as f:
                style_example = yaml.safe_load(f).get(whisper_lang, "")
        except Exception as e:
            logger.exception(e)
            log_cb('error', t('err_loading_prompt') + '\n')

        # Füllwort-Beispiel und Fachbegriffe gehen zusammen in EINEN
        # initial_prompt. Vorher ging das Beispiel nach `hotwords`, während
        # `initial_prompt` auskommentiert war -- faster-whisper baut aus beiden
        # denselben Kontext, und wer bei gleichzeitiger Angabe gewinnt, hängt
        # von der Fassung ab. Ein Kanal ist vorhersagbar.
        prompt = build_prompt(style_example, args.get("vocabulary", []))
        if prompt:
            plog("debug", f"initial_prompt: {prompt}")

        # Perform transcription (streaming)
        #
        # `audio` statt `audio_path`: die Datei wurde oben bereits vollständig
        # dekodiert. Den Pfad zu übergeben hieße, faster-whisper dekodiert sie
        # ein zweites Mal -- bei einer Stunde Aufnahme eine spürbare Zugabe
        # ganz ohne Gegenwert.
        segments, info = model.transcribe(
            audio,
            language=whisper_lang,
            multilingual=multilingual,
            beam_size=args["beam_size"],
            word_timestamps=args.get("word_timestamps", True),
            initial_prompt=prompt or None,
            # Bei langen Aufnahmen verfängt sich Whisper sonst in
            # Wiederholungsschleifen: es speist den eigenen Ausgabetext als
            # Kontext zurück und schaukelt sich daran auf.
            condition_on_previous_text=args.get("condition_on_previous_text", False),
            vad_filter=args.get("vad_filter", True),
            vad_parameters=vad_parameters,
        )
        
        log_cb('info', t('start_transcription') + '\n')
        
        # Stream segments to parent as they arrive
        for s in segments:
            try:
                seg_d = {
                    "start": getattr(s, "start", None),
                    "end": getattr(s, "end", None),
                    "text": getattr(s, "text", None),
                }
                words = getattr(s, "words", None)
                if words:
                    seg_d["words"] = [
                        {
                            "word": getattr(w, "word", None),
                            "start": getattr(w, "start", None),
                            "end": getattr(w, "end", None),
                            "prob": getattr(w, "probability", None),
                        }
                        for w in words
                    ]
                q.put({"type": "segment", "segment": seg_d})
            except Exception:
                # Best-effort; continue on serialization issues
                pass

        # info into dict
        if is_dataclass(info):
            info_dict = asdict(info)
        else:
            info_dict = {}
            for k in ("language", "language_probability", "duration", "sample_rate"):
                if hasattr(info, k):
                    info_dict[k] = getattr(info, k)
        # Ensure duration is available
        info_dict.setdefault("duration", duration)

        try:
            q.put({"type": "result", "ok": True, "info": info_dict})
        except Exception:
            pass

        # Cleanup VRAM (harmless on CPU)
        try:
            del model
        except Exception:
            pass
        try:
            torch.cuda.empty_cache()
        except Exception:
            pass
        gc.collect()
        plog("debug", "Subprocess finished cleanly.")

    except Exception as e:
        try:
            q.put({
                "type": "result",
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
                "trace": traceback.format_exc(),
            })
        except Exception:
            pass
