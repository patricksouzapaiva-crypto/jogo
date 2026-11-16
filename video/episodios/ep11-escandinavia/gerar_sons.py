"""Sons do Ep. 11 (Escandinávia, 16/11). Base: biblioteca Sonniss (royalty-free, uso comercial, sem crédito
obrigatório) pelo archive.org — vento nos pinheiros, nevasca, passos na neve, gelo estalando, galho quebrando, clique
de lanterna, impacto grave, coração, rosnado. Os sons que já existem no canal (tambor, porta, rangido, fogo) são
reaproveitados de painel/sons/ep10_*. O canto kulning distante sai do sintetizador da trilha (ep11_kulning_longe).
Cada som: arquivo → corte → nivelado em LUFS → painel/sons/ep11_<nome>.mp3 (o .flac é apagado: disco curto).
Uso: python3 gerar_sons.py [nome ...]"""
import subprocess, sys, urllib.parse
from pathlib import Path

AQUI = Path(__file__).parent
SONS = AQUI.parents[1] / "painel" / "sons"
TMP = AQUI / "sons"; TMP.mkdir(exist_ok=True)

# nome: (ano, arquivo, início s, duração s, LUFS, filtro extra)
LISTA = {
    # ambientes (laços longos) — sem chiado: passa-baixa onde o vento tem agudo demais
    "vento_pinheiros": (0, "Soundopolis - Natures Fury_Wind_01/Wind_Forest_Fienup_001.flac", 5, 120, -26, "lowpass=f=6000,"),
    "nevasca": (0, "Ivo Vicic - Winter textures vol.1/07 Blizzard_Snow melting_wind_MS stereo.flac", 5, 120, -25, "lowpass=f=7000,"),
    "mata_inverno_noite": (0, "Articulated Sounds - Winter Forest Ambience/WINTER Forest night dark moon with distant wolves howls, North Laurentian Wo", 10, 120, -28, ""),
    # efeitos
    "passos_neve": (0, "Pole Position Production - The Snow & Ice Textures Library/snow_foley_walking_on_snow_02.flac", 0, 20, -22, ""),
    "passos_neve_correndo": (0, "Bluezone - Snow Footsteps/Bluezone_BC0264_snow_footsteps_run_004.flac", 0, 8, -20, ""),
    "gelo_estalo": (0, "Mindful Audio - Elements - Ice/thin ice cracks crunchy 06.flac", 0, 6, -22, ""),
    "galho_quebra": (0, "InMotionAudio - Wood/WOODBrk_Snap09_InMotionAudio_Wood.flac", 0, 3, -16, ""),
    "lanterna_clique": (0, "Bart Kamski - Clicks & Switches/Button_Press 007.flac", 0, 1.5, -18, ""),
    "impacto_grave": (0, "Baxter Audio - IMPACT/10 Hit Deep Thud.flac", 0, 5, -15, ""),
    "coracao": (0, "Airborne Sound - Human/Heartbeat,Sound Design,Pulse,Throb,Steady,Accelerate,Panic,Fear.flac", 0, 25, -22, ""),
    "rosnado": (0, "Epic Stock Media - Elemental Mutation Whooshes and Impacts/FIREWhsh_Whoosh Fire Deep Growl Monster Saturated Crisp 03_ES", 0, 4, -18, "lowpass=f=4000,asetrate=44100*0.8,aresample=44100,"),
}


def achar(arq):
    """(id do pacote no archive.org, nome completo) — aceita o começo do nome (os do índice são longos)."""
    import json
    idx = json.load(open(SONS / "sonniss" / "indice.json"))
    f = next(f for f in idx if f["arq"] == arq or f["arq"].startswith(arq))
    return f["id"], f["arq"]


so = set(sys.argv[1:])
for nome, (_, arq, ini, dur, lufs, extra) in LISTA.items():
    if so and nome not in so:
        continue
    saida = SONS / f"ep11_{nome}.mp3"
    if saida.exists():
        continue
    ident, arq = achar(arq)
    flac = TMP / f"{nome}.flac"
    url = f"https://archive.org/download/{ident}/" + urllib.parse.quote(arq)
    subprocess.run(["curl", "-sL", "--fail", "--retry", "3", "-o", str(flac), url], check=True)
    fade = f"afade=t=in:d=0.02,areverse,afade=t=in:d={min(1.5, dur / 6):.2f},areverse,"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(ini), "-t", str(dur), "-i", str(flac), "-af",
                    f"{extra}{fade}loudnorm=I={lufs}:TP=-2:LRA=11", "-ar", "44100", "-b:a", "192k", str(saida)], check=True)
    flac.unlink()
    print("ok", saida.name, flush=True)
# o kulning distante (o chamado que atrai): sintetizado, com muito reverb e passa-baixa (vem de longe, pela mata)
k = SONS / "ep11_kulning_longe.mp3"
if not k.exists() and (not so or "kulning_longe" in so):
    sys.path.insert(0, str(AQUI.parents[1] / "painel" / "ferramentas"))
    import numpy as np, sintetizar_norte_ep11 as N
    m = N.reverb(N.kulning([("A5", 1.3), ("D6", 2.4), ("C6", 0.7), ("A5", 2.6)], vel=0.08), 6.0, 0.6)
    N._salvar(m, str(k), "lowpass=f=3500,highpass=f=300,loudnorm=I=-22:TP=-3")
    print("ok", k.name)
