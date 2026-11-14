import sys, hashlib, json
sys.path.insert(0,"."); sys.path.insert(0,"../../../painel")
import gerar; gerar.IDIOMA["whisper"]="en"
from gerar import CACHE, tokens, alinhar, transcrever, norm
from traducao_en import EN
import narrar_en_blocos as nb
res={}
for bl in nb.TODOS:
    texto="\n".join(EN[i][0] for i in bl)
    w=CACHE/("en_"+hashlib.sha1(f"gemini-3.1-flash-tts-preview|Algenib|{texto}".encode()).hexdigest()[:16]+".wav")
    ouv=[norm(x[0]) for x in transcrever(w,"")]
    # quantas batidas do bloco foram faladas: procura a última batida cuja última palavra aparece na transcrição
    feitas=[]
    pos=0
    for i in bl:
        pal=[norm(p) for p in tokens(EN[i][0])]
        ult=pal[-1]
        try:
            j=ouv.index(ult,pos); feitas.append(i); pos=j+1
        except ValueError:
            break
    falt=[i for i in bl if i not in feitas]
    print(bl[0],"-",bl[-1],"faltam:",falt, "| fim ouvido:", " ".join(ouv[-8:]))
    res[bl[0]]=falt
json.dump(res,open("faltam.json","w"))
