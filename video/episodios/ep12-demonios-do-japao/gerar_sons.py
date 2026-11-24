"""Sons do Ep. 12 (24/11). Os créditos do ElevenLabs acabaram (24/11): base = biblioteca Sonniss (royalty-free, uso
comercial, sem crédito obrigatório) pelo archive.org, como no Ep. 11. Cada som: arquivo → corte → nivelado em LUFS →
painel/sons/ep12_<nome>.mp3 (o .flac é apagado: disco curto). Uso: python3 gerar_sons.py [nome ...]"""
import json, subprocess, sys, urllib.parse
from pathlib import Path

AQUI = Path(__file__).parent
SONS = AQUI.parents[1] / "painel" / "sons"
TMP = AQUI / "busca" / "sons"; TMP.mkdir(parents=True, exist_ok=True)
# nome: (arquivo no índice, início s, duração s, LUFS, filtro extra)
LISTA = {
    "martelo_prego": ("The Sound Pack Tree - Construction & Tools/Nail Hammering 03.flac", 0, 4, -18, "lowpass=f=6000,aecho=0.6:0.5:60:0.25,"),
    "espada": ("David Dumais Audio - Melee Weapons Sound Effects Pack 1/SWSH_Sword Slash Impact V2 Assorted 18", 0, 2.5, -18, ""),
    "trovao": ("Soundopolis - Natures Fury_Thunder/Thunder_Crack_Fienup_016.flac", 0, 8, -17, ""),
    "mar_noite": ("Nikkö Barrera-Amaya - Colombia, Caribbean Coast/WAVES - Beach Medium Waves Near.flac", 2, 90, -26, "lowpass=f=5000,"),
    "pedra_racha": ("Mechanical Wave - Rock Brick and Dirt/Smash Rock On Debris_RBD 04.flac", 0, 4, -17, "asetrate=44100*0.75,aresample=44100,"),
}


def achar(arq):
    idx = json.load(open(SONS / "sonniss" / "indice.json"))
    f = next(f for f in idx if f["arq"] == arq or f["arq"].startswith(arq))
    return f["id"], f["arq"]


so = set(sys.argv[1:])
for nome, (arq, ini, dur, lufs, extra) in LISTA.items():
    saida = SONS / f"ep12_{nome}.mp3"
    if (so and nome not in so) or (not so and saida.exists()):
        continue
    ident, arq = achar(arq)
    flac = TMP / f"{nome}.flac"
    subprocess.run(["curl", "-sL", "--fail", "--retry", "3", "-o", str(flac),
                    f"https://archive.org/download/{ident}/" + urllib.parse.quote(arq)], check=True)
    fade = f"afade=t=in:d=0.02,areverse,afade=t=in:d={min(1.5, dur / 6):.2f},areverse,"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(ini), "-t", str(dur), "-i", str(flac), "-af",
                    f"{extra}{fade}loudnorm=I={lufs}:TP=-2:LRA=11", "-ar", "44100", "-b:a", "192k", str(saida)], check=True)
    flac.unlink()
    print("ok", saida.name, flush=True)
