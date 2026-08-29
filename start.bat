@echo off
setlocal EnableExtensions
title ORYN - Inicializador

set "ORYN_ROOT=%~dp0"
if "%ORYN_ROOT:~-1%"=="\" set "ORYN_ROOT=%ORYN_ROOT:~0,-1%"
set "COMFY_ROOT=C:\ComfyUI\ComfyUI"
set "COMFY_PY=%COMFY_ROOT%\.venv\Scripts\python.exe"
set "ORYN_PY=%ORYN_ROOT%\.venv\Scripts\python.exe"

rem ---------- Ollama ----------
set "OLLAMA_FOUND="
set "OLLAMA_EXE=ollama"
where ollama >nul 2>nul
if not errorlevel 1 set "OLLAMA_FOUND=1"
if not defined OLLAMA_FOUND (
  if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (set "OLLAMA_FOUND=1"&set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe")
)
curl -s -o nul --max-time 2 http://127.0.0.1:11434/api/version
if errorlevel 1 (
  if defined OLLAMA_FOUND (
    echo Iniciando o servidor Ollama...
    start "Ollama - server" "%OLLAMA_EXE%" serve
    timeout /t 3 /nobreak >nul
  )
)

if not exist "%COMFY_PY%" set "COMFY_PY="
if not exist "%COMFY_ROOT%\main.py" (
  echo AVISO: ComfyUI nao encontrado em %COMFY_ROOT%.
  echo O ORYN abrira sem geracao de imagem/video.
  echo Rode install.bat se quiser instalar.
  set "COMFY_PY="
)
if not exist "%ORYN_PY%" set "ORYN_PY=py"
if not exist "%ORYN_ROOT%\app.py" (
  echo ERRO: ORYN nao encontrado em %ORYN_ROOT%.
  pause
  exit /b 1
)

if defined COMFY_PY (
  start "ComfyUI - ORYN" /D "%COMFY_ROOT%" cmd /k "set COMFYUI_ROOT=%COMFY_ROOT%&& %COMFY_PY% main.py --listen 127.0.0.1 --port 8188"
)
start "ORYN - Web" /D "%ORYN_ROOT%" cmd /k "set COMFYUI_ROOT=%COMFY_ROOT%&& set OLLAMA_HOST=http://127.0.0.1:11434&& %ORYN_PY% app.py"

timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8000
exit /b 0