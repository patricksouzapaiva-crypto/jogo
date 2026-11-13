"""Confere cada faixa: duração, volume e se tem 'pancada' (salto > 12 dB em meio segundo) — regra: sem susto."""
import glob, subprocess, sys, numpy as np
for f in sorted(glob.glob(sys.argv[1] if len(sys.argv) > 1 else "faixas/*.mp3")):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
                                     capture_output=True).stdout, np.float32)
    j = x[:len(x) // 2000 * 2000].reshape(-1, 2000)          # janelas de 0,25 s
    db = 20 * np.log10(np.sqrt((j ** 2).mean(1)) + 1e-6)
    salto = [(i / 4, db[i] - db[max(0, i - 2):i].max()) for i in range(2, len(db)) if db[i] - db[max(0, i - 2):i].max() > 12 and db[i] > -30]
    print(f"{f.split('/')[-1]:24s} {len(x) / 8000:6.1f}s  média {np.median(db):5.1f} dB  máx {db.max():5.1f}  "
          f"saltos: {[(round(t, 1), round(d)) for t, d in salto[:5]]}")
