import json, os, sys
from PIL import Image
d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'revisao', 'lado')
Z = 6
nomes = ['parado'] + [f'andar_{k}' for k in range(8)]
ims = [Image.open(f'{d}/{n}.png') for n in nomes]
w, h = ims[0].size
o = Image.new('RGBA', (w * len(ims) * Z, h * Z), (96, 140, 70, 255))
for i, im in enumerate(ims):
    o.alpha_composite(im.resize((w * Z, h * Z), Image.NEAREST), (i * w * Z, 0))
o.save(f'{d}/prancha_final.png'); print(o.size)
