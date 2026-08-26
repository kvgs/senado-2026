# -*- coding: utf-8 -*-
"""Baixa a malha oficial do IBGE e a simplifica para dados/mapa-uf.json.

RODA UMA VEZ, NAO A CADA GERACAO. O site nao pode depender de o servico do IBGE
estar no ar para ser publicado. A malha crua fica em fontes/, para procedencia,
e o resultado simplificado em dados/ — igual a qualquer outra fonte do acervo.

POR QUE SIMPLIFICAR. A malha oficial tem 51.814 pontos e 391 KB. A pagina
inicial inteira tem 18 KB. Medido:

    tolerancia   pontos   SVG    erro a 900px   erro a 360px
           500     2646   42 KB       1,0 px         0,4 px
          1000     1396   22 KB       2,0 px         0,8 px
          2000      788   13 KB       4,0 px         1,6 px

Fico em 1000: 22 KB com erro de dois pixels na maior largura em que o mapa
aparece, e menos de um pixel no celular. Erro invisivel.

DOUGLAS-PEUCKER ITERATIVO, e nao recursivo. Anel de 3.000 pontos estoura a pilha
padrao do Python, e subir o limite de recursao para contornar isso e trocar um
erro visivel por um estouro de pilha no meio de outra coisa.

O ID DE CADA PATH E O CODIGO DO IBGE (35 = SP). A tabela de codigo para sigla
mora aqui, escrita, porque nao da para derivar — e errar isso pintaria o estado
errado no mapa sem nenhum aviso.
"""
import json
import pathlib
import re
import urllib.request

AQUI = pathlib.Path(__file__).resolve().parent
BRUTO = AQUI / "fontes" / "mapa-ibge-uf.svg"
SAIDA = AQUI / "dados" / "mapa-uf.json"

URL = ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
       "?formato=image/svg+xml&intrarregiao=UF")

TOLERANCIA = 1000

# Codigo do IBGE -> sigla. Escrito, e nao derivado: errar aqui pinta o estado
# errado e nada avisa.
CODIGO = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


def baixar() -> str:
    if BRUTO.exists():
        print(f"malha ja baixada: {BRUTO.relative_to(AQUI)} "
              f"({BRUTO.stat().st_size/1024:.0f} KB)")
        return BRUTO.read_text(encoding="utf-8")
    req = urllib.request.Request(URL, headers={
        "User-Agent": "senado-2026/1.0 (projeto civico; +https://kvgs.github.io/senado-2026/)"})
    with urllib.request.urlopen(req, timeout=90) as r:
        s = r.read().decode("utf-8")
    BRUTO.write_text(s, encoding="utf-8")
    print(f"baixado do IBGE: {len(s)/1024:.0f} KB -> {BRUTO.relative_to(AQUI)}")
    return s


def aneis(d: str) -> list[list[tuple[float, float]]]:
    """Le o path do IBGE (M/m/L/l/Z relativos) e devolve aneis absolutos."""
    saida, atual = [], []
    x = y = 0.0
    for cmd, corpo in re.findall(r"([MmLlZz])([^MmLlZz]*)", d):
        nums = [float(n) for n in re.findall(r"-?\d+\.?\d*", corpo)]
        if cmd in "Zz":
            if atual:
                saida.append(atual); atual = []
            continue
        for i in range(0, len(nums) - 1, 2):
            a, b = nums[i], nums[i + 1]
            if cmd in "Mm":
                if atual:
                    saida.append(atual); atual = []
                x, y = (a, b) if cmd == "M" else (x + a, y + b)
            else:
                x, y = (a, b) if cmd == "L" else (x + a, y + b)
            atual.append((x, y))
    if atual:
        saida.append(atual)
    return saida


def simplificar(pts, tol):
    """Douglas-Peucker sem recursao: pilha explicita de intervalos."""
    if len(pts) < 3:
        return list(pts)
    manter = [False] * len(pts)
    manter[0] = manter[-1] = True
    pilha = [(0, len(pts) - 1)]
    while pilha:
        ini, fim = pilha.pop()
        if fim <= ini + 1:
            continue
        ax, ay = pts[ini]; bx, by = pts[fim]
        dx, dy = bx - ax, by - ay
        norma = (dx * dx + dy * dy) ** 0.5
        pior, idx = -1.0, ini
        for i in range(ini + 1, fim):
            px, py = pts[i]
            dist = (abs(dy * (px - ax) - dx * (py - ay)) / norma if norma
                    else ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5)
            if dist > pior:
                pior, idx = dist, i
        if pior > tol:
            manter[idx] = True
            pilha.append((ini, idx)); pilha.append((idx, fim))
    return [p for p, m in zip(pts, manter) if m]


def main() -> int:
    s = baixar()
    vb = s.split('viewBox="')[1].split('"')[0]
    # O IBGE nega o y na exibicao: as coordenadas do path sao latitude*10000, e o
    # grupo aplica scale(0.0001,-0.0001). Guardo o transform em vez de embutir a
    # conta nas coordenadas — reproduzir o transform do IBGE garante a geometria
    # certa; refazer a aritmetica e uma chance de espelhar o pais e nao notar.
    m = re.search(r'<g[^>]*transform="([^"]+)"', s)
    if not m:
        raise SystemExit("a malha do IBGE veio sem transform no grupo; conferir antes de usar")
    transform = m.group(1)
    paths = re.findall(r'<path id="(\d+)" d="([^"]+)"', s)
    if len(paths) != 27:
        raise SystemExit(f"esperava 27 estados na malha, achei {len(paths)}")

    faltam = sorted(set(CODIGO) - {c for c, _ in paths})
    if faltam:
        raise SystemExit(f"codigos do IBGE ausentes na malha: {faltam}")

    ufs, antes, depois = {}, 0, 0
    for cod, d in paths:
        uf = CODIGO.get(cod)
        if not uf:
            raise SystemExit(f"codigo {cod} nao esta na tabela CODIGO — mapa incompleto")
        partes = []
        for anel in aneis(d):
            antes += len(anel)
            novo = simplificar(anel, TOLERANCIA)
            # Anel que sobra com menos de 3 pontos nao e area: descarta, senao
            # vira um risco na tela.
            if len(novo) < 3:
                continue
            depois += len(novo)
            p = f"M{int(novo[0][0])},{int(novo[0][1])}"
            for px, py in novo[1:]:
                p += f"L{int(px)},{int(py)}"
            partes.append(p + "Z")
        ufs[uf] = "".join(partes)

    corpo = sum(len(v) for v in ufs.values())
    SAIDA.write_text(json.dumps({
        "_nota": ("Malha das 27 unidades da federacao, do IBGE, simplificada por "
                  f"Douglas-Peucker com tolerancia {TOLERANCIA} — cerca de dois pixels "
                  "de desvio a 900px de largura. A malha crua esta em "
                  "fontes/mapa-ibge-uf.svg. Gerado por gerar_mapa.py; nao editar a mao."),
        "_fonte": "IBGE — Servico de Dados, malhas territoriais (API v3)",
        "_url": URL,
        "viewBox": vb,
        "transform": transform,
        "_eixo": ("y do path e latitude*10000, e CRESCE para o norte. O transform nega,"
                  " entao na tela o y cresce para baixo, como de costume."),
        "tolerancia": TOLERANCIA,
        "paths": ufs,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"pontos: {antes} -> {depois}  ({100 - depois*100//antes}% menos)")
    print(f"path de todos os estados: {corpo/1024:.0f} KB")
    print(f"escrito: {SAIDA.relative_to(AQUI)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
