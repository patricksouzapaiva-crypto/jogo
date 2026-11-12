"""Sons do Ep. 08 no ElevenLabs (2 versões de cada) → busca/sons/<cod>_<v>.mp3. Chave injetada pelo proxy."""
import json, sys, time, requests
from pathlib import Path
SAI = Path(__file__).parent / "busca" / "sons"
P = {
 # transições
 "T_pincel": (2.5, "Calligraphy brush making one fast confident stroke on rice paper, close, dry bristles, crisp, no music", False),
 "T_shoji": (2.0, "Japanese wooden shoji sliding door slid open quickly on its wooden track, soft paper rattle, close, no music", False),
 "T_vela": (3.0, "A candle flame blown out with one soft breath, tiny hiss, faint smoke, very close and quiet room, no music", False),
 "T_taiko": (4.0, "One single deep distant Japanese taiko drum hit with a long low reverberating tail in a large wooden hall, no music", False),
 "T_tinta": (2.5, "Dark ink drop falling into water and spreading, deep soft whoosh with a liquid bloom, cinematic transition, no music", False),
 "T_carimbo": (1.5, "A heavy wooden hanko seal stamp pressed firmly on paper, one dull thud, close, no music", False),
 # lugar
 "L_trem_dentro": (20.0, "Inside an empty Japanese commuter train at night, steady rhythmic clatter of wheels on rails, hum of fluorescent lights and electric motor, no voices, no music", True),
 "L_freio": (5.0, "Electric commuter train braking to a stop at a small station, long metallic squeal then hiss of air brakes, no voices, no music", False),
 "L_sino_estacao": (4.0, "Small Japanese railway station departure bell melody ringing alone on an empty platform at night, slight echo, no voices", False),
 "L_tambor_longe": (15.0, "Very distant slow Japanese taiko drum beats echoing from the hills at night, with a small bell ringing faintly, wind in rice fields, eerie, no voices, no music", True),
 "L_campo_noite": (20.0, "Rural Japan at night, empty rice fields, soft wind, distant frogs and insects, total isolation, no voices, no music", True),
 "L_quintal": (20.0, "Brazilian house backyard on a cloudy Sunday afternoon, soft wind in trees, distant birds, a dog barking far away, quiet, no music", True),
 "L_reza": (12.0, "A small group of people softly praying together outdoors in Portuguese, murmured and indistinct, slow, sad, no music", False),
 "E_ei": (2.0, "A man shouting one short word 'Hey!' from far away in the dark, echoing over an empty field at night, no music", False),
 "E_vibra": (2.0, "A smartphone vibrating twice on a wooden table, close, no music", False),
 "E_msg": (1.0, "A soft generic smartphone message notification pop, short, no music", False),
 "E_porta_carro": (2.5, "A car door closing with a dull thud at night on a quiet road, no music", False),
 "E_tv_chiado": (8.0, "Old CRT television white noise static hiss with a faint electric hum, in a silent room, no music", True),
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
