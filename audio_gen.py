from __future__ import annotations

import json
import re
import subprocess
import threading
import wave
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).parent
AUDIO_DIR = ROOT / "models" / "audio"
TMP_DIR = ROOT / "audio_tmp"
VOICE_MODEL = AUDIO_DIR / "pt_BR-faber-medium.onnx"
VOICE_CONFIG = AUDIO_DIR / "pt_BR-faber-medium.onnx.json"
SCENE_MODEL = "facebook/musicgen-medium"
SCENE_SAMPLE_RATE = 32000
VOICE_SAMPLE_RATE = 22050
MAX_SCENE_SECONDS = 30

_lock = threading.Lock()

_voice = None
_voice_ready = False
_scene = None
_scene_ready = False


def _ffmpeg_bin() -> Path:
    from imageio_ffmpeg import get_ffmpeg_exe
    return Path(get_ffmpeg_exe())


def _write_wav(path: Path, samples: np.ndarray, rate: int) -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


def voice_available() -> bool:
    return VOICE_MODEL.exists() and VOICE_CONFIG.exists()


def scene_available() -> bool:
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(SCENE_MODEL, local_files_only=True)
        return True
    except Exception:
        return False


def status() -> dict[str, Any]:
    return {
        "voice": voice_available(),
        "scene": scene_available(),
        "sceneEngine": "musicgen",
        "busy": _lock.locked(),
    }


def _voice_model() -> Any:
    global _voice, _voice_ready
    if _voice_ready:
        return _voice
    from piper.voice import PiperVoice
    _voice = PiperVoice.load(
        str(VOICE_MODEL),
        str(VOICE_CONFIG),
        espeak_data_dir=str(ROOT / ".venv" / "Lib" / "site-packages" / "piper" / "espeak-ng-data"),
        include_alignments=False,
    )
    _voice_ready = True
    return _voice


def _scene_model() -> tuple[Any, Any]:
    global _scene, _scene_ready
    if _scene_ready:
        return _scene
    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    processor = AutoProcessor.from_pretrained(SCENE_MODEL, low_cpu_mem_usage=True)
    model = MusicgenForConditionalGeneration.from_pretrained(
        SCENE_MODEL, torch_dtype=torch.float16, low_cpu_mem_usage=True
    )
    model.to("cuda")
    model.eval()
    _scene = (processor, model)
    _scene_ready = True
    return _scene


_SPEECH_RE = re.compile(
    r"\b(falar|falando|fala|diga|diz|dizer|dizendo|conta|contando|"
    r"narra|narrando|narração|voz|vozes|diálogo|dialogo|conversa|"
    r"pergunta|responde|legenda|explica|explicando|ensina|ensinando|"
    r"anuncio|anúncio|noticia|notícia|grita|gritando|sussurra|sussurrando)\b",
    re.IGNORECASE,
)


def is_speech_prompt(prompt: str) -> bool:
    return bool(_SPEECH_RE.search(prompt or ""))


def _clean_for_speech(prompt: str) -> str:
    text = re.sub(r"\s*\*\*.*?\*\*", " ", prompt or "")
    text = re.sub(r"\s{2,}", " ", text).strip()
    if len(text) > 260:
        text = text[:257].rsplit(" ", 1)[0]
    return text or "O ORYN enviou esta mensagem com voz."


def piper_wav(text: str, out_wav: Path) -> None:
    voice = _voice_model()
    voice.synthesize_wav(text, wave.open(str(out_wav), "wb"))


def musicgen_wav(prompt: str, duration: float, out_wav: Path) -> None:
    import torch
    processor, model = _scene_model()
    seconds = max(1.0, min(float(duration), MAX_SCENE_SECONDS))
    inputs = processor(text=[prompt], padding=True, return_tensors="pt").to("cuda")
    with torch.inference_mode():
        out = model.generate(
            **inputs,
            max_new_tokens=int(seconds * 50) + 1,
            do_sample=True,
            temperature=1.0,
            top_k=250,
            guidance_scale=3.0,
        )
    audio = out[0, 0].float().cpu().numpy()
    torch.cuda.empty_cache()
    _write_wav(out_wav, audio, SCENE_SAMPLE_RATE)


def render_audio(prompt: str, duration: float, out_wav: Path) -> str:
    if is_speech_prompt(prompt):
        piper_wav(_clean_for_speech(prompt), out_wav)
        return "voice"
    musicgen_wav(prompt, duration, out_wav)
    return "scene"


def mux_audio(video_path: Path, audio_wav: Path, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            str(_ffmpeg_bin()),
            "-y",
            "-i", str(video_path),
            "-i", str(audio_wav),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(out_path),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not out_path.exists():
        raise RuntimeError(proc.stderr[-1500:] or "ffmpeg falhou no mux de áudio.")