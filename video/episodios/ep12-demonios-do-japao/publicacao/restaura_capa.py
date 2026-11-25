import sys, numpy as np, torch, cv2
from spandrel import ModelLoader
from PIL import Image
torch.set_num_threads(6)
src, out, x0, y0, x1, y1, alt = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:7]), int(sys.argv[7])
im = Image.open(src).convert("RGB"); W, H = im.size
im = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
im = im.resize((int(im.width * alt / im.height), alt), Image.LANCZOS)
x = np.asarray(im).astype(np.float32) / 255
m = ModelLoader().load_from_file("/dev/shm/modelos/x4plus.pth").model.eval()
h, w = x.shape[:2]; T, P = 256, 16; o = np.zeros((h * 4, w * 4, 3), np.float32)
with torch.no_grad():
    for y in range(0, h, T):
        for xx in range(0, w, T):
            ya, xa = max(0, y - P), max(0, xx - P); yb, xb = min(h, y + T + P), min(w, xx + T + P)
            r = m(torch.from_numpy(x[ya:yb, xa:xb]).permute(2, 0, 1)[None])[0].permute(1, 2, 0).clamp(0, 1).numpy()
            hh, ww = min(T, h - y) * 4, min(T, w - xx) * 4
            o[y * 4:y * 4 + hh, xx * 4:xx * 4 + ww] = r[(y - ya) * 4:(y - ya) * 4 + hh, (xx - xa) * 4:(xx - xa) * 4 + ww]
o = (o * 255).astype(np.uint8)
# cor: CLAHE leve na luminância (tinta mais viva, papel limpo)
lab = cv2.cvtColor(o, cv2.COLOR_RGB2LAB); L, a, b = cv2.split(lab)
L = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8)).apply(L)
o = cv2.cvtColor(cv2.merge([L, a, b]), cv2.COLOR_LAB2RGB)
Image.fromarray(o).save(out, quality=95); print(out, o.shape)
