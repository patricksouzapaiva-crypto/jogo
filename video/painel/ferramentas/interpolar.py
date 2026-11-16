"""Câmera lenta / mais quadros com RIFE 4.25 lite (16/11, pesquisa do motor). Substitui o `minterpolate` do ffmpeg
(que borra ou deforma o movimento) por quadros intermediários de verdade, estimados pela rede (Practical-RIFE de hzwer,
MIT; ONNX de huggingface.co/t9749/rife-4.25-lite-onnx). Roda na CPU (onnxruntime).
Uso: python3 interpolar.py entrada.mp4 saida.mp4 [lento=1.25] [fps=30]
  lento: 1 = mesma velocidade (só sobe os quadros por segundo); 1.25 = 25% mais lento; 2 = metade da velocidade."""
import subprocess, sys, json
from pathlib import Path
import numpy as np

MODELO = Path.home() / ".cache" / "rife" / "rife_v425lite.onnx"
URL = "https://huggingface.co/t9749/rife-4.25-lite-onnx/resolve/main/rife_v425lite.onnx"
_sess = None


def sessao():
    global _sess
    if _sess is None:
        if not MODELO.exists():
            MODELO.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["curl", "-sL", "-o", str(MODELO), URL], check=True)
        import onnxruntime as ort
        so = ort.SessionOptions(); so.intra_op_num_threads = 4
        _sess = ort.InferenceSession(str(MODELO), so, providers=["CPUExecutionProvider"])
    return _sess


def meio(a, b, t):
    """Quadro no instante t (0..1) entre a e b (uint8 HxWx3, RGB)."""
    s = sessao()
    h, w = a.shape[:2]; H, W = (h + 63) // 64 * 64, (w + 63) // 64 * 64
    def prep(x):
        y = np.zeros((H, W, 3), np.float32); y[:h, :w] = x / 255.0
        return y.transpose(2, 0, 1)[None]
    out = s.run(None, {"img0": prep(a), "img1": prep(b), "timestep": np.full((1, 1, 1, 1), t, np.float32)})[0][0]
    return (np.clip(out.transpose(1, 2, 0)[:h, :w], 0, 1) * 255 + 0.5).astype(np.uint8)


def interpolar(entrada, saida, lento=1.25, fps=30):
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                      "stream=width,height,r_frame_rate", "-of", "json", str(entrada)], capture_output=True, text=True).stdout)
    st = info["streams"][0]; w, h = st["width"], st["height"]
    n_, d_ = st["r_frame_rate"].split("/"); fps_src = float(n_) / float(d_)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(entrada), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    quadros = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    n_out = int(len(quadros) / fps_src * lento * fps)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps),
                             "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", str(saida)],
                            stdin=subprocess.PIPE)
    for k in range(n_out):
        ts = k / fps / lento * fps_src                      # posição no vídeo original, em quadros
        i = int(ts); t = ts - i
        if i + 1 >= len(quadros):
            q = quadros[-1]
        elif t < 0.02:
            q = quadros[i]
        elif t > 0.98:
            q = quadros[i + 1]
        else:
            a, b = quadros[i], quadros[i + 1]
            # corte de cena (quadros muito diferentes): não inventa um meio-termo, pula para o mais perto
            q = (a if t < 0.5 else b) if np.abs(a.astype(np.int16) - b).mean() > 40 else meio(a, b, t)
        proc.stdin.write(q.tobytes())
    proc.stdin.close(); proc.wait()
    return saida


if __name__ == "__main__":
    a = sys.argv[1:]
    interpolar(a[0], a[1], float(a[2]) if len(a) > 2 else 1.25, int(a[3]) if len(a) > 3 else 30)
