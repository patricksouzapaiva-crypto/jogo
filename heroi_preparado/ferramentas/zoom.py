import sys
from PIL import Image, ImageDraw
src, x0, y0, x1, y1, z, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
im = Image.open(src).convert('RGBA')
c = im.crop((x0, y0, x1, y1))
bg = Image.new('RGBA', c.size, (60, 60, 70, 255)); bg.alpha_composite(c)
zimg = bg.resize((c.width * z, c.height * z), Image.NEAREST)
d = ImageDraw.Draw(zimg)
for x in range((x0 // 10 + 1) * 10, x1, 10):
    col = (255, 60, 60) if x % 50 == 0 else (120, 120, 130)
    d.line([((x - x0) * z, 0), ((x - x0) * z, zimg.height)], fill=col)
    if x % 50 == 0: d.text(((x - x0) * z + 2, 2), str(x), fill=(255, 255, 0))
for y in range((y0 // 10 + 1) * 10, y1, 10):
    col = (255, 60, 60) if y % 50 == 0 else (120, 120, 130)
    d.line([(0, (y - y0) * z), (zimg.width, (y - y0) * z)], fill=col)
    if y % 50 == 0: d.text((2, (y - y0) * z + 2), str(y), fill=(0, 255, 255))
zimg.save(out); print(zimg.size)
