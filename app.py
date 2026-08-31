from __future__ import annotations

import json
import os
import re
import shutil
import time
import html
import urllib.parse
from pathlib import Path
from typing import Any

import requests
import audio_gen
import agent
from flask import Flask, Response, jsonify, request, send_from_directory

ROOT = Path(__file__).parent
FRONTEND = ROOT / "frontend"
CONFIG_FILE = ROOT / "config.json"

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_COMFYUI_URL = "http://127.0.0.1:8188"

COMFYUI_CANDIDATE_ROOTS = [
    Path(r"C:\ComfyUI\ComfyUI"),
    Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "Comfy-Desktop" / "ComfyUI-Shared",
]

MAX_UPLOAD_BYTES = 100 * 1024 * 1024

SEARCH_DB = ROOT / "search_memory.db"

app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="/static")


def load_config() -> dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


_cfg = load_config()
OLLAMA_URL = _cfg.get("ollamaUrl") or os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_URL)
COMFYUI_URL = _cfg.get("comfyuiUrl") or os.getenv("COMFYUI_URL", DEFAULT_COMFYUI_URL)
COMFYUI_URL = COMFYUI_URL.rstrip("/")
OLLAMA_URL = OLLAMA_URL.rstrip("/")

_object_info_cache: dict[str, Any] = {}
_object_info_ts: float = 0.0


def comfyui_object_info() -> dict[str, Any]:
    global _object_info_cache, _object_info_ts
    if time.time() - _object_info_ts < 30:
        return _object_info_cache
    try:
        r = requests.get(f"{COMFYUI_URL}/object_info", timeout=10)
        r.raise_for_status()
        _object_info_cache = r.json()
        _object_info_ts = time.time()
    except requests.RequestException:
        pass
    return _object_info_cache


def comfy_model_list(class_type: str, input_name: str) -> list[str]:
    info = comfyui_object_info()
    node = info.get(class_type, {})
    req = node.get("input", {}).get("required", {})
    combo = req.get(input_name, [None, None])
    if isinstance(combo, tuple) and len(combo) > 0 and isinstance(combo[0], list):
        return combo[0]
    return []


def detect_comfyui_roots() -> list[Path]:
    roots = []
    env_root = os.getenv("COMFYUI_ROOT")
    if env_root:
        p = Path(env_root)
        if p.exists():
            roots.append(p)
    for candidate in COMFYUI_CANDIDATE_ROOTS:
        if candidate.exists() and candidate not in roots:
            roots.append(candidate)
    return roots


def find_model_file(filename: str, subfolders: list[str]) -> bool:
    roots = detect_comfyui_roots()
    for root in roots:
        for sub in subfolders:
            if (root / sub / filename).exists():
                return True
    return False


def comfy_available() -> bool:
    try:
        r = requests.get(f"{COMFYUI_URL}/system_stats", timeout=3)
        return r.ok
    except requests.RequestException:
        return False


def comfy_view_url(filename: str, subfolder: str = "", ftype: str = "output") -> str:
    return f"{COMFYUI_URL}/view?filename={urllib.parse.quote(filename)}&subfolder={urllib.parse.quote(subfolder)}&type={urllib.parse.quote(ftype)}"


def map_comfy_error(text: str) -> str:
    lower = text.lower()
    if "out of memory" in lower or "oom" in lower or "cuda" in lower and "memory" in lower:
        return "A geração falhou por falta de memória da GPU. Tente resolução menor ou menos frames."
    if "value not in list" in lower:
        match = re.search(r"Value not in list:\s*([^\s]+)", text, re.IGNORECASE)
        missing = match.group(1) if match else "o modelo necessário"
        return f"O modelo '{missing}' não foi encontrado no ComfyUI. Verifique se está em models/diffusion_models."
    if "no module named" in lower or "not found" in lower:
        return "O ComfyUI não possui o nó necessário. Atualize o ComfyUI para a versão mais recente."
    if "invalid prompt" in lower:
        return "O workflow contém parâmetros inválidos para o modelo selecionado."
    return f"ComfyUI retornou erro: {text[:400]}"


@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/css/<path:filename>")
def css_static(filename):
    return send_from_directory(FRONTEND / "css", filename)


@app.get("/js/<path:filename>")
def js_static(filename):
    return send_from_directory(FRONTEND / "js", filename)


@app.get("/favicon.ico")
def favicon():
    return send_from_directory(FRONTEND, "favicon.ico") if (FRONTEND / "favicon.ico").exists() else ("", 404)


@app.get("/img/<path:filename>")
def img_static(filename):
    return send_from_directory(FRONTEND / "img", filename)


@app.get("/api/status")
def status():
    ollama_online = False
    comfyui_online = comfy_available()
    models: list[str] = []
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        r.raise_for_status()
        ollama_online = True
        models = [m.get("name", "") for m in r.json().get("models", [])]
    except requests.RequestException:
        pass

    flux_klein = find_model_file("flux-2-klein-4b.safetensors", ["models/diffusion_models"])
    wan_5b = find_model_file("wan2.2_ti2v_5B_fp16.safetensors", ["models/diffusion_models"])
    wan_14b_hi = find_model_file("wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors", ["models/diffusion_models"])
    wan_14b_lo = find_model_file("wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors", ["models/diffusion_models"])
    vae_wan = find_model_file("wan_2.1_vae.safetensors", ["models/vae"]) or find_model_file("wan2.2_vae.safetensors", ["models/vae"])
    clip_umt5 = find_model_file("umt5_xxl_fp8_e4m3fn_scaled.safetensors", ["models/text_encoders", "models/clip"])
    flux_clip = find_model_file("qwen_3_4b_fp4_flux2.safetensors", ["models/text_encoders/split_files/text_encoders"])
    flux_vae = find_model_file("flux2-vae.safetensors", ["models/vae/split_files/vae"])

    flux_klein_ready = comfyui_online and flux_klein and flux_clip and flux_vae
    wan_5b_ready = comfyui_online and wan_5b and vae_wan and clip_umt5
    wan_14b_ready = comfyui_online and wan_14b_hi and wan_14b_lo and vae_wan and clip_umt5

    try:
        _du = shutil.disk_usage(ROOT)
        disk_free_gb = _du.free // (1024**3)
        disk_total_gb = _du.total // (1024**3)
    except OSError:
        disk_free_gb = disk_total_gb = None

    try:
        audio_ready = audio_gen.status()
    except Exception:
        audio_ready = {"voice": False, "scene": False, "sceneEngine": "musicgen", "busy": False}

    return jsonify({
        "backend": True,
        "ollama": ollama_online,
        "models": models,
        "vision": any(n.lower().split(":", 1)[0] in {"llava", "gemma3", "qwen2.5-vl"} for n in models),
        "audio": audio_ready,
        "comfyui": comfyui_online,
        "flux_klein": flux_klein_ready,
        "wan_5b": wan_5b_ready,
        "wan_14b": wan_14b_ready,
        "disk_free_gb": disk_free_gb,
        "disk_total_gb": disk_total_gb,
        "comfyui_url": COMFYUI_URL,
        "ollama_url": OLLAMA_URL,
    })


@app.post("/api/config")
def set_config():
    data = request.get_json(silent=True) or {}
    cfg = load_config()
    for key in ("ollamaUrl", "comfyuiUrl"):
        if key in data:
            cfg[key] = str(data[key]).strip()
    save_config(cfg)
    global OLLAMA_URL, COMFYUI_URL, _object_info_ts
    if "ollamaUrl" in data:
        OLLAMA_URL = cfg["ollamaUrl"].rstrip("/")
    if "comfyuiUrl" in data:
        COMFYUI_URL = cfg["comfyuiUrl"].rstrip("/")
        _object_info_ts = 0
    return jsonify({"ok": True, "ollamaUrl": OLLAMA_URL, "comfyuiUrl": COMFYUI_URL})


@app.get("/api/config")
def get_config():
    return jsonify({
        "ollamaUrl": OLLAMA_URL,
        "comfyuiUrl": COMFYUI_URL,
        "model_files": {
            "flux_klein": find_model_file("flux-2-klein-4b.safetensors", ["models/diffusion_models"]),
            "wan_5b": find_model_file("wan2.2_ti2v_5B_fp16.safetensors", ["models/diffusion_models"]),
            "wan_14b_high": find_model_file("wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors", ["models/diffusion_models"]),
            "wan_14b_low": find_model_file("wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors", ["models/diffusion_models"]),
            "vae_wan": find_model_file("wan_2.1_vae.safetensors", ["models/vae"]) or find_model_file("wan2.2_vae.safetensors", ["models/vae"]),
            "clip_umt5": find_model_file("umt5_xxl_fp8_e4m3fn_scaled.safetensors", ["models/text_encoders"]),
            "clip_flux2": find_model_file("qwen_3_4b_fp4_flux2.safetensors", ["models/text_encoders/split_files/text_encoders"]),
            "vae_flux2": find_model_file("flux2-vae.safetensors", ["models/vae/split_files/vae"]),
        },
    })


@app.get("/api/media")
def media():
    fn = request.args.get("filename", "").strip()
    sub = request.args.get("subfolder", "").strip()
    ftype = request.args.get("type", "output").strip()
    if not fn or "/" in fn or "\\" in fn or ".." in fn:
        return jsonify({"error": "Nome de arquivo inválido."}), 400
    try:
        url = comfy_view_url(fn, sub, ftype)
        r = requests.get(url, timeout=30)
        if not r.ok:
            return jsonify({"error": "Arquivo não encontrado no ComfyUI."}), 404
        ct = r.headers.get("Content-Type", "application/octet-stream")
        return Response(r.content, mimetype=ct, headers={"Content-Disposition": f'attachment; filename="{fn}"'})
    except requests.RequestException as e:
        return jsonify({"error": f"Erro ao buscar arquivo: {e}"}), 502


def _search_db():
    import sqlite3
    con = sqlite3.connect(str(SEARCH_DB))
    con.execute("CREATE TABLE IF NOT EXISTS search_items(href TEXT PRIMARY KEY, query TEXT NOT NULL, title TEXT, body TEXT, added_at REAL NOT NULL)")
    return con


def _store_search_results(query: str, results: list[dict[str, str]]) -> None:
    if not results:
        return
    try:
        con = _search_db()
        try:
            now = time.time()
            for r in results:
                href = (r.get("href") or "").strip()
                if not href:
                    continue
                con.execute(
                    "INSERT OR REPLACE INTO search_items(href, query, title, body, added_at) VALUES(?,?,?,?,?)",
                    (href, query, (r.get("title") or "").strip(), (r.get("body") or "").strip(), now),
                )
            con.commit()
        finally:
            con.close()
    except Exception:
        pass


def _cached_results_for(query: str, max_results: int = 5) -> list[dict[str, str]]:
    words = [w for w in re.split(r"\W+", query.lower()) if len(w) > 3]
    if not words:
        return []
    try:
        con = _search_db()
        try:
            rows = con.execute("SELECT href, title, body FROM search_items").fetchall()
        finally:
            con.close()
    except Exception:
        return []
    q = query.lower()
    scored = []
    for href, title, body in rows:
        text = f"{title} {body}".lower()
        if q in text:
            scored.append((2 + len(words), {"title": title, "href": href, "body": body}))
            continue
        score = sum(1 for w in words if w in text)
        if score >= 2:
            scored.append((score, {"title": title, "href": href, "body": body}))
    scored.sort(key=lambda t: -t[0])
    return [x[1] for x in scored[:max_results]]


def _search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        try:
            results = list(DDGS().text(query, max_results=max_results, timeout=8))
        except TypeError:
            results = list(DDGS().text(query, max_results=max_results))
        out = []
        for r in results or []:
            if not isinstance(r, dict):
                continue
            href = str(r.get("href", "") or r.get("url", ""))
            if not href:
                continue
            out.append({
                "title": str(r.get("title", "")),
                "href": href,
                "body": str(r.get("body", "") or r.get("snippet", "")),
            })
        if out:
            return out
    except Exception:
        pass
    return _bing_search(query, max_results)


def _bing_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    }
    try:
        url = "https://www.bing.com/search?q=" + urllib.parse.quote(query) + "&count=" + str(max_results)
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
    except requests.RequestException:
        return []
    out = []
    for block in re.findall(r'<li class="b_algo".*?</li>', r.text, re.S):
        m_url = re.search(r'<h2[^>]*><a[^>]*href="([^"]+)"', block)
        m_title = re.search(r"<h2[^>]*><a[^>]*>(.*?)</a>", block, re.S)
        m_snip = re.search(r"<p[^>]*>(.*?)</p>", block, re.S)
        if not m_url:
            continue
        href = html.unescape(m_url.group(1))
        title = re.sub(r"<[^>]+>", "", html.unescape(m_title.group(1))) if m_title else ""
        body = re.sub(r"<[^>]+>", "", html.unescape(m_snip.group(1))) if m_snip else ""
        out.append({"title": title.strip(), "href": href, "body": body.strip()})
        if len(out) >= max_results:
            break
    return out


def _web_results_block(query: str) -> str:
    try:
        results = _search_web(query)
        _store_search_results(query, results)
    except Exception:
        results = []
    if not results:
        results = _cached_results_for(query)
    if not results:
        return ""
    lines = []
    for i, r in enumerate(results[:5], 1):
        title = (r.get("title") or "").strip()
        body = (r.get("body") or "").strip()
        href = (r.get("href") or "").strip()
        if not href and not body:
            continue
        if len(body) > 250:
            body = body[:250] + "\u2026"
        lines.append(f"{i}. {title} \u2014 {body} ({href})")
    return "[Resultados da web]\n" + "\n".join(lines) if lines else ""


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    messages = []
    for msg in data.get("messages", []):
        if isinstance(msg, dict) and msg.get("images"):
            msg = dict(msg)
            msg["images"] = [im.split(",", 1)[1] if isinstance(im, str) and im.startswith("data:") else im for im in msg["images"]]
        messages.append(msg)

    last_user = None
    for idx in range(len(messages) - 1, -1, -1):
        m = messages[idx]
        if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str) and m.get("content").strip():
            last_user = idx
            break
    if last_user is not None:
        content = messages[last_user]["content"]
        if not content.lstrip().startswith("/") and "[Resultados da web]" not in content:
            ctx = _web_results_block(content[:300])
            if ctx:
                m = dict(messages[last_user])
                m["content"] = ctx + "\n\n---\n\n" + content
                messages[last_user] = m

    payload = {
        "model": data.get("model", "oryn:14b"),
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": float(data.get("temperature", 0.7)),
            "num_ctx": int(data.get("context", 8192)),
        },
    }
    return Response(_stream_ollama(payload), mimetype="application/x-ndjson")


def _stream_ollama(payload: dict[str, Any]):
    try:
        with requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=600) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="replace")
                yield line + "\n"
    except requests.ConnectionError:
        yield json.dumps({"error": "Ollama offline. Inicie o Ollama para usar o chat."}) + "\n"
    except requests.Timeout:
        yield json.dumps({"error": "Ollama demorou para responder. Tente novamente."}) + "\n"
    except requests.RequestException as e:
        yield json.dumps({"error": f"Ollama retornou erro: {e}"}) + "\n"
    except Exception as e:
        yield json.dumps({"error": f"Erro ao falar com o Ollama: {e}"}) + "\n"


@app.post("/api/upload")
def upload():
    files = []
    for f in request.files.getlist("files"):
        data = f.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            files.append({"name": f.filename, "error": "Arquivo excede 100MB."})
            continue
        files.append({"name": f.filename, "type": f.content_type, "size": len(data)})
    return jsonify({"files": files})


@app.post("/api/upload/comfyui")
def upload_comfyui():
    if not comfy_available():
        return jsonify({"error": "ComfyUI offline."}), 503
    uploaded = []
    for f in request.files.getlist("files"):
        data = f.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            continue
        fname = re.sub(r'[^\w.\-]', '_', f.filename or "upload.png")
        try:
            r = requests.post(
                f"{COMFYUI_URL}/upload/image",
                files={"image": (fname, data, f.content_type or "image/png")},
                data={"overwrite": "true"},
                timeout=60,
            )
            if r.ok:
                result = r.json()
                uploaded.append({"name": result.get("name", fname), "subfolder": result.get("subfolder", "")})
            else:
                uploaded.append({"name": fname, "error": "Falha no upload para ComfyUI."})
        except requests.RequestException as e:
            uploaded.append({"name": fname, "error": f"Erro: {e}"})
    return jsonify({"files": uploaded})


@app.post("/api/search")
def search():
    query = (request.get_json(silent=True) or {}).get("query", "").strip()
    if not query:
        return jsonify({"error": "Informe uma pesquisa."}), 400
    try:
        results = _search_web(query)
        _store_search_results(query, results)
        if not results:
            results = _cached_results_for(query)
        return jsonify({"query": query, "results": results})
    except requests.Timeout:
        return jsonify({"error": "Pesquisa expirou. Tente novamente."}), 503
    except Exception as e:
        msg = str(e)
        if "ratelimit" in msg.lower() or "rate" in msg.lower():
            return jsonify({"error": "Busca temporariamente limitada. Tente novamente em instantes."}), 503
        return jsonify({"error": f"Pesquisa indisponível: {msg[:200]}"}), 503


@app.post("/api/generate/image")
def generate_image():
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Escreva um prompt antes de gerar a imagem."}), 400
    if not comfy_available():
        return jsonify({"error": "ComfyUI offline. Inicie-o em " + COMFYUI_URL}), 503

    wf = build_flux2_klein_prompt(
        prompt=prompt,
        negative="",
        width=int(data.get("width", 1024)),
        height=int(data.get("height", 1024)),
        seed=data.get("seed", 0),
        steps=int(data.get("steps", 20)),
        batch=int(data.get("batch", 1)),
    )
    return _submit_comfyui_prompt(wf)


def _ensure_input_image(image_ref: dict[str, str]) -> str:
    """Make sure an image referenced by the user is available in ComfyUI's input folder.

    `image_ref` may contain {filename, subfolder, type}. Returns the input-folder
    filename that a LoadImage node can consume.
    """
    filename = image_ref.get("filename", "")
    subfolder = image_ref.get("subfolder", "")
    ftype = image_ref.get("type", "output")
    try:
        data = requests.get(comfy_view_url(filename, subfolder, ftype), timeout=30).content
    except requests.RequestException as e:
        raise ValueError(f"Não foi possível ler a imagem no ComfyUI: {e}") from e
    safe_name = re.sub(r'[^\w.\-]', '_', filename)
    try:
        r = requests.post(
            f"{COMFYUI_URL}/upload/image",
            files={"image": (safe_name, data)},
            data={"overwrite": "true"},
            timeout=60,
        )
        if r.ok:
            body = r.json()
            return body.get("name", safe_name)
    except requests.RequestException as e:
        raise ValueError(f"Não foi possível mover a imagem para o ComfyUI: {e}") from e
    raise ValueError("Falha ao mover a imagem para o ComfyUI.")


@app.post("/api/generate/video")
def generate_video():
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "").strip()
    model = data.get("model", "wan_5b")
    if not prompt:
        return jsonify({"error": "Escreva um prompt antes de gerar o vídeo."}), 400
    if not comfy_available():
        return jsonify({"error": "ComfyUI offline. Inicie-o em " + COMFYUI_URL}), 503

    fps = int(data.get("fps", 24))
    duration = int(data.get("duration", 5))
    length_frames = duration * fps + 1
    width = int(data.get("width", 640))
    height = int(data.get("height", 640))
    seed = int(data.get("seed", 0)) if data.get("seed") else 0
    start_image = data.get("startImage")

    try:
        start_name = None
        if start_image:
            start_name = _ensure_input_image(start_image)
        if model == "wan_14b" and start_name:
            return jsonify({"error": "O Wan 2.2 14B instalado é text-to-video. Para animar uma imagem, use o Wan 2.2 5B."}), 400
        if model == "wan_14b":
            wf = build_wan22_14b_t2v(prompt, width, height, length_frames, fps, seed)
        else:
            wf = build_wan22_5b(prompt, width, height, length_frames, fps, seed, start_image=start_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 503

    return _submit_comfyui_prompt(wf)


@app.post("/api/generate/video/animate")
def animate_image():
    data = request.get_json(silent=True) or {}
    if not isinstance(data.get("image"), dict) or not data["image"].get("filename"):
        return jsonify({"error": "Nenhuma imagem fornecida para animar."}), 400
    prompt = data.get("prompt", "").strip() or "Smooth subtle camera movement, cinematic lighting"
    if not comfy_available():
        return jsonify({"error": "ComfyUI offline."}), 503

    fps = int(data.get("fps", 24))
    duration = int(data.get("duration", 5))
    length_frames = duration * fps + 1
    width = int(data.get("width", 640))
    height = int(data.get("height", 640))

    try:
        start_name = _ensure_input_image(data["image"])
        wf = build_wan22_5b(prompt, width, height, length_frames, fps, 0, start_image=start_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 503

    return _submit_comfyui_prompt(wf)


@app.get("/api/audio/status")
def audio_status():
    try:
        return jsonify(audio_gen.status())
    except Exception as e:
        return jsonify({"error": f"Status de áudio indisponível: {e}"}), 500


def _comfy_media_path(f: dict[str, Any]) -> Path | None:
    ftype = f.get("type") or "output"
    base_dir = {"output": "output", "input": "input", "temp": "temp"}.get(ftype, "output")
    sub = f.get("subfolder") or ""
    filename = f.get("filename") or ""
    if not filename or "/" in filename or "\\" in filename or ".." in filename:
        return None
    for root in detect_comfyui_roots():
        p = root / base_dir / sub / filename
        if p.exists():
            return p
    return None


@app.post("/api/audio/render")
def audio_render():
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Informe o prompt para gerar o som."}), 400
    f = data.get("file")
    if not isinstance(f, dict) or not f.get("filename"):
        return jsonify({"error": "Vídeo de origem não informado."}), 400
    if audio_gen._lock.locked():
        return jsonify({"error": "Já tem um som sendo gerado. Aguarde e tente de novo."}), 409

    video_path = _comfy_media_path(f)
    if video_path is None:
        return jsonify({"error": "Vídeo de origem não encontrado no ComfyUI."}), 404

    duration = float(data.get("durationSeconds") or 5)
    try:
        duration = max(1, float(duration))
    except (TypeError, ValueError):
        duration = 5

    tmp = ROOT / "audio_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    wav = tmp / f"oryn_{os.urandom(4).hex()}.wav"
    out_name = f"{Path(f['filename']).stem}_audio.mp4"
    sub = f.get("subfolder") or "ORYN/video"
    out_path = video_path.parent / out_name

    with audio_gen._lock:
        try:
            engine = audio_gen.render_audio(prompt, duration, wav)
            audio_gen.mux_audio(video_path, wav, out_path)
        except Exception as e:
            return jsonify({"error": f"Falha ao gerar som: {e}"}), 500
        finally:
            try:
                wav.unlink(missing_ok=True)
            except OSError:
                pass

    return jsonify({
        "engine": engine,
        "file": {"filename": out_name, "subfolder": sub, "type": f.get("type") or "output"},
    })


@app.get("/api/agent/status")
def agent_status():
    try:
        return jsonify(agent.agent_status())
    except Exception as e:
        return jsonify({"error": f"Agente indisponível: {e}"}), 500


@app.post("/api/agent/run")
def agent_run():
    data = request.get_json(silent=True) or {}
    task = data.get("task", "").strip()
    if not task:
        return jsonify({"error": "Descreva a tarefa para o agente."}), 400
    if len(task) > 3000:
        return jsonify({"error": "Tarefa longa demais (máx. 3000 caracteres)."}), 400
    model = data.get("model") or "oryn:14b"
    try:
        result = agent.run_agent(task, model, OLLAMA_URL)
    except requests.RequestException:
        return jsonify({"error": "Ollama offline. Inicie o Ollama para usar o agente."}), 503
    except Exception as e:
        return jsonify({"error": f"Falha no agente: {e}"}), 500
    status_code = 200 if result.get("ok") else 200
    return jsonify(result), status_code


def _submit_comfyui_prompt(prompt_graph: dict[str, Any]) -> Any:
    try:
        r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": prompt_graph}, timeout=30)
        if not r.ok:
            err = map_comfy_error(r.text[:1200])
            return jsonify({"error": err}), 503
        job = r.json()
        return jsonify({"queued": True, "promptId": job.get("prompt_id")})
    except requests.ConnectionError:
        return jsonify({"error": "ComfyUI offline. Não foi possível conectar a " + COMFYUI_URL + "."}), 503
    except requests.Timeout:
        return jsonify({"error": "ComfyUI não respondeu a tempo."}), 503
    except requests.RequestException as e:
        return jsonify({"error": f"Erro ao comunicar com ComfyUI: {e}"}), 503


@app.get("/api/generate/status/<prompt_id>")
def generation_status(prompt_id: str):
    if not re.match(r'^[0-9a-f\-]{36}$', prompt_id, re.IGNORECASE):
        return jsonify({"state": "error", "error": "ID de geração inválido."}), 400
    try:
        r = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10)
        r.raise_for_status()
        hist = r.json().get(prompt_id)
        if not hist:
            return jsonify({"state": "queued", "promptId": prompt_id})
        status = hist.get("status", {})
        if status.get("status_str") == "error":
            msgs = status.get("messages", [])
            detail = " ".join(str(m) for m in msgs[-1:]) if msgs else ""
            return jsonify({"state": "error", "error": map_comfy_error(detail or "ComfyUI falhou ao executar o workflow.")}), 500
        if not status.get("completed"):
            return jsonify({"state": "running", "promptId": prompt_id})
        files = []
        for output in hist.get("outputs", {}).values():
            files.extend(output.get("images", []))
            files.extend(output.get("gifs", []))
            files.extend(output.get("videos", []))
        media = [{
            "filename": f.get("filename"),
            "subfolder": f.get("subfolder", ""),
            "type": f.get("type", "output"),
        } for f in files]
        return jsonify({"state": "complete", "promptId": prompt_id, "files": media})
    except requests.ConnectionError:
        return jsonify({"state": "error", "error": "ComfyUI offline."}), 503
    except requests.RequestException as e:
        return jsonify({"state": "error", "error": f"Erro ao consultar ComfyUI: {e}"}), 503


@app.post("/api/files/preview")
def file_preview():
    data = request.get_json(silent=True) or {}
    filename = data.get("filename", "").strip()
    data_url = data.get("dataUrl", "")
    filetype = data.get("type", "")
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()

    if not data_url:
        return jsonify({"preview": "", "kind": "unknown"})

    payload = data_url.split(",", 1)[-1] if "," in data_url else data_url
    raw: bytes = b""
    try:
        import base64
        raw = base64.b64decode(payload)
    except Exception:
        return jsonify({"preview": "", "kind": "unknown"})

    text_types = {
        "txt", "md", "py", "js", "ts", "jsx", "tsx", "json", "html", "css",
        "c", "cpp", "h", "hpp", "cs", "java", "go", "rs", "php", "xml",
        "yaml", "yml", "toml", "ini", "log", "csv", "bat", "sh", "ps1",
    }
    image_exts = {"png", "jpg", "jpeg", "webp", "bmp", "gif", "avif"}

    if ext in image_exts or filetype.startswith("image/"):
        mime = filetype or {
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp", "bmp": "image/bmp", "gif": "image/gif",
            "avif": "image/avif", "tiff": "image/tiff",
        }.get(ext, "image/png")
        b64 = base64.b64encode(raw).decode("ascii")
        return jsonify({"preview": f"data:{mime};base64,{b64}", "kind": "image", "size": len(raw)})

    if ext in text_types or filetype.startswith("text/") or ext in {"",}:
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            text = raw.decode("latin-1", errors="replace")
        if ext == "md":
            try:
                import markdown
                html = markdown.markdown(text, extensions=["fenced_code", "tables"])
                return jsonify({"preview": html, "kind": "markdown", "size": len(raw)})
            except Exception:
                pass
        return jsonify({"preview": text[:20000], "kind": "text", "size": len(raw)})

    return jsonify({"preview": "", "kind": "binary", "size": len(raw)})


def _split_choices(value):
    if isinstance(value, tuple) and len(value) > 0 and isinstance(value[0], list):
        return value[0]
    if isinstance(value, list) and value and isinstance(value[0], list):
        return value[0]
    return []


def _resolve_wan_model_files() -> dict[str, str] | None:
    info = comfyui_object_info()
    unet_list = _split_choices(info.get("UNETLoader", {}).get("input", {}).get("required", {}).get("unet_name", [None, None]))

    ti2v_5b = None
    t2v_14b_hi = None
    t2v_14b_lo = None
    for name in unet_list:
        nl = name.lower()
        if "ti2v" in nl and "5b" in nl:
            if ti2v_5b is None:
                ti2v_5b = name
        elif "high_noise" in nl:
            if t2v_14b_hi is None:
                t2v_14b_hi = name
        elif "low_noise" in nl:
            if t2v_14b_lo is None:
                t2v_14b_lo = name
    if not t2v_14b_hi:
        for name in unet_list:
            nl = name.lower()
            if "14b" in nl and "t2v" in nl and "low_noise" not in nl and "ti2v" not in nl:
                t2v_14b_hi = name
                break
    if not t2v_14b_lo:
        for name in unet_list:
            nl = name.lower()
            if "14b" in nl and "t2v" in nl and "high_noise" not in nl and "ti2v" not in nl:
                t2v_14b_lo = name
                break

    vae_names = _split_choices(info.get("VAELoader", {}).get("input", {}).get("required", {}).get("vae_name", [None, None]))

    vae = None
    for vn in vae_names:
        vlower = vn.lower()
        if "wan2.2_vae" in vlower or "wan_2.1_vae" in vlower:
            vae = vn
            break

    clip_names = _split_choices(info.get("CLIPLoader", {}).get("input", {}).get("required", {}).get("clip_name", [None, None]))

    clip = None
    for cn in clip_names:
        if "umt5" in cn.lower():
            clip = cn
            break

    if not all([ti2v_5b, t2v_14b_hi, t2v_14b_lo, vae, clip]):
        missing = []
        if not ti2v_5b: missing.append("wan2.2 ti2v 5B")
        if not t2v_14b_hi: missing.append("wan2.2 t2v 14B high_noise")
        if not t2v_14b_lo: missing.append("wan2.2 t2v 14B low_noise")
        if not vae: missing.append("wan VAE")
        if not clip: missing.append("umt5 text encoder")
        raise ValueError("Modelos Wan 2.2 ausentes no ComfyUI: " + ", ".join(missing) + ".")

    return {"ti2v_5b": ti2v_5b, "t2v_14b_hi": t2v_14b_hi, "t2v_14b_lo": t2v_14b_lo, "vae": vae, "clip": clip}


def build_wan22_5b(
    prompt: str, width: int, height: int, length: int, fps: int,
    seed: int = 0, start_image: str | None = None,
) -> dict[str, Any]:
    m = _resolve_wan_model_files()
    g: dict[str, Any] = {}
    g["1"] = {"class_type": "CLIPLoader", "inputs": {"clip_name": m["clip"], "type": "wan", "device": "default"}}
    g["2"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": prompt}}
    g["3"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": ""}}
    g["4"] = {"class_type": "UNETLoader", "inputs": {"unet_name": m["ti2v_5b"], "weight_dtype": "default"}}
    g["5"] = {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": 8.0}}
    g["6"] = {"class_type": "VAELoader", "inputs": {"vae_name": m["vae"]}}
    wan_inputs: dict[str, Any] = {"vae": ["6", 0], "width": width, "height": height, "length": length, "batch_size": 1}
    if start_image:
        wan_inputs["start_image"] = ["7", 0]
        g["7"] = {"class_type": "LoadImage", "inputs": {"image": start_image, "upload": "image"}}
    g["8"] = {"class_type": "Wan22ImageToVideoLatent", "inputs": wan_inputs}
    g["9"] = {"class_type": "KSampler", "inputs": {
        "model": ["5", 0], "positive": ["2", 0], "negative": ["3", 0],
        "latent_image": ["8", 0], "seed": seed, "steps": 20, "cfg": 5.0,
        "sampler_name": "uni_pc", "scheduler": "simple", "denoise": 1.0,
    }}
    g["10"] = {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["6", 0]}}
    g["11"] = {"class_type": "CreateVideo", "inputs": {"images": ["10", 0], "fps": float(fps), "bit_depth": "auto", "color_space": "sRGB"}}
    g["12"] = {"class_type": "SaveVideo", "inputs": {
        "video": ["11", 0], "filename_prefix": "ORYN/video",
        "format": "mp4", "codec": {"codec": "h264"},
    }}
    return g


def build_wan22_14b_t2v(
    prompt: str, width: int, height: int, length: int, fps: int, seed: int = 0,
) -> dict[str, Any]:
    m = _resolve_wan_model_files()
    g: dict[str, Any] = {}
    g["1"] = {"class_type": "CLIPLoader", "inputs": {"clip_name": m["clip"], "type": "wan", "device": "default"}}
    g["2"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": prompt}}
    g["3"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": ""}}
    g["10"] = {"class_type": "UNETLoader", "inputs": {"unet_name": m["t2v_14b_hi"], "weight_dtype": "default"}}
    g["11"] = {"class_type": "ModelSamplingSD3", "inputs": {"model": ["10", 0], "shift": 8.0}}
    g["12"] = {"class_type": "UNETLoader", "inputs": {"unet_name": m["t2v_14b_lo"], "weight_dtype": "default"}}
    g["13"] = {"class_type": "ModelSamplingSD3", "inputs": {"model": ["12", 0], "shift": 8.0}}
    g["14"] = {"class_type": "VAELoader", "inputs": {"vae_name": m["vae"]}}
    g["15"] = {"class_type": "Wan22ImageToVideoLatent", "inputs": {"vae": ["14", 0], "width": width, "height": height, "length": length, "batch_size": 1}}

    total_steps = 20
    switch_at = 4
    g["20"] = {"class_type": "KSamplerAdvanced", "inputs": {
        "model": ["11", 0], "positive": ["2", 0], "negative": ["3", 0],
        "latent_image": ["15", 0], "add_noise": "enable", "noise_seed": seed,
        "steps": total_steps, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
        "start_at_step": 0, "end_at_step": switch_at, "return_with_leftover_noise": "enable",
    }}
    g["21"] = {"class_type": "KSamplerAdvanced", "inputs": {
        "model": ["13", 0], "positive": ["2", 0], "negative": ["3", 0],
        "latent_image": ["20", 0], "add_noise": "disable", "noise_seed": seed,
        "steps": total_steps, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
        "start_at_step": switch_at, "end_at_step": total_steps, "return_with_leftover_noise": "disable",
    }}
    g["30"] = {"class_type": "VAEDecode", "inputs": {"samples": ["21", 0], "vae": ["14", 0]}}
    g["31"] = {"class_type": "CreateVideo", "inputs": {"images": ["30", 0], "fps": float(fps), "bit_depth": "auto", "color_space": "sRGB"}}
    g["32"] = {"class_type": "SaveVideo", "inputs": {
        "video": ["31", 0], "filename_prefix": "ORYN/video",
        "format": "mp4", "codec": {"codec": "h264"},
    }}
    return g


def build_flux2_klein_prompt(
    prompt: str, negative: str = "", width: int = 1024, height: int = 1024,
    seed: int = 0, steps: int = 20, batch: int = 1,
) -> dict[str, Any]:
    if not prompt.strip():
        raise ValueError("Escreva um prompt antes de gerar a imagem.")
    info = comfyui_object_info()
    clip_list = info.get("CLIPLoader", {}).get("input", {}).get("required", {}).get("clip_name", [None, None])
    clip_names = clip_list[0] if isinstance(clip_list, tuple) and isinstance(clip_list[0], list) else []
    flux_clip = None
    for cn in clip_names:
        if "flux2" in cn.lower() or "qwen" in cn.lower():
            flux_clip = cn
            break
    if not flux_clip:
        flux_clip = "split_files\\text_encoders\\qwen_3_4b_fp4_flux2.safetensors"

    unet_list = info.get("UNETLoader", {}).get("input", {}).get("required", {}).get("unet_name", [None, None])
    unets = unet_list[0] if isinstance(unet_list, tuple) and isinstance(unet_list[0], list) else []
    flux_unet = None
    for un in unets:
        if "flux" in un.lower() and "klein" in un.lower():
            flux_unet = un
            break
    if not flux_unet:
        flux_unet = "flux-2-klein-4b.safetensors"

    vae_list = info.get("VAELoader", {}).get("input", {}).get("required", {}).get("vae_name", [None, None])
    vaes = vae_list[0] if isinstance(vae_list, tuple) and isinstance(vae_list[0], list) else []
    flux_vae = None
    for vn in vaes:
        if "flux2" in vn.lower():
            flux_vae = vn
            break
    if not flux_vae:
        flux_vae = "split_files\\vae\\flux2-vae.safetensors"

    neg = negative.strip() or "baixa qualidade, não realista"

    g: dict[str, Any] = {}
    g["1"] = {"class_type": "CLIPLoader", "inputs": {"clip_name": flux_clip, "type": "flux2", "device": "default"}}
    g["2"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": prompt}}
    g["3"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": neg}}
    g["4"] = {"class_type": "UNETLoader", "inputs": {"unet_name": flux_unet, "weight_dtype": "default"}}
    g["5"] = {"class_type": "CFGGuider", "inputs": {"model": ["4", 0], "positive": ["2", 0], "negative": ["3", 0], "cfg": 1.0}}
    g["6"] = {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": width, "height": height, "batch_size": batch}}
    g["7"] = {"class_type": "Flux2Scheduler", "inputs": {"steps": steps, "width": width, "height": height}}
    g["8"] = {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}}
    g["9"] = {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}}
    g["10"] = {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["9", 0], "guider": ["5", 0], "sampler": ["8", 0], "sigmas": ["7", 0], "latent_image": ["6", 0]}}
    g["11"] = {"class_type": "VAELoader", "inputs": {"vae_name": flux_vae}}
    g["12"] = {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["11", 0]}}
    g["13"] = {"class_type": "SaveImage", "inputs": {"images": ["12", 0], "filename_prefix": "ORYN/FLUX2"}}
    return g


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "8000")), debug=True, use_reloader=False)
