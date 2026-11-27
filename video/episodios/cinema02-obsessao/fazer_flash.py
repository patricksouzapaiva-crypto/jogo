"""g_flash (27/11, usuário: "na hora que falar quem fica no caminho morre, coloca a cena em flash dela socando a cabeça da
menina, de forma bem rápida e borrada pro vídeo não cair"; depois: "rápido demais… muito seco"): dois instantes do ataque
no carro (1:27:52.2–53.0 e 1:27:55.8–56.7), borrados, em câmera lenta (0,75×), fundidos entre si e com o preto, na
mesma moldura de arquivo; som: só um baque abafado. Saída H.264 yuv420p (o xfade sai em yuv444).
Uso: python3 fazer_flash.py → filmes_prontos/g_flash.mp4 + .wav (e atualiza trechos.json)"""
import json, subprocess
from pathlib import Path
AQUI = Path(__file__).parent; SAI = AQUI / "filmes_prontos"; F = AQUI / "filme" / "obsessao.mkv"
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
fw, fh = 1440, 960; fx, fy = (1920 - fw) // 2, 80
cor = "crop=1620:1080:150:0,boxblur=9:2,eq=gamma=1.25:brightness=0.03:saturation=0.8,setpts=PTS/0.75,fps=24"
fc = (f"[0:v:0]trim=5272.2:5273.0,setpts=PTS-STARTPTS,{cor}[a];[1:v:0]trim=5275.8:5276.7,setpts=PTS-STARTPTS,{cor}[b];"
      f"[a][b]xfade=transition=fade:duration=0.3:offset=0.77,format=yuv420p,split[x][y];"
      f"[x]scale=480:320,boxblur=12:3,eq=brightness=-0.24:saturation=0.6,scale=1920:1080,setsar=1[fundo];"
      f"[y]scale={fw}:{fh},pad={fw + 4}:{fh + 4}:2:2:color=0xb8b0a4@0.55[q];[fundo][q]overlay={fx - 2}:{fy - 2},"
      f"drawtext=fontfile={FONTE}:text='TRECHO DE FILME':fontsize=22:fontcolor=0xc8302c:x={fx}:y={fy - 42},"
      f"drawtext=fontfile={FONTE}:text='OBSESSÃO (2026) · DIR. CURRY BARKER':fontsize=22:fontcolor=0xd8d0c4:x={fx + 230}:y={fy - 42},"
      f"fade=t=in:d=0.3,fade=t=out:st=1.7:d=0.35,trim=0:2.05,format=yuv420p[v]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "5270", "-t", "8", "-copyts", "-i", str(F), "-ss", "5270", "-t", "8", "-copyts",
                "-i", str(F), "-filter_complex", fc, "-map", "[v]", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                str(SAI / "g_flash.mp4")], check=True)
baque = AQUI.parents[1] / "painel" / "sons" / "impacto.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(next(baque.parent.glob("impacto.*"))), "-af",
                "lowpass=f=420,volume=0.8,apad,atrim=0:2.05,afade=t=out:st=1.5:d=0.5", "-ar", "48000", "-ac", "2",
                "-c:a", "pcm_s16le", str(SAI / "g_flash.wav")], check=True)
info = json.loads((SAI / "trechos.json").read_text()) if (SAI / "trechos.json").exists() else {}
info["g_flash"] = {"dur": 2.05, "video_dur": 2.05, "som": True, "falas": []}
(SAI / "trechos.json").write_text(json.dumps(info, ensure_ascii=False, indent=1)); print("ok g_flash")
