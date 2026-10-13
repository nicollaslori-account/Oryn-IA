# ORYN - Download dos modelos locais (Wan 2.2 / FLUX.2 Klein + modelos leves)
# Uso: python download_models.py <comfy_root> [--check] [--skip-wan14b] [--light-only] [--add-light]
# Baixa somente os arquivos que faltam, direto para a pasta de modelos do ComfyUI.
import pathlib
import sys

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    sys.exit("ERRO: instalacao do huggingface_hub faltando. Rode: pip install -U huggingface_hub")

# Grupos:
#   shared  -> sempre baixado (vae + text encoder usados por Wan 5B/14B e Wan 2.1)
#   base    -> conjunto padrao (FLUX.2 Klein + Wan 2.2 5B)
#   wan14b  -> pesado (pulado em GPU fraca)
#   light   -> modelos leves (SD 1.5 + SDXL Turbo + Wan 2.1 1.3B), via --light-only/--add-light
CONFIG = [
    # (repositorio, [candidatos de arquivo], pasta destino, [nome final], [grupo])
    # --- Compartilhados ---
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     ["split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"],
     "models/text_encoders", None, "shared"),
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     ["split_files/vae/wan2.2_vae.safetensors",
      "split_files/vae/wan_2.1_vae.safetensors",
      "split_files/vae/wan2.2_5B_vae.safetensors",
      "split_files/vae/wan2.2_14B_vae.safetensors"],
     "models/vae", None, "shared"),
    # --- Base (GPU normal) ---
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     ["split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors"],
     "models/diffusion_models", None, "base"),
    # FLUX.2 Klein (o text encoder Qwen3 vem pelo ComfyUI-Manager no primeiro uso)
    ("black-forest-labs/FLUX.2-klein-4B",
     ["flux-2-klein-4b.safetensors"],
     "models/diffusion_models", None, "base"),
    ("black-forest-labs/FLUX.2-dev",
     ["ae.safetensors"],
     "models/vae", "flux2-vae.safetensors", "base"),
    # --- Pesados (Wan 2.2 14B) ---
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     ["split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors"],
     "models/diffusion_models", None, "wan14b"),
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     ["split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors"],
     "models/diffusion_models", None, "wan14b"),
    # --- Leves (GPU fraca) ---
    ("Comfy-Org/stable-diffusion-v1-5-archive",
     ["v1-5-pruned-emaonly-fp16.safetensors", "v1-5-pruned-emaonly.safetensors"],
     "models/checkpoints", None, "light"),
    ("stabilityai/sdxl-turbo",
     ["sd_xl_turbo_1.0_fp16.safetensors"],
     "models/checkpoints", None, "light"),
    ("Comfy-Org/Wan_2.1_ComfyUI_repackaged",
     ["split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors",
      "split_files/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors"],
     "models/diffusion_models", None, "light"),
]


def main():
    if len(sys.argv) < 2:
        sys.exit("Uso: python download_models.py <comfy_root> "
                 "[--check] [--skip-wan14b] [--light-only] [--add-light]")
    check_only = "--check" in sys.argv
    skip_wan14b = "--skip-wan14b" in sys.argv
    light_only = "--light-only" in sys.argv
    add_light = "--add-light" in sys.argv
    root = pathlib.Path(sys.argv[1])

    def selected(entry):
        group = entry[4] if len(entry) > 4 else "base"
        if group == "shared":
            return True
        if light_only:
            return group == "light"
        if group == "light":
            return add_light
        if group == "wan14b":
            return not skip_wan14b
        return True

    ok, missing = 0, 0
    for entry in CONFIG:
        repo, candidates, dest = entry[0], entry[1], entry[2]
        final_name = entry[3] if len(entry) > 3 else None
        group = entry[4] if len(entry) > 4 else "base"
        if not selected(entry):
            print(f"[--] pulado ({group}): {candidates[0]}")
            continue
        dest_dir = root / dest
        want = final_name or pathlib.Path(candidates[0]).name
        if (dest_dir / want).exists():
            print(f"[ok] ja existe: {dest}/{want}")
            ok += 1
            continue
        if check_only:
            missing += 1
            print(f"[ ] falta: {dest}/{want}")
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        done = False
        for f in candidates:
            try:
                print(f"[...] baixando {repo} :: {f}")
                p = pathlib.Path(hf_hub_download(repo, f))
                target = dest_dir / want
                target.parent.mkdir(parents=True, exist_ok=True)
                if p.resolve() != target.resolve():
                    p.replace(target)
                print(f"[ok] salvo em: {target}")
                ok += 1
                done = True
                break
            except Exception as e:
                print(f"[x] {f} indisponivel: {e}")
        if not done:
            print(f"[!!] nao foi possivel baixar '{dest}/{want}'. Baixe manualmente.")
            missing += 1
    print("-" * 50)
    print(f"Concluido: {ok} pronto(s), {missing} pendente(s).")
    if check_only and missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
