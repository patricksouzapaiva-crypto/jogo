import sys; sys.path.insert(0,".")
from traducao_en import EN
def blocos(idx, maxc):
    out, atual = [], []
    for i in idx:
        if atual and sum(len(EN[j][0]) for j in atual) + len(EN[i][0]) > maxc:
            out.append(atual); atual = []
        atual.append(i)
    return out + ([atual] if atual else [])
TODOS=[list(range(3,19))]+blocos(list(range(19,96)),2000)+blocos(list(range(97,133)),2000)
