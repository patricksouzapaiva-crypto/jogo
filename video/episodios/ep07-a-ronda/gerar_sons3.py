"""3ª rodada (12/11): o usuário achou as correntes com cara de RODA e a respiração ruim. Causa: prompts com
"dragged across floor" + escolha por grave (ronco contínuo). Agora: elos batendo/chacoalhando (transientes metálicos),
sem reforço de grave. 2 versões de cada → busca/sons3/<cod>_<v>.mp3. Chave injetada pelo proxy."""
import json, sys, time, requests
from pathlib import Path
AQUI = Path(__file__).parent; SAI = AQUI / "busca" / "sons3"; SAI.mkdir(parents=True, exist_ok=True)
P = {
 "C1": (8, "Heavy iron chains clanking and rattling as a prisoner slowly walks in shackles, each slow step makes the thick metal links clink and clank together, echoing stone corridor, horror foley"),
 "C2": (8, "Close-up foley of a thick rusty iron chain slowly pulled link by link through a metal ring, loud heavy metallic clanks and rattles, dungeon reverb"),
 "C3": (8, "Ghost rattling heavy chains, slow menacing clanking and jingling of thick iron chain links, haunted hospital hallway, distant echo"),
 "C4": (8, "A heavy iron chain slowly lowered link by link onto a stone floor, each link hitting the floor with a loud metallic clank, chain piling up, reverb"),
 "C5": (8, "Thick old iron chains swaying and clanking against an iron bed frame, slow heavy metallic rattling, cold empty room"),
 "R1": (10, "Slow heavy breathing of a large unseen creature right behind a closed door, deep raspy inhale through the nose, long rattling exhale, patient, horror foley, no voice"),
 "R2": (10, "Deep slow raspy human breathing in total darkness, close microphone, long inhale, slow shaky exhale, unsettling, horror"),
 "R3": (10, "Something sniffing slowly at the gap under a door, then a deep wet raspy breath, listening, eerie horror sound design"),
}
so = set(sys.argv[1:]); rel = {}
for cod, (dur, txt) in P.items():
    if so and cod not in so: continue
    for v in "ab":
        arq = SAI / f"{cod}_{v}.mp3"
        if arq.exists(): continue
        for k in range(4):
            r = requests.post("https://api.elevenlabs.io/v1/sound-generation", headers={"xi-api-key": "proxy"},
                json={"text": txt, "duration_seconds": dur, "prompt_influence": 0.7}, timeout=180)
            if r.status_code == 200: arq.write_bytes(r.content); print(cod, v, "ok"); break
            print(cod, v, r.status_code, r.text[:200]); time.sleep(8)
(AQUI / "busca" / "sons3.json").write_text(json.dumps({k: v[1] for k, v in P.items()}, indent=1, ensure_ascii=False))
