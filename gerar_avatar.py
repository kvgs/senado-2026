# -*- coding: utf-8 -*-
"""Gera o PNG da foto de perfil, a partir do mesmo mapa que o site desenha.

POR QUE UM SCRIPT, E NAO UMA CAPTURA DE TELA. Captura depende da tela de quem
capturou: escala, densidade de pixel, recorte a mao. Aqui o arquivo sai do mesmo
dado que o site usa (dados/mapa-uf.json), no tamanho pedido, sempre igual. E
quando a identidade mudar, regerar e um comando.

O MAPA E SILHUETA, e nao 27 estados. O Instagram exibe a foto de 40px a 150px,
e nesse tamanho as divisas viram sujeira. Os 27 poligonos sao pintados da mesma
cor, sem traco.

COMO O DESENHO SAI DO SVG. Os paths tem so M, L e Z — poligonos puros, porque o
mapa ja passou por Douglas-Peucker. Entao nao ha curva para aproximar: cada
contorno vira uma lista de pontos e e pintado direto. O transform do IBGE
(scale(0.0001,-0.0001)) e reproduzido, e nao refeito na mao: o eixo Y e NEGADO,
e refazer essa conta ja produziu mapa de cabeca para baixo neste projeto.

ANTISSERRILHADO por superamostragem: desenha em 4x e reduz. Poligono pintado
sem isso fica com a borda em escada, que aparece justamente no tamanho pequeno.

USO
    python gerar_avatar.py                 # opcao C, 1080px
    python gerar_avatar.py --opcao D --px 640
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

from PIL import Image, ImageDraw

RAIZ = pathlib.Path(__file__).resolve().parent
MAPA = RAIZ / "dados" / "mapa-uf.json"

# As quatro variantes comparadas com a curadoria. Cor de fundo, cor da forma, e
# quanto da largura o mapa ocupa. Os valores sao os tokens do site.
OPCOES = {
    "A": {"fundo": "#141110", "forma": "#2FB4E4", "ocupa": 0.64,
          "desc": "ciano sobre escuro"},
    "B": {"fundo": "#2FB4E4", "forma": "#141110", "ocupa": 0.64,
          "desc": "escuro sobre ciano"},
    "C": {"fundo": "#F7F4F1", "forma": "#0C6C8F", "ocupa": 0.64,
          "desc": "ciano fundo sobre papel"},
    "D": {"fundo": "#141110", "forma": "#2FB4E4", "ocupa": 0.88,
          "desc": "ciano sobre escuro, corte cheio"},
}

SUPER = 4  # superamostragem


def poligonos(dados: dict) -> list[list[tuple[float, float]]]:
    """Cada subcaminho vira uma lista de pontos, ja com o transform aplicado."""
    m = re.search(r"scale\(([-\d.]+),\s*([-\d.]+)\)", dados["transform"])
    if not m:
        raise SystemExit(f"nao entendi o transform: {dados['transform']!r}")
    sx, sy = float(m.group(1)), float(m.group(2))

    fora = []
    for _, d in sorted(dados["paths"].items()):
        for sub in d.split("Z"):
            sub = sub.strip()
            if not sub:
                continue
            pts = [(float(x) * sx, float(y) * sy)
                   for x, y in re.findall(r"[ML](-?[\d.]+),(-?[\d.]+)", sub)]
            if len(pts) >= 3:
                fora.append(pts)
    return fora


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--opcao", default="C", choices=sorted(OPCOES))
    ap.add_argument("--px", type=int, default=1080)
    ap.add_argument("--saida", default=None)
    a = ap.parse_args()
    o = OPCOES[a.opcao]

    dados = json.loads(MAPA.read_text(encoding="utf-8"))
    polis = poligonos(dados)

    xs = [p[0] for g in polis for p in g]
    ys = [p[1] for g in polis for p in g]
    larg, alt = max(xs) - min(xs), max(ys) - min(ys)

    lado = a.px * SUPER
    # O mapa cabe no quadrado pelo lado MAIOR, e nao pela largura: o Brasil e
    # quase quadrado, mas nao e, e escalar pela largura o cortaria em cima.
    escala = (lado * o["ocupa"]) / max(larg, alt)
    dx = (lado - larg * escala) / 2 - min(xs) * escala
    dy = (lado - alt * escala) / 2 - min(ys) * escala

    img = Image.new("RGB", (lado, lado), o["fundo"])
    d = ImageDraw.Draw(img)
    # AS FRESTAS PRECISAM SER FECHADAS. Depois da simplificacao, poligonos
    # vizinhos nao encostam com exatidao, e sobram fios do fundo entre estados —
    # numa silhueta isso le como rasgo, e o mais visivel cortava o mapa ao meio.
    # Cada contorno e repassado como linha grossa na mesma cor do preenchimento:
    # a borda engorda o suficiente para cobrir a fresta, sem alterar o formato.
    costura = max(3, round(lado * 0.008))
    for g in polis:
        pts = [(x * escala + dx, y * escala + dy) for x, y in g]
        d.polygon(pts, fill=o["forma"])
        d.line(pts + [pts[0]], fill=o["forma"], width=costura, joint="curve")

    img = img.resize((a.px, a.px), Image.LANCZOS)
    # A foto de perfil e material de Instagram, e nao codigo: mora junto com as
    # artes, e nao solta na raiz do repositorio.
    pasta = RAIZ / "artes-instagram" / "perfil-da-conta"
    pasta.mkdir(parents=True, exist_ok=True)
    saida = pathlib.Path(a.saida) if a.saida else pasta / f"avatar-{a.opcao.lower()}-{a.px}.png"
    img.save(saida, "PNG", optimize=True)
    print(f"gravado: {saida.name}  ({a.px}x{a.px}, {saida.stat().st_size/1024:.0f} KB)")
    print(f"  opcao {a.opcao} — {o['desc']}: forma {o['forma']} sobre {o['fundo']}, "
          f"ocupando {o['ocupa']:.0%} do quadro")
    print(f"  {len(polis)} contorno(s) de {len(dados['paths'])} estados, "
          f"pintados como silhueta unica")


if __name__ == "__main__":
    main()
