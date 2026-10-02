import json, os, sys
from PIL import Image, ImageDraw
PREP=sys.argv[1]; OUT=sys.argv[2]; K=int(sys.argv[3]) if len(sys.argv)>3 else 3
os.makedirs(OUT, exist_ok=True)
rel=json.load(open(os.path.join(PREP,'preparo.json')))
GR=(104,168,72)
for esp,d in rel.items():
    W,H=d['canvas']; px,py=d['pivot']
    anims=[]
    for q in d['quadros']:
        k=(q['tipo'],q['anim'])
        if k not in anims: anims.append(k)
    cols=8
    sheet=Image.new('RGB',((W*cols)*K+120, H*K*len(anims)),(40,40,48))
    dr=ImageDraw.Draw(sheet)
    for ri,(t,an) in enumerate(anims):
        qs=[q for q in d['quadros'] if q['tipo']==t and q['anim']==an]
        dr.text((4,ri*H*K+4),f"{t}\n{an}",fill=(230,230,230))
        for q in qs:
            im=Image.open(os.path.join(PREP,esp,q['arquivo']))
            cell=Image.new('RGBA',(W,H),GR+(255,)); cell.alpha_composite(im)
            cell=cell.resize((W*K,H*K),Image.NEAREST)
            x=120+q['quadro']*W*K; y=ri*H*K
            sheet.paste(cell.convert('RGB'),(x,y))
            dr.line([(x+px*K,y+py*K-4),(x+px*K,y+py*K+4)],fill=(255,0,0)); dr.line([(x+px*K-4,y+py*K),(x+px*K+4,y+py*K)],fill=(255,0,0))
            dr.rectangle([x,y,x+W*K-1,y+H*K-1],outline=(60,90,50))
    sheet.save(os.path.join(OUT,f'prancha_{esp}.png')); print(esp, sheet.size)
