"""Prueba mínima: arranca una GPU T4 en Modal y dice qué tarjeta es. Coste: unos céntimos del crédito gratuito.
Uso: modal run pipeline/modal/prueba_gpu.py"""
import modal

app = modal.App("neido-prueba-gpu")
imagen = modal.Image.debian_slim().pip_install("torch")


@app.function(gpu="T4", image=imagen, timeout=600)
def info():
    import torch, time
    t = time.time()
    x = torch.randn(4096, 4096, device="cuda")
    for _ in range(50):
        x = x @ x / 64
    torch.cuda.synchronize()
    return f"{torch.cuda.get_device_name(0)} · {torch.cuda.get_device_properties(0).total_memory/1e9:.0f} GB · prueba {time.time()-t:.2f} s"


@app.local_entrypoint()
def main():
    print(info.remote())
