"""Trilha do Ep. 09, composta por partes (ElevenLabs Music), uma faixa para cada momento do roteiro.
Pedido do usuário (13/11): "no terror a música é o que mais marca; caprichar mais". No Ep. 08 era uma faixa
única sintetizada, baixinha, o episódio inteiro. Aqui cada parte tem a sua, todas com a mesma instrumentação
coreana (gayageum, haegeum, daegeum/piri, janggu, jing) e o mesmo TEMA (uma melodia curta de gayageum que volta
no gancho, no "han", na Bia e no fim, cada vez mais triste). Regras da casa: sem susto, sem pancada repentina,
saídas lentas.
Uso: python3 gerar_trilha.py [nome ...]  → faixas/<nome>.mp3  (pula as que já existem)"""
import sys, time, requests
from pathlib import Path

AQUI = Path(__file__).parent
(AQUI / "faixas").mkdir(exist_ok=True)
URL = "https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192"
BASE = ("Instrumental Korean horror film score, no vocals, no singing, no choir words. Cinematic, high-end, "
        "intimate, recorded close. Traditional Korean instruments with dark orchestral strings. "
        "No sudden hits, no jump scares, no drops; slow swells and slow fade-out at the end. ")
TEMA = ("The main theme: a slow, simple, memorable 5-note gayageum melody in a minor pentatonic mode, "
        "descending, with long pauses and bent notes (nonghyeon vibrato), like a lullaby nobody finishes. ")

FAIXAS = {
    # gancho 0:00–0:40: o áudio das três; quase nada, o tema aparece no fim
    "01_tres_da_tarde": (75, "Continuous from the very first second, never silent: a low warm sub drone with slow "
                         "beating, a soft airy noise bed, a single gayageum note plucked and bent every few seconds "
                         "with long resonance. Around the middle the main theme is played once, quietly, solo "
                         "gayageum, and stops mid-phrase while the drone continues to the end. " + TEMA),
    # tema 0:40–1:55: o Vigia apresenta o han
    "02_han": (100, "The opening theme of the episode. A haegeum (Korean two-string fiddle) plays a mournful, "
               "crying lament over soft low strings; then the gayageum answers with the main theme. Deep, "
               "sad and beautiful, slowly growing in intensity like a grief that keeps growing, then settling "
               "back to a single held note. " + TEMA),
    # a Bia 1 + andar F + ventilador: curiosidade que vai azedando
    "03_as_regras": (180, "Uneasy curiosity. Light, sparse plucked gayageum ostinato like a music box, a soft "
                     "ticking pulse, quiet pizzicato strings. Slowly, very slowly, a low dissonant cello note "
                     "creeps in underneath and the ostinato starts to sound wrong, slightly out of tune. "
                     "Late-night, small empty room, something not right."),
    # parte 3: o conto das irmãs da era Joseon
    "04_joseon_irmas": (170, "A Joseon-era folk tale told at night. Daegeum (large bamboo flute) with breathy, "
                        "airy tone over a very slow buk drum heartbeat and a quiet ajaeng (bowed zither) drone. "
                        "Eerie still water, fog over a lake, two sisters. Melancholic and cold, in the middle "
                        "the gayageum plays the main theme slowly. Ends unresolved. " + TEMA),
    # a Bia 2 + parte 4: o choro na parede, as batidas, godoksa
    "05_a_parede": (200, "Pure dread, very quiet. Low sustained dissonant strings, sul ponticello whispers, "
                    "slow sub-bass pulses like a heartbeat behind a wall, scraped gayageum strings, sparse "
                    "metallic resonances. Lonely, claustrophobic, the smell of a closed room. Minimal melody. "
                    "Dark ambient horror, slow evolution, never loud."),
    # a Bia 3 + parte 5: o nome em vermelho, a moça de branco, o casamento de almas
    "06_moca_de_branco": (200, "A ghost bride. A slow, sad, distorted Korean wedding melody played on piri "
                          "(double-reed oboe) far away, as if from another room, over trembling strings. "
                          "The gayageum plays the main theme in a lower register, darker. Beautiful and wrong, "
                          "mourning and wedding at the same time. Builds slightly, then fades. " + TEMA),
    # a Bia 4: o chamado no corredor com a voz da mãe (o clímax da história)
    "07_o_chamado": (100, "The climax of dread, slow and unbearable, continuous from the first second with NO "
                     "silence and NO sudden entrance: begins with a quiet high thin string harmonic and a low "
                     "drone, then a very slow, steady crescendo over 70 seconds of clustered dissonant strings "
                     "and low brass, a breathing haegeum, a deep jing gong swelling softly (no hit). In the last "
                     "25 seconds it slowly dissolves into a long dark reverb tail and a low drone."),
    # parte 6: a mudang, o gut, Exhuma
    "08_gut_mudang": (180, "A Korean shaman ritual (gut). Starts with a slow janggu (hourglass drum) pattern and "
                      "a jing gong, a piri melody bending wildly, bells (bangul) shaking. Gradually the rhythm "
                      "speeds up into a hypnotic trance with layered janggu and buk drums and dark low strings, "
                      "intense but controlled, never a sudden hit. In the last 30 seconds it slows down and ends "
                      "on a long gong decay."),
    # a Bia 5 + 6: o quarto, os cadernos, até hoje
    "09_o_quarto": (210, "Devastating sadness. The main theme returns as a slow lullaby: solo gayageum, then a "
                    "soft felt piano doubles it, then warm low strings carry it. Heartbreaking, quiet, like an "
                    "empty room in the morning light. Towards the end only the gayageum remains, playing the "
                    "theme one last time, and it stops before the last note. " + TEMA),
    # fecho do Vigia
    "10_fecho": (100, "Closing reflection. A low warm drone, a few sparse soft piano notes and a distant haegeum "
                 "playing fragments of the main theme. Calm but unsettling, intimate, as if someone is still "
                 "in the room. Fades into near silence. " + TEMA),
}

pedidas = sys.argv[1:] or list(FAIXAS)
for nome in pedidas:
    seg, desc = FAIXAS[nome]
    saida = AQUI / "faixas" / f"{nome}.mp3"
    if saida.exists():
        continue
    corpo = {"prompt": BASE + desc, "music_length_ms": seg * 1000, "force_instrumental": True}
    for tent in range(4):
        r = requests.post(URL, headers={"xi-api-key": "proxy"}, json=corpo, timeout=600)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("audio"):
            saida.write_bytes(r.content); print("ok", nome, f"{len(r.content) / 1e6:.1f} MB", flush=True); break
        print(nome, r.status_code, r.text[:300], flush=True); time.sleep(15)
