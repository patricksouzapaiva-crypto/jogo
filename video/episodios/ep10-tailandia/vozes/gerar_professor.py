"""Ep. 10 (16/11, pedido do usuário no rascunho 2: "a fala do professor não entra… fica sem sentido"): o áudio de
WhatsApp do Prof. Henrique respondendo ao Mateus (antes era só a mensagem escrita na tela). 1 pedido do Gemini TTS.
Saída: limpas_escolhidas/prof.wav (instrução lida em voz alta é cortada pelo Whisper, como nas outras falas)."""
import sys
from pathlib import Path
sys.argv = [sys.argv[0], "--so-funcoes"]
AQUI = Path(__file__).parent
src = (AQUI / "gerar_vozes.py").read_text()
exec(src[:src.index('if "--amostra" in sys.argv:')])
FALA = "Mateus, não abre essa porta! Lembra do que você pesquisou sobre os Rang Song. Não abre!"
JEITO_P = ("Homem de 55 anos, professor universitário, acordado de madrugada pelo celular, desesperado e com autoridade, "
           "falando alto e rápido, quase gritando de medo pelo aluno.")
VOZ = sys.argv[2] if len(sys.argv) > 2 else "Orus"
arq = B / f"prof_{VOZ}.wav"
if not arq.exists():
    gerar(f"{BASE}{JEITO_P} Diga: {FALA}", VOZ, arq)
cortar(arq, FALA, L / "prof.wav")
