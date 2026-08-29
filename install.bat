@echo off
setlocal EnableExtensions
title ORYN - Instalador local

rem ============================================================
rem  ORYN installer - ComfyUI + ORYN, tudo em uma maquina local
rem  - Baixa/clona o ComfyUI e cria os ambientes Python
rem  - Instala as dependencias do ORYN
rem  - Instala/verifica o Ollama e os modelos de chat (oryn, llava, embed)
rem  - Reaproveita os modelos compartilhados do Comfy-Desktop (se houver)
rem  - Baixa (default) os modelos Wan 2.2 / FLUX.2 Klein quando faltarem
rem  - Copia/restaura o SEU workflow e instala os templates FLUX.2 / Wan do ORYN
rem ============================================================

set "ORYN_ROOT=%~dp0"
if "%ORYN_ROOT:~-1%"=="\" set "ORYN_ROOT=%ORYN_ROOT:~0,-1%"
set "COMFY_PARENT=C:\ComfyUI"
set "COMFY_ROOT=%COMFY_PARENT%\ComfyUI"
set "COMFY_VENV=%COMFY_ROOT%\.venv\Scripts\python.exe"
set "ORYN_VENV=%ORYN_ROOT%\.venv\Scripts\python.exe"
set "DESKTOP_SHARED=%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Shared"
set "WF_BACKUP=%ORYN_ROOT%\comfy_workflows"

echo.
echo  === Instalador do ORYN ===
echo  Pasta do ORYN : %ORYN_ROOT%
echo  ComfyUI       : %COMFY_ROOT%
echo.

if not exist "%ORYN_ROOT%\app.py" (
  echo ERRO: app.py nao encontrado em %ORYN_ROOT%.
  pause
  exit /b 1
)

rem ---------- Python ----------
set "PYFOUND="
where py >nul 2>nul
if not errorlevel 1 set "PYFOUND=1"
if not defined PYFOUND (
  where python >nul 2>nul
  if not errorlevel 1 set "PYFOUND=1"
)
if not defined PYFOUND (
  echo ERRO: Python nao encontrado. Instale o Python 3.12+ em https://www.python.org
  echo Marque "Add python.exe to PATH" e rode este instalador novamente.
  pause
  exit /b 1
)
where git >nul 2>nul
if errorlevel 1 (
  echo ERRO: Git nao encontrado. Instale em https://git-scm.com
  pause
  exit /b 1
)

rem ---------- Ollama ----------
set "OLLAMA_OK="
set "OLLAMA_EXE=ollama"
where ollama >nul 2>nul
if not errorlevel 1 set "OLLAMA_OK=1"
if not defined OLLAMA_OK (
  rem Path padrao da instalacao do Ollama (via winget, sem PATH atualizado)
  if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (set "OLLAMA_OK=1"&set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe")
)
if not defined OLLAMA_OK (
  where winget >nul 2>nul
  if not errorlevel 1 (
    echo Instalando o Ollama via winget...
    winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (set "OLLAMA_OK=1"&set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe")
  ) else (
    echo.
    echo ATENCAO: Ollama nao encontrado e winget indisponivel.
    echo Baixe e instale manualmente em https://ollama.com/download
  )
)
if not defined OLLAMA_OK (
  echo AVISO: Ollama nao disponivel nesta sessao. O chat/visao ficarao indisponiveis.
  echo Se instalou agora, rode o install.bat novamente (PATH sera atualizado).
)

rem ---------- Pre-checagem: disco ----------
set "DRV=%COMFY_ROOT:~0,1%"
set "FREE_GB="
for /f "usebackq delims=" %%s in (`powershell -NoProfile -Command "[int]((Get-PSDrive -Name '%DRV%').Free/1GB)"`) do set "FREE_GB=%%s"
if not defined FREE_GB (
  echo AVISO: nao foi possivel ler o espaco livre da unidade %DRV%.
) else (
  echo Espaço livre na unidade %DRV%: %FREE_GB% GB
  if %FREE_GB% LSS 20 (
    echo.
    echo ERRO: pouco espaco em disco (%FREE_GB% GB). O ORYN precisa de pelo menos 20 GB.
    echo Libere espaco e rode o instalador novamente.
    pause
    exit /b 1
  )
)

rem ---------- Pre-checagem: GPU ----------
set "GPU_NAME="
set "VRAM_MB="
set "GPU_WEAK="
set "GPU_MEDIA="
set "GPU_SMI="
set "SMI_PATH=C:\Windows\System32\nvidia-smi.exe"
if exist "%SMI_PATH%" set "GPU_SMI=%SMI_PATH%"
where nvidia-smi >nul 2>nul
if not errorlevel 1 set "GPU_SMI=nvidia-smi"
if defined GPU_SMI (
  "%GPU_SMI%" --query-gpu=name --format=csv,noheader,nounits > "%TEMP%\oryn_gpu_name.txt" 2>nul
  "%GPU_SMI%" --query-gpu=memory.total --format=csv,noheader,nounits > "%TEMP%\oryn_gpu_vram.txt" 2>nul
  for /f "usebackq delims=" %%g in ("%TEMP%\oryn_gpu_name.txt") do set "GPU_NAME=%%g"
  for /f "usebackq delims=" %%v in ("%TEMP%\oryn_gpu_vram.txt") do set "VRAM_MB=%%v"
  del "%TEMP%\oryn_gpu_name.txt" "%TEMP%\oryn_gpu_vram.txt" >nul 2>nul
)
set "VRAM_GB="
if defined VRAM_MB if not "%VRAM_MB%"=="ERROR" set /a VRAM_GB=%VRAM_MB%/1024
if defined GPU_NAME (
  echo GPU NVIDIA: %GPU_NAME%  (%VRAM_GB% GB VRAM)
) else (
  echo GPU NVIDIA: nao detectada (sem driver nvidia-smi).
  echo ATENCAO: geracao de imagem/video exige GPU NVIDIA razoavel. O chat/visao funcionam normal.
  set "GPU_WEAK=1"
)
if defined GPU_NAME (
  if defined VRAM_GB (
    if %VRAM_GB% LSS 8 (
      echo ATENCAO: pouca VRAM (%VRAM_GB% GB). Video pesado pode falhar.
      set "GPU_WEAK=1"
    )
    if %VRAM_GB% GEQ 8 if %VRAM_GB% LSS 16 (
      echo OK: VRAM suficiente para FLUX.2 Klein e Wan 5B. Wan 14B fica pesado.
      set "GPU_MEDIA=1"
    )
  ) else (
    echo AVISO: nao foi possivel ler a VRAM.
    set "GPU_WEAK=1"
  )
)
if not defined GPU_MEDIA if not defined GPU_WEAK (
  echo OK: VRAM >= 16 GB - todos os modelos liberados.
)

rem ---------- ComfyUI ----------
set "COMFY_FRESH="
if not exist "%COMFY_ROOT%\main.py" (
  echo Instalando o ComfyUI em %COMFY_PARENT%...
  if not exist "%COMFY_PARENT%" mkdir "%COMFY_PARENT%"
  git clone https://github.com/comfyanonymous/ComfyUI.git "%COMFY_ROOT%"
  if errorlevel 1 (
    echo ERRO: nao foi possivel clonar o ComfyUI. Verifique Git e internet.
    pause
    exit /b 1
  )
)
if not exist "%COMFY_VENV%" (
  set "COMFY_FRESH=1"
  echo Criando ambiente Python do ComfyUI...
  py -3.13 -m venv "%COMFY_ROOT%\.venv"
  if errorlevel 1 py -m venv "%COMFY_ROOT%\.venv"
)
if not exist "%COMFY_VENV%" (
  echo ERRO: ambiente Python do ComfyUI nao foi criado.
  pause
  exit /b 1
)
if defined COMFY_FRESH (
  echo Instalando dependencias do ComfyUI (pode demorar)...
  "%COMFY_VENV%" -m pip install --upgrade pip
  "%COMFY_VENV%" -m pip install -r "%COMFY_ROOT%\requirements.txt"
  if errorlevel 1 (
    echo ERRO nas dependencias do ComfyUI.
    pause
    exit /b 1
  )
)

rem ---------- extra_model_paths.yaml ----------
rem Reaproveita os modelos do Comfy-Desktop (Wan 2.2, FLUX) quando existirem
set "SHARED_EMPTY=1"
if exist "%DESKTOP_SHARED%\models\diffusion_models" set "SHARED_EMPTY="
if not exist "%COMFY_ROOT%\extra_model_paths.yaml" (
  if not defined SHARED_EMPTY (
    echo Criando extra_model_paths.yaml apontando para %DESKTOP_SHARED%...
    > "%COMFY_ROOT%\extra_model_paths.yaml" (
      echo comfyui_desktop_shared:
      echo     base_path: %DESKTOP_SHARED:\=\\%
      echo     diffusion_models: models/diffusion_models
      echo     text_encoders: models/text_encoders
      echo     vae: models/vae
      echo     loras: models/loras
      echo     upscale_models: models/upscale_models
    )
  ) else (
    echo AVISO: modelos nao encontrados no Comfy-Desktop. Eles serao baixados abaixo/ou usados os do ComfyUI.
  )
)

rem ---------- ORYN ----------
if not exist "%ORYN_VENV%" (
  echo Criando ambiente Python do ORYN...
  py -3.12 -m venv "%ORYN_ROOT%\.venv"
  if errorlevel 1 py -m venv "%ORYN_ROOT%\.venv"
)
if not exist "%ORYN_VENV%" (
  echo ERRO: ambiente Python do ORYN nao foi criado.
  pause
  exit /b 1
)
echo Instalando dependencias do ORYN...
"%ORYN_VENV%" -m pip install --upgrade pip
"%ORYN_VENV%" -m pip install -r "%ORYN_ROOT%\requirements.txt"
if errorlevel 1 (
  echo ERRO nas dependencias do ORYN.
  pause
  exit /b 1
)

rem ---------- config.json ----------
if not exist "%ORYN_ROOT%\config.json" (
  echo Criando config.json padrao...
  > "%ORYN_ROOT%\config.json" (
    echo {
    echo   "ollamaUrl": "http://localhost:11434",
    echo   "comfyuiUrl": "http://127.0.0.1:8188"
    echo }
  )
)

rem ---------- Modelos de chat (Ollama) ----------
if defined OLLAMA_OK (
  echo.
  echo Verificando modelos do Ollama...
  rem Garante o servidor Ollama rodando nesta sessao
  curl -s -o nul --max-time 2 http://127.0.0.1:11434/api/version
  if errorlevel 1 (
    echo Iniciando o servidor Ollama...
    start "Ollama - server" "%OLLAMA_EXE%" serve
    timeout /t 3 /nobreak >nul
  )
  "%OLLAMA_EXE%" list 2>nul | findstr /c:"oryn:14b" >nul
  if errorlevel 1 (
    echo Criando o modelo oryn:14b (puxa o qwen3:14b na 1a vez, ~9GB)...
    "%OLLAMA_EXE%" pull qwen3:14b
    if exist "%ORYN_ROOT%\Modelfile-14b" "%OLLAMA_EXE%" create oryn:14b -f "%ORYN_ROOT%\Modelfile-14b"
  )
  "%OLLAMA_EXE%" list 2>nul | findstr /c:"llava:latest" >nul
  if errorlevel 1 (
    echo Puxando o modelo de visao llava:latest...
    "%OLLAMA_EXE%" pull llava:latest
  )
  "%OLLAMA_EXE%" list 2>nul | findstr /c:"nomic-embed-text:latest" >nul
  if errorlevel 1 (
    echo Puxando o modelo de embeddings nomic-embed-text...
    "%OLLAMA_EXE%" pull nomic-embed-text:latest
  )
  "%OLLAMA_EXE%" list 2>nul | findstr /c:"oryn:32b" >nul
  if errorlevel 1 (
    set /p DL_32B="Criar tambem o oryn:32b (puxa o qwen3:32b, ~20GB)? (s/n): "
    if /i "%DL_32B%"=="s" (
      "%OLLAMA_EXE%" pull qwen3:32b
      if exist "%ORYN_ROOT%\Modelfile-32b" "%OLLAMA_EXE%" create oryn:32b -f "%ORYN_ROOT%\Modelfile-32b"
    )
  )
)

rem ---------- Seus workflows ----------
if not exist "%WF_BACKUP%" mkdir "%WF_BACKUP%"
if exist "%COMFY_ROOT%\user\default\workflows" (
  for %%f in ("%COMFY_ROOT%\user\default\workflows\*.json") do (
    if exist "%%f" (
      copy /y "%%f" "%WF_BACKUP%\" >nul
      echo Backup do workflow: %%~nxf
    )
  )
)
rem Restaura em instalacao nova do ComfyUI
if not exist "%COMFY_ROOT%\user\default\workflows" (
  if exist "%WF_BACKUP%\*.json" (
    echo Restaurando SEU workflow no ComfyUI...
    mkdir "%COMFY_ROOT%\user\default\workflows"
    copy /y "%WF_BACKUP%\*.json" "%COMFY_ROOT%\user\default\workflows\" >nul
  )
)

rem ---------- Workflows padrao (FLUX.2 / Wan) ----------
rem Instala os templates que ja vem com o ORYN se ainda nao existirem
if not exist "%WF_BACKUP%\defaults" (
  echo AVISO: pasta de workflows padrao nao encontrada (%WF_BACKUP%\defaults).
)
if not exist "%COMFY_ROOT%\user\default\workflows" mkdir "%COMFY_ROOT%\user\default\workflows"
for %%f in ("%WF_BACKUP%\defaults\*.json") do (
  if not exist "%COMFY_ROOT%\user\default\workflows\%%~nxf" (
    copy /y "%%f" "%COMFY_ROOT%\user\default\workflows\" >nul
    echo Workflow padrao instalado: %%~nxf
  )
)

rem ---------- Modelos de geracao (ComfyUI) ----------
rem Verifica se falta algum modelo de geracao antes de perguntar.
rem Modelos do Comfy-Desktop sao reutilizados pelo extra_model_paths.yaml.
set "SKIP_FLAG="
if defined GPU_WEAK set "SKIP_FLAG=--skip-wan14b"
if defined GPU_WEAK (
  echo.
  echo  GPU fraca ou sem NVIDIA: o instalador vai PULAR o Wan 14B (pesado).
  echo  Vem apenas FLUX.2 Klein (imagem) + Wan 2.2 5B (video basico) + chat/visao.
)
set "NEED_MODELS="
set "HAVE_GEN="
if exist "%COMFY_ROOT%\extra_model_paths.yaml" (
  if exist "%DESKTOP_SHARED%\models\diffusion_models" set "HAVE_GEN=1"
)
if not defined HAVE_GEN (
  "%COMFY_VENV%" "%ORYN_ROOT%\download_models.py" "%COMFY_ROOT%" --check %SKIP_FLAG% >nul 2>nul
  if errorlevel 1 set "NEED_MODELS=1"
)
if defined NEED_MODELS (
  set "MIN_FREE=60"
  if defined GPU_WEAK set "MIN_FREE=25"
  if defined FREE_GB if %FREE_GB% LSS %MIN_FREE% (
    echo.
    echo ERRO: espaco livre (%FREE_GB% GB) menor que o necessario (%MIN_FREE% GB) para os modelos.
    echo Libere espaco e rode o instalador novamente.
    pause
    exit /b 1
  )
  echo.
  if defined GPU_WEAK (
    echo  Baixando: FLUX.2 Klein + Wan 2.2 5B (~25 GB)...
  ) else (
    echo  Faltam modelos de geracao (Wan 2.2 / FLUX.2 Klein), alguns GB.
  )
  choice /c SN /n /t 30 /d S /m "Baixar agora (S=sim, N=nao, default S em 30s)? "
  if not errorlevel 2 (
    "%COMFY_VENV%" -m pip install -U huggingface_hub >nul 2>nul
    echo Baixando modelos (alguns GB, pode demorar)...
    "%COMFY_VENV%" "%ORYN_ROOT%\download_models.py" "%COMFY_ROOT%" %SKIP_FLAG%
  ) else (
    echo OK, sem download agora. Rode install.bat novamente para baixar depois.
  )
) else (
  echo Modelos de geracao ja presentes (via Comfy-Desktop ou ComfyUI), sem download.
)

echo.
echo  ==========================================
echo   Instalacao concluida.
echo   GPU           : %GPU_NAME%  (%VRAM_GB% GB VRAM)
echo   Espaco livre  : %FREE_GB% GB (unidade %DRV%)
echo   - Ollama com modelos de chat/visao: verificados
echo   - Workflows FLUX.2 / Wan prontos no ComfyUI
echo   Proximo passo:
echo   1) Rode start.bat para iniciar ComfyUI + Ollama + ORYN
echo   2) Abra http://127.0.0.1:8000
echo  ==========================================
pause
exit /b 0