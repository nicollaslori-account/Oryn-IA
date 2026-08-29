# ORYN - Download dos modelos locais (Wan 2.2 + FLUX.2 Klein)
# Uso: python download_models.py <comfy_root>
# Baixa somente os arquivos que faltam, direto para a pasta de modelos do ComfyUI.
import pathlib
import sys

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    sys.exit("ERRO: instalacao do huggingface_hub faltando. Rode: pip install -U huggingface_hub")

CONFIG = [
    # (repositorio, [candidatos de arquivo], pasta destino, [nome final], [grupo])
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     ["split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors"],
     "models/diffusion_models"),
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     ["split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors"],
     "models/diffusion_models", None, "wan14b"),
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     ["split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors"],
     "models/diffusion_models", None, "wan14b"),
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     ["split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"],
     "models/text_encoders", None, "wan14b"),
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     ["split_files/vae/wan2.2_vae.safetensors",
      "split_files/vae/wan_2.1_vae.safetensors",
      "split_files/vae/wan2.2_5B_vae.safetensors",
      "split_files/vae/wan2.2_14B_vae.safetensors"],
     "models/vae"),
    # FLUX.2 Klein (o text encoder Qwen3 vem pelo ComfyUI-Manager no primeiro uso)
    ("black-forest-labs/FLUX.2-klein-4B",
     ["flux-2-klein-4b.safetensors"],
     "models/diffusion_models"),
    ("black-forest-labs/FLUX.2-dev",
     ["ae.safetensors"],
     "models/vae", "flux2-vae.safetensors"),
]


def main():
    if len(sys.argv) < 2:
        sys.exit("Uso: python download_models.py <comfy_root> [--check] [--skip-wan14b]")
    check_only = "--check" in sys.argv
    skip_wan14b = "--skip-wan14b" in sys.argv
    root = pathlib.Path(sys.argv[1])
    ok, missing = 0, 0
    for entry in CONFIG:
        if skip_wan14b and len(entry) > 4 and entry[4] == "wan14b":
            print(f"[--] pulado (GPU fraca): {entry[1][0]}")
            continue
        repo, candidates, dest = entry[0], entry[1], entry[2]
        final_name = entry[3] if len(entry) > 3 else None
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