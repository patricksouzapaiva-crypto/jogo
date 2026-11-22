"""23/11 — a NBC Universal bloqueou o vídeo (Content ID, visual) pelos ~6 min de filme usados DE FUNDO.
Cada cena de fundo do filme vira uma ilustração ORIGINAL (Gemini imagem), no estilo das IA01–05: fotográfica, grão de
cinema, SEM rosto humano, sem texto. O filme só fica nas falas-pista (comentário). Saída: imagens/IL_<nome>_<v>.jpg
Uso: python3 gerar_ilustracoes.py [nome ...]"""
import base64, json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
SAI = Path(__file__).parent / "imagens"; SAI.mkdir(exist_ok=True)
MODELO = "gemini-3-pro-image-preview"
ESTILO = (" Cinematic horror film still, photorealistic, moody motivated lighting, shallow depth of field, subtle film grain, "
          "wide 16:9 composition. Absolutely NO visible human faces (people only from behind, in silhouette, or just hands/limbs), "
          "no text, no letters, no watermark.")
CASA = "inside a modern American suburban family house with warm wood floors and white walls"
MULHER = "a tall thin woman with very long straight black hair and bangs, wearing black"
MENINA = "a small 8-year-old girl with a short strawberry-blonde bob haircut and a lavender hoodie"
CENAS = {
    "porta_azul": f"A bedroom door painted pale blue, slightly ajar at night, {CASA}; through the gap a long thin shadow of {MULHER} falls across the hallway floor; cold blue moonlight.",
    "espelho": "A bathroom mirror at night, fogged with steam, smudged long-fingered handprints on the glass, the reflection shows only an empty dark doorway behind; single warm bulb.",
    "almoco": f"A sunny kitchen at noon {CASA}, a table set for lunch for two, a woman's pale hand with long fingers placing a plate, cropped at the wrist, the rest out of frame.",
    "cozinha": f"Seen from behind, {MULHER} standing perfectly still at a kitchen stove at midday, steam rising from a pot, bright window light, uncanny stillness.",
    "mesa": "Under a wooden dining table, in the shadow, long pale human arms and legs folded at impossible angles like a spider, long black hair spilling on the floor, only limbs and hair visible, chairs around, warm afternoon light.",
    "quarto_portas": "A child's bedroom at night, a closet door slightly open with pure darkness inside, a small amber nightlight on the floor, toys, drawings on the wall.",
    "segredos": "A two-story suburban family house at dusk seen from the street, only one window lit, the rest dark, a single cigarette glowing on the dark back porch.",
    "pais_briga": "A kitchen at night seen through a half-open door: two adult silhouettes arguing behind a frosted glass door, a child's crayon drawing on the fridge in the foreground.",
    "outra_silhueta": f"{MULHER} standing in a dark doorway at the end of a hallway, strongly backlit, her face completely lost in black shadow, only the outline of hair and shoulders.",
    "carro": "Seen from the back seat, a woman with long black hair wearing a bright yellow dress sitting in the driver's seat of a parked car, rain on the windows, face not visible.",
    "bela_cama": f"Top-down view of {MENINA} asleep in bed seen from behind under a quilt, and at the foot of the bed the long dark shadow of a tall figure on the wall.",
    "maos_porta": "Many pale long-fingered hands pressed against the other side of a frosted glass door at night, only the blurred hands visible through the glass, cold light.",
    "ritual_sal": "Top-down view of a large heart shape drawn in white salt on a dark wooden floor, a lit candle and a bowl of water in the center, dim room.",
    "uv": "A ritual gone wrong in a dark living room: candle knocked over, salt scattered across the floor, eerie ultraviolet purple light flooding the room, a huge distorted shadow of a long-haired figure on the wall.",
    "rasteja": "A figure covered by a pale blue towel crawling on a white-tiled bathroom floor in dim green light, only long thin arms visible reaching forward, unsettling.",
    "maquete": f"Close-up of a handmade cardboard model house on a table, inside one tiny room a small doll with long black hair, {MENINA} seen from behind with her small hand reaching in.",
    "bela_sozinha": f"Seen from behind, {MENINA} sitting alone on the floor of a big empty living room playing with a cardboard model house, adult legs walking past in the background out of focus.",
    "botas": "By the front door of a family house, three pairs of rubber boots in a row (father's, mother's, a child's) and next to them a fourth pair of black women's shoes that does not belong, morning light.",
    "praca": "Overhead view of a family table in a busy shopping mall food court, trays of food, one empty chair, the surrounding crowd motion-blurred with no faces visible.",
    "outro_lado": "An upside-down living room: sofa, lamp and dining table attached to the ceiling, dim red light, dreamlike and wrong, empty of people.",
    "afundou": "A children's indoor ball pit full of colorful plastic balls, a small child's hand sinking under the balls, harsh fluorescent light, eerie.",
    "avo": "An old grandmother's farmhouse kitchen at night, an oil lamp lit on a wooden table, wrinkled elderly hands holding a cup of tea, warm low light.",
    "confissao": "A kitchen table at night, a woman's hands clasped tightly, a half-empty glass of red wine, a single lamp, heavy silence.",
    "cicatriz": "Extreme close-up of a woman's shoulder and upper arm with a long vertical stitched scar that looks like a zipper, dark moody light, no face.",
    "maos_avo": f"An old woman's wrinkled hand holding the small hand of {MENINA}, close-up of the two hands only, soft window light.",
    "familia_fim": "A family of three (father, mother, little girl) walking away down a sunny suburban sidewalk seen from behind holding hands, long shadows, autumn.",
    "escola": f"An elementary school classroom, {MENINA} seen from behind standing at the front of the class reading a paper aloud, rows of small desks, daylight.",
    "pos_creditos": "A dark empty child's bedroom, the closet door slightly open, a pale long-fingered hand curling around the edge of the door from inside the darkness.",
    "medium": "A spiritual medium's table: several lit candles, crystals, an old leather book, a woman's hands with many silver rings hovering over it, dark room.",
    "frank": "An empty booth in a roadside diner at night, a man's denim jacket left on the seat, a spilled cup of coffee dripping off the table, neon light through the window.",
    "abraco": f"In a dim bathroom, a very tall dark figure with long black hair kneeling and embracing {MENINA}, both seen from behind, the figure's arms unnaturally long wrapping around her.",
    "tunel": "Inside a glowing red plastic tube slide tunnel at an indoor playground, the tunnel curving into darkness, red light everywhere.",
    "bolinhas": "A child's bedroom floor turned into an ocean of colorful plastic balls up to the bed, a small sneaker floating on top, night light, surreal.",
    "mar": "View from the back seat of a car at night driving along a dark coastal road, the black sea and white waves visible through the window, headlights.",
    "escada": f"Seen from behind, {MENINA} running up a dark staircase {CASA}, motion blur, a door at the top glowing faintly.",
    "espelho_rachado": "A cracked bathroom mirror in darkness, long strands of black hair caught in the cracks, a single drop of water running down.",
}


def gerar(nome, v):
    saida = SAI / f"IL_{nome}_{v}.jpg"
    if saida.exists():
        return nome, v, "já"
    corpo = {"contents": [{"parts": [{"text": CENAS[nome] + ESTILO + (" Variation with a different camera angle." if v == 2 else "")}]}],
             "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9", "imageSize": "2K"}}}
    for t in range(4):
        try:
            req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent",
                                         json.dumps(corpo).encode(), {"Content-Type": "application/json", "x-goog-api-key": "x"})
            r = json.loads(urllib.request.urlopen(req, timeout=240).read())
            for p in r["candidates"][0]["content"]["parts"]:
                if "inlineData" in p:
                    saida.write_bytes(base64.b64decode(p["inlineData"]["data"]))
                    return nome, v, "ok"
            return nome, v, "sem imagem: " + json.dumps(r)[:200]
        except Exception as e:
            err = str(e); time.sleep(10 * (t + 1))
    return nome, v, "erro " + err


if __name__ == "__main__":
    nomes = sys.argv[1:] or list(CENAS)
    with ThreadPoolExecutor(5) as ex:
        for r in ex.map(lambda a: gerar(*a), [(n, v) for n in nomes for v in (1, 2)]):
            print(*r, flush=True)
