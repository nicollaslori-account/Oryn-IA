from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).parent
WORKSPACE = ROOT / "workspace"

READ_ROOTS = (WORKSPACE, ROOT)
ALLOWED_APPS = {
    "notepad": "notepad",
    "bloco de notas": "notepad",
    "calc": "calc",
    "calculadora": "calc",
    "paint": "mspaint",
    "mspaint": "mspaint",
    "explorer": "explorer",
    "explorador": "explorer",
}

DANGEROUS_TOKENS = [
    "import os", "from os ", "os.system", "os.remove", "os.unlink", "os.rmdir",
    "shutil.rmtree", "shutil.move", "shutil.rm", "import subprocess",
    "import ctypes", "import winreg", "__import__", "exec(", "eval(",
    "format c:", "rm -rf", "del /f", "format c:", "netsh", "reg add",
    "remove-item", "remove-item", "invoke-", "powercfg",
]

PLAN_PROMPT = """Você é o "construtor" do ORYN, um agente que executa tarefas no computador do usuário (Windows).
O usuário faz um pedido em português e você deve responder EXCLUSIVAMENTE com um JSON (array), sem texto, sem markdown, sem comentários.

Regras:
- Mapeie o pedido em uma ou mais operações válidas.
- Escreva arquivos e pastas SEMPRE dentro do workspace (paths relativos como "site/index.html").
- Para código Python, primeiro crie o arquivo com write_file e depois execute com run_python.
- Não invente caminhos absolutos do Windows; use caminhos relativos ao workspace.

Operações válidas (formato {"op": "...", "args": {...}}):
- {"op": "write_file", "args": {"path": "pasta/arquivo.txt", "content": "texto completo do arquivo"}}
- {"op": "mkdir", "args": {"path": "pasta/subpasta"}}
- {"op": "read_file", "args": {"path": "pasta/arquivo"}}
- {"op": "list_dir", "args": {"path": "."}}
- {"op": "run_python", "args": {"path": "pasta/script.py"}}
- {"op": "open_app", "args": {"app": "notepad|calc|paint|explorer"}}
- {"op": "search", "args": {"query": "texto da busca"}}
- {"op": "info", "args": {}}

Exemplo: pedido "crie uma pasta projetos com um script python que calcula 2+2 e rode" ->
[{"op":"mkdir","args":{"path":"projetos"}},
 {"op":"write_file","args":{"path":"projetos/soma.py","content":"a = 2 + 2\nprint('resultado:', a)"}},
 {"op":"run_python","args":{"path":"projetos/soma.py"}}]

Pedido do usuário:
"""


def _in_workspace(path: Path) -> bool:
    try:
        path.resolve().relative_to(WORKSPACE.resolve())
        return True
    except ValueError:
        return False


def _in_read_roots(path: Path) -> bool:
    try:
        p = path.resolve()
        return any(p.relative_to(r.resolve()) for r in READ_ROOTS)
    except ValueError:
        return False


def _workspace_path(rel: str) -> Path:
    rel = (rel or ".").replace("\\", "/")
    if rel.startswith("/") or re.match(r"^[A-Za-z]:", rel):
        raise ValueError("Caminhos do Windows fora do workspace não são permitidos.")
    p = (WORKSPACE / rel).resolve()
    if not _in_workspace(p):
        raise ValueError("O caminho escapa do workspace.")
    return p


def _scan_script(code: str) -> list[str]:
    low = code.lower()
    return [t for t in DANGEROUS_TOKENS if t in low]


def _op_write_file(args: dict[str, Any]) -> str:
    p = _workspace_path(str(args.get("path", "")))
    if p.is_dir():
        raise ValueError("Caminho é uma pasta; informe um nome de arquivo com extensão.")
    content = str(args.get("content", ""))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Criado {p.relative_to(WORKSPACE)} ({len(content)} caracteres)."


def _op_mkdir(args: dict[str, Any]) -> str:
    p = _workspace_path(str(args.get("path", "")))
    p.mkdir(parents=True, exist_ok=True)
    return f"Pasta pronta: {p.relative_to(WORKSPACE)}"


def _op_read_file(args: dict[str, Any]) -> str:
    p = _workspace_path(str(args.get("path", "")))
    if not p.is_file():
        raise ValueError(f"Arquivo não existe: {p.relative_to(WORKSPACE)}")
    text = p.read_text(encoding="utf-8", errors="replace")
    return text[:4000] + ("\n…" if len(text) > 4000 else "")


def _op_list_dir(args: dict[str, Any]) -> str:
    p = _workspace_path(str(args.get("path", ".")))
    if not p.exists():
        return "(pasta vazia)"
    if p.is_file():
        return f"- {p.name} (arquivo, {p.stat().st_size} bytes)"
    names = sorted(x.name + ("/" if x.is_dir() else "") for x in p.iterdir())
    return "\n".join(names) if names else "(pasta vazia)"


def _op_run_python(args: dict[str, Any]) -> str:
    p = _workspace_path(str(args.get("path", "")))
    if not p.is_file():
        raise ValueError(f"Arquivo não existe: {p.relative_to(WORKSPACE)}")
    if p.suffix.lower() != ".py":
        raise ValueError("run_python aceita apenas arquivos .py no workspace.")
    code = p.read_text(encoding="utf-8", errors="replace")
    bad = _scan_script(code)
    if bad:
        raise ValueError("Script bloqueado por segurança: " + ", ".join(bad[:3]))
    try:
        proc = subprocess.run(
            [sys.executable, str(p)],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except subprocess.TimeoutExpired:
        raise ValueError("Script excedeu 30 segundos e foi interrompido.")
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    status = f"-> SAÍDA | {out[:1500]}" if out else ""
    if proc.returncode != 0:
        raise ValueError(f"Script falhou (código {proc.returncode}).\n{err[:1200]}")
    return f"Script Ok (código 0).{status}"


def _op_open_app(args: dict[str, Any]) -> str:
    app = str(args.get("app", "")).strip().lower()
    target = ALLOWED_APPS.get(app)
    if not target:
        raise ValueError("App não permitido. Use: notepad, calc, paint ou explorer.")
    subprocess.Popen([target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return f"Abrindo {target}"


def _op_search(args: dict[str, Any]) -> str:
    query = str(args.get("query", "")).strip()
    if not query:
        raise ValueError("Busca sem termo.")
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, max_results=5, timeout=8))
    except Exception:
        results = []
    if not results:
        return "Busca sem resultados. (Internet indisponível?)"
    lines = []
    for i, r in enumerate(results[:5], 1):
        title = r.get("title") or r.get("href") or ""
        href = r.get("href") or ""
        lines.append(f"{i}. {title}\n   {href}")
    return "\n".join(lines)


def _op_info(args: dict[str, Any]) -> str:
    try:
        import platform
        import psutil
        info = (
            f"Sistema: {platform.system()} {platform.release()} ({platform.machine()})\n"
            f"CPU: {platform.processor()} · {psutil.cpu_count(logical=True)} núcleos\n"
            f"RAM: {psutil.virtual_memory().total/2**30:.1f} GB\n"
            f"Disco livre: {psutil.disk_usage(str(ROOT)).free/2**30:.1f} GB\n"
            f"Workspace: {WORKSPACE}"
        )
    except Exception as e:
        info = f"Informações indisponíveis: {e}"
    return info


OPS_EXEC: dict[str, tuple[str, Callable[[dict[str, Any]], str], list[str]]] = {
    "write_file": ("escrever arquivo", _op_write_file, ["path", "content"]),
    "mkdir": ("criar pasta", _op_mkdir, ["path"]),
    "read_file": ("ler arquivo", _op_read_file, ["path"]),
    "list_dir": ("listar pasta", _op_list_dir, []),
    "run_python": ("rodar python", _op_run_python, ["path"]),
    "open_app": ("abrir aplicativo", _op_open_app, ["app"]),
    "search": ("buscar na web", _op_search, ["query"]),
    "info": ("informações do sistema", _op_info, []),
}


def _plan_with_llm(task: str, model: str, ollama_url: str) -> list[dict[str, Any]]:
    import requests
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Você converte pedidos em JSON de operações. Responda só o JSON."},
            {"role": "user", "content": PLAN_PROMPT + task},
        ],
        "stream": False,
        "options": {"temperature": 0.0, "num_ctx": 4096},
    }
    r = requests.post(f"{ollama_url}/api/chat", json=payload, timeout=180)
    r.raise_for_status()
    content = r.json().get("message", {}).get("content", "")
    m = re.search(r"\[[\s\S]*\]", content)
    if not m:
        raise ValueError("O modelo não devolveu um JSON de operações. Tente reformular o pedido.")
    ops = json.loads(m.group(0))
    if not isinstance(ops, list):
        raise ValueError("Plano inválido (esperava uma lista de operações).")
    return ops


def run_agent(task: str, model: str, ollama_url: str) -> dict[str, Any]:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        ops = _plan_with_llm(task, model, ollama_url)
    except Exception as e:
        return {
            "ok": False,
            "error": f"Não consegui planejar a tarefa: {e}",
            "steps": [], "elapsed_s": round(time.time() - t0, 1),
        }

    log: list[dict[str, Any]] = []
    created: list[str] = []
    all_ok = True
    for op in ops:
        if not isinstance(op, dict):
            log.append({"op": "?", "ok": False, "detail": "Operação inválida."})
            all_ok = False
            continue
        name = str(op.get("op", ""))
        args = op.get("args", {}) if isinstance(op.get("args", {}), dict) else {}
        spec = OPS_EXEC.get(name)
        if not spec:
            log.append({"op": name, "ok": False, "detail": f"Operação desconhecida: {name}"})
            all_ok = False
            continue
        label, fn, required = spec
        missing = [k for k in required if not str(args.get(k, "")).strip() and k not in args]
        if missing:
            log.append({"op": name, "ok": False, "detail": f"Faltam argumentos: {', '.join(missing)}"})
            all_ok = False
            continue
        try:
            detail = fn(args)
            if name == "write_file":
                rel = str(args.get("path", "")).replace("\\", "/").lstrip("/")
                created.append(rel)
            log.append({"op": name, "ok": True, "detail": detail[:400]})
        except Exception as e:
            log.append({"op": name, "ok": False, "detail": str(e)[:400]})
            all_ok = False

    return {
        "ok": all_ok,
        "error": "" if all_ok else "Algumas etapas falharam (veja o log).",
        "created": created,
        "steps": log,
        "workspace": str(WORKSPACE),
        "elapsed_s": round(time.time() - t0, 1),
    }


def agent_status() -> dict[str, Any]:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    return {
        "workspace": str(WORKSPACE),
        "ops": sorted(OPS_EXEC.keys()),
        "apps": sorted(set(ALLOWED_APPS.values())),
        "ready": True,
    }