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
 # v3 (14/11)
 "L_mata_noite": (20.0, "A Korean mountain pine forest at dusk turning to night, cold wind in the pine needles, a few distant insects, a branch creaking, very quiet, no birds, no voices, no music", True),
 "L_motor_elevador": (20.0, "Inside an old elevator moving slowly upward, low steady motor hum and cable whine, faint rattling of the metal cabin, no music, no voices", True),
 "L_hospital": (20.0, "Inside an empty abandoned concrete building at night, cold hollow room tone, distant dripping water, wind through broken windows, faint creaks, no voices, no music", True),
 "L_fluorescente": (20.0, "A clean empty hospital corridor, steady buzzing of fluorescent tube lights, perfectly still, faint ventilation hum, no voices, no music", True),
 "L_cozinha": (20.0, "A small apartment kitchen at 3 a.m., refrigerator hum, a faint buzzing light over the sink, total stillness, no voices, no music", True),
 "E_sino_andar": (3.0, "A single soft old elevator floor chime, one clear ding, close, no music", False),
 "E_porta_elevador": (5.0, "Old heavy elevator doors sliding open slowly with a metallic scrape and stopping, no music", False),
 "E_passos_descalcos": (6.0, "Slow bare footsteps on a smooth hard floor, soft wet slapping steps coming closer, close and quiet, no music", False),
 "E_oleo_mao": (6.0, "Close soft wet sound of oily hands slowly rubbing along skin, slippery and slow, quiet room, no music", False),
 "E_vidro_balcao": (3.0, "A glass bottle being put down gently on a kitchen counter, quiet room, no music", False),
 "E_porta_abre": (5.0, "A hospital room door handle turning and a door opening slowly with a long low creak, no music", False),
 "E_interruptor": (3.0, "A light switch clicking off in a silent room, close, no music", False),
 "E_lanterna": (3.0, "A small flashlight being clicked on, close, quiet forest at night, no music", False),
 "T_subgrave": (5.0, "A deep soft sub-bass swell rising slowly and fading, cinematic low rumble, no hit, no music", False),
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
 # v3 (14/11) — os créditos do ElevenLabs acabaram no meio: o resto vem da biblioteca dos episódios anteriores
 "mata_noite": ("L_mata_noite_a", "", -26), "motor_elevador": ("L_motor_elevador_a", "", -24),
 "hospital": ("L_hospital_a", "", -26), "fluorescente": ("L_fluorescente_a", "", -26),
}
if "--instalar" in sys.argv or not so:
    for nome, (cod, filtro, lufs) in ESCOLHA.items():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(SAI / f"{cod}.mp3"), "-af",
                        f"{filtro}loudnorm=I={lufs}:TP=-3:LRA=11", "-ar", "44100", "-b:a", "192k",
                        str(SONS / f"ep09_{nome}.mp3")], check=True)
    print("instalados:", ", ".join(ESCOLHA))
