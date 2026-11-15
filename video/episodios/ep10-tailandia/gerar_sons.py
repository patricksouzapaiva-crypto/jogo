"""Sons do Ep. 10 (15/11). ElevenLabs sem créditos até 12/12 → a base é a biblioteca Sonniss (royalty-free, uso comercial,
sem crédito obrigatório), com GRAVAÇÕES FEITAS NA TAILÂNDIA (Faunethic) para a mata, a chuva e a noite de Isan;
o que a biblioteca não tem (cães uivando) sai do Stable Audio Open local (gerar_efeito.py).
Cada som: arquivo da biblioteca → corte → nivelado em LUFS → painel/sons/ep10_<nome>.mp3. O .flac é apagado depois
(o disco da sessão é curto). Uso: python3 gerar_sons.py [nome ...]"""
import subprocess, sys, urllib.parse
from pathlib import Path

AQUI = Path(__file__).parent
SONS = AQUI.parents[1] / "painel" / "sons"
TMP = AQUI / "sons"; TMP.mkdir(exist_ok=True)
G = "sonniss-gdc-{}-game-audio-bundle-normalized"
FAU = "Charlie Atanasyan - Thailand sound library by Faunethic/"

# nome: (ano do pacote, arquivo, início s, duração s, LUFS, filtro extra)
LISTA = {
    # ambientes (laços longos)
    "mata_noite": (2016, FAU + "Forest  cicadas insects and birds at night_120113_01.flac", 20, 120, -26, ""),
    "mata_quieta": (2016, FAU + "Jungle quiet insects and birds wide _120407_11.flac", 10, 120, -27, ""),
    "chuva_mata": (2016, FAU + "Rain in forest the day_120118_13.flac", 5, 90, -26, ""),
    "arrozal_noite": (2016, "Charlie Atanasyan - South India sound library by Faunethic/Rice field frogs and insects close, wide at night 376.flac", 10, 120, -27, ""),
    "vila_caes": (2016, "Charlie Atanasyan - Philippines sound library by Faunethic/Village quiet insects birds dogs and light activity away_140301_04.flac", 0, 120, -27, ""),
    "cctv_estatica": (2018, "CFry – Shortwave/Radio Static 9.flac", 0, 30, -34, "highpass=f=1500,lowpass=f=9000,"),
    # efeitos
    "obturador": (2019, "SmartSoundFX - Mavic Travel Filmmaker/CAMERA Minolta 505 Shutter.flac", 0, 3, -18, ""),
    "obturador_lento": (2020, "Soundholder - Old Cameras 192kHz/camera 11 film rewind lever and shutter slow mono 192kHz.flac", 0, 6, -20, ""),
    "projetor": (2017, "SoundBits - Antiques/Projector_Antique_A_Run_01.flac", 0, 8, -26, ""),
    "porta_madeira": (2019, "Rogue Waves - Creaking Door/DOORCreak_Wooden Door, Opening and Closing 09_RogueWaves_CreakingDoor.flac", 0, 8, -20, ""),
    "batida_madeira": (2023, "Articulated Sounds - Ghosts Return/DOOR KNOCK Bathroom A, Wood, Heavy, Fist, Medium 01, From INSIDE.flac", 0, 6, -22, "lowpass=f=2500,"),
    "rangido_viga": (2018, "Matt Script - Squeaks & Creaks/Old wood floor_creak_creaking_slow_back and forth_04.flac", 0, 10, -22, ""),
    "pano": (2019, "TheWorkRoom Audio Post - Cloths & Sponges Foley/Cloth 61.flac", 0, 6, -22, ""),
    "fogo_pano": (2019, "The Sound Keeper - Small Fire/sm-fire-cotton-02-8040.flac", 0, 20, -24, ""),
    "queda_wifi": (2017, "Glitchedtones - Paranormal/Abstract FX 01.flac", 0, 5, -20, ""),
    "respiracao": (2020, "JC Audio - Breathing In Hell/scared breath 12.flac", 0, 8, -22, ""),
    "tambor": (2016, "Baxter Audio - IMPACT/03 Hit Big Drum.flac", 0, 6, -16, ""),
    "gongo": (2023, "Orbital Emitter - Cinematic Transitions for Editors Volume 2/80,TheGong.flac", 0, 10, -20, ""),
}


def achar_ano(arq):
    import json
    idx = json.load(open(AQUI.parents[1] / "painel" / "sons" / "sonniss" / "indice.json"))
    return next(f["id"] for f in idx if f["arq"] == arq)


so = set(sys.argv[1:])
for nome, (_, arq, ini, dur, lufs, extra) in LISTA.items():
    if so and nome not in so:
        continue
    saida = SONS / f"ep10_{nome}.mp3"
    if saida.exists():
        continue
    flac = TMP / f"{nome}.flac"
    url = f"https://archive.org/download/{achar_ano(arq)}/" + urllib.parse.quote(arq)
    subprocess.run(["curl", "-sL", "--fail", "--retry", "3", "-o", str(flac), url], check=True)
    fade = f"afade=t=in:d=0.02,areverse,afade=t=in:d={min(1.5, dur / 6):.2f},areverse,"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(ini), "-t", str(dur), "-i", str(flac), "-af",
                    f"{extra}{fade}loudnorm=I={lufs}:TP=-2:LRA=11", "-ar", "44100", "-b:a", "192k", str(saida)], check=True)
    flac.unlink()
    print("ok", saida.name, flush=True)
