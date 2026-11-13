"""Sons do Ep. 09 no ElevenLabs (2 versões de cada) → busca/sons/<cod>_<v>.mp3; a escolhida vai para
painel/sons/ep09_<nome>.mp3 (instalar_sons). Chave injetada pelo proxy. Regra: nada de susto."""
import subprocess, sys, time, requests
from pathlib import Path
AQUI = Path(__file__).parent; SAI = AQUI / "busca" / "sons"; SONS = AQUI.parents[1] / "painel" / "sons"
P = {
 "L_ventilador": (20.0, "An old cheap electric desk fan spinning in a tiny silent room at night, steady soft whirr of the blades and a faint motor hum, close, no music, no voices", True),
 "L_corredor": (20.0, "A narrow apartment building corridor at night, buzzing flickering fluorescent tube, distant muffled city hum through the walls, empty, no voices, no music", True),
 "L_quarto": (20.0, "A tiny room at night in a big city, very quiet room tone, faint distant traffic through a thin wall, a little electrical hum, no voices, no music", True),
 "L_seul_chuva": (20.0, "A busy Seoul street at night in the rain, rain on pavement and umbrellas, distant indistinct crowd, cars passing on wet road, no music", True),
 "L_sala_bh": (20.0, "A quiet Brazilian living room on a sunny afternoon, a wall clock ticking softly, distant street and birds through an open window, no voices, no music", True),
 "L_lago": (20.0, "A still black lake at night in the countryside, faint water lapping, distant frogs and insects, light wind in dry grass, eerie, no voices, no music", True),
 "E_batidas": (5.0, "Four slow knocks on a thin wall heard from the other side of the wall, muffled and dull, evenly spaced, in a silent room, no music", False),
 "E_choro_parede": (10.0, "A young woman crying very softly heard muffled through a thin wall from the next room at night, distant, quiet, no music", False),
 "E_elevador": (4.0, "An old small apartment elevator arriving, a soft electronic ding and the doors sliding open, no voices, no music", False),
 "E_chave": (4.0, "A key turning slowly in an old door lock and a thin door creaking open slowly, close, quiet corridor, no music", False),
 "E_papel": (3.0, "Old wallpaper slowly peeling off a wall, dry paper tearing softly, close, no music", False),
 "E_ventilador_liga": (4.0, "Click of an old electric fan switch being turned on and the blades slowly spinning up, close, quiet room, no music", False),
 "T_buk": (5.0, "One single soft deep distant Korean buk barrel drum hit with a long low reverberating tail in a large wooden hall, no music", False),
 "T_jing": (6.0, "One soft distant Korean jing gong struck gently, long shimmering low decay, no music", False),
}
so = set(sys.argv[1:])
for cod, (dur, txt, laco) in P.items():
    if so and cod not in so: continue
    for v in "ab":
        arq = SAI / f"{cod}_{v}.mp3"
        if arq.exists(): continue
        for k in range(4):
            r = requests.post("https://api.elevenlabs.io/v1/sound-generation", headers={"xi-api-key": "proxy"},
                json={"text": txt, "duration_seconds": dur, "prompt_influence": 0.6, "loop": laco}, timeout=180)
            if r.status_code == 200: arq.write_bytes(r.content); print(cod, v, "ok", flush=True); break
            print(cod, v, r.status_code, r.text[:150], flush=True); time.sleep(8)


# escolhidas (13/11, pela análise de volume e de ataques): nome final → (código_versão, filtro extra, LUFS)
ESCOLHA = {
 "ventilador": ("L_ventilador_a", "", -24), "corredor": ("L_corredor_a", "", -26), "seul_chuva": ("L_seul_chuva_a", "", -24),
 "sala_bh": ("L_sala_bh_a", "", -26), "lago": ("L_lago_a", "", -26),
 "batidas": ("E_batidas_b", "atrim=0.45:4.1,asetpts=PTS-STARTPTS,afade=t=out:st=3.2:d=0.45,", -18),   # só as 4 batidas
 "choro_parede": ("E_choro_parede_a", "", -24), "elevador": ("E_elevador_a", "", -20), "chave": ("E_chave_a", "", -20),
 "papel": ("E_papel_a", "", -22), "ventilador_liga": ("E_ventilador_liga_a", "", -22),
 "buk": ("T_buk_b", "", -17), "jing": ("T_jing_b", "", -18),
}
if "--instalar" in sys.argv or not so:
    for nome, (cod, filtro, lufs) in ESCOLHA.items():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(SAI / f"{cod}.mp3"), "-af",
                        f"{filtro}loudnorm=I={lufs}:TP=-3:LRA=11", "-ar", "44100", "-b:a", "192k",
                        str(SONS / f"ep09_{nome}.mp3")], check=True)
    print("instalados:", ", ".join(ESCOLHA))
