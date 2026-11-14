"""Ep. 09 — ambientes em CAMADAS (15/11, pedido do usuário: "som é extremamente importante no terror").
Antes cada lugar tinha um som só e baixo; nos respiros sobrava quase nada. Aqui cada ambiente é o lugar + uma camada
de tensão grave por baixo (drone, coração), em laço sem emenda audível (as pontas se fundem em 3 s).
Saída: painel/sons/ep09_<nome>.mp3 (normalizado). Uso: python3 desenho_som.py"""
import subprocess
import numpy as np
from pathlib import Path

SONS = Path(__file__).resolve().parents[2] / "painel" / "sons"
SR, DUR, FUSAO = 48000, 60.0, 3.0


def ler(nome, db=0.0, filtro="anull"):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", str(SONS / f"{nome}.mp3"), "-t", f"{DUR + FUSAO}",
                          "-af", f"{filtro},volume={db}dB", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    n = int((DUR + FUSAO) * SR)
    return np.pad(x, ((0, max(0, n - len(x))), (0, 0)))[:n]


CAMADAS = {
    # a trilha do monte Jangsan à noite: pinheiros, vento, e um grave que não deixa relaxar
    "mata_tensa": [("ep09_sn_mata_noite_corujas", 0), ("ep09_mata_noite", -6), ("drone_tensao", -15, "lowpass=f=400")],   # corujas: Sonniss
    # o hospital abandonado: o oco do prédio, goteira, vento nas janelas, e o drone
    "hospital_tenso": [("ep09_hospital", 0), ("ep07_hospital_noite", -6), ("drone_terror", -14, "lowpass=f=500")],
    # o elevador do ritual: o motor + um coração baixo (o dele) + o grave
    "elevador_tenso": [("ep09_motor_elevador", 0), ("batimento", -12, "lowpass=f=300"), ("drone_terror", -17, "lowpass=f=400")],
    # a cozinha às 3h: geladeira, a casa estalando, quase nada — e o nada pesa
    "cozinha": [("geladeira", -2), ("casa_noite", -9), ("drone_tensao", -20, "lowpass=f=300")],
    # o "outro lado": a lâmpada fluorescente zumbindo + um agudo fino errado
    "fluorescente_tenso": [("ep09_fluorescente", 0), ("drone_tensao", -16, "highpass=f=200,lowpass=f=2500")],
    # a madrugada no mato, na frente do hospital: vento e o grave sumindo
    "amanhecer_tenso": [("ep09_mata_noite", -3), ("ep06_vento_capacete", -10), ("drone_tensao", -19, "lowpass=f=300")],
}

for nome, cam in CAMADAS.items():
    x = sum(ler(c[0], c[1], c[2] if len(c) > 2 else "anull") for c in cam)
    n, f = int(DUR * SR), int(FUSAO * SR)
    out = x[:n].copy()
    w = np.linspace(0, 1, f)[:, None]
    out[:f] = out[:f] * w + x[n:n + f] * (1 - w)          # o fim do laço vira o começo sem emenda
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "loudnorm=I=-24:TP=-3:LRA=11", "-b:a", "192k", str(SONS / f"ep09_{nome}.mp3")],
                   input=np.clip(out, -1, 1).astype(np.float32).tobytes(), check=True)
    print("ok", nome)
