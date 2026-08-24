# -*- coding: utf-8 -*-
"""Mede o contraste real da paleta nova, nos dois temas.

Acessibilidade WCAG estava no escopo original do projeto, e paleta trocada e
justamente quando ela quebra em silencio: nada da erro, o site so fica ilegivel
para quem tem baixa visao. Afirmar "conferido" sem medir seria o mesmo tipo de
alegacao sem fonte que o projeto inteiro combate.

Minimos: 4.5:1 para texto normal, 3:1 para texto grande e para bordas.
"""
import itertools
import pathlib
import re


def canal(v):
    v = v / 255
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def luminancia(hexcor):
    h = hexcor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def razao(a, b):
    la, lb = luminancia(a), luminancia(b)
    claro, escuro = max(la, lb), min(la, lb)
    return (claro + 0.05) / (escuro + 0.05)


HTML = pathlib.Path(r"c:\Users\BOC277 - Usuario\Documents\politica\_template_site.html").read_text(encoding="utf-8")


def bloco(marcador, fim):
    i = HTML.index(marcador)
    return dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9A-Fa-f]{6})", HTML[i:HTML.index(fim, i)]))


claro = bloco("  :root{", "@media (prefers-color-scheme: dark)")
escuro = bloco(':root[data-theme="dark"]{', "*,*::before")

TEXTOS = ["ink", "ink-2", "muted", "marca",
          "s-oficial", "s-verificada", "s-secundaria", "s-declaracao", "s-registro", "alert"]
FUNDOS = ["ground", "surface", "surface-2", "surface-3", "marca-fraca"]

falhas = []
for nome, pal in (("CLARO", claro), ("ESCURO", escuro)):
    print(f"=== tema {nome} ===")
    pior = ("", 99)
    for txt, fun in itertools.product(TEXTOS, FUNDOS):
        if txt not in pal or fun not in pal:
            continue
        r = razao(pal[txt], pal[fun])
        if r < pior[1]:
            pior = (f"--{txt} sobre --{fun}", r)
        if r < 4.5:
            falhas.append(f"{nome}: --{txt} sobre --{fun} = {r:.2f}:1")
    print(f"  pares conferidos com o minimo 4.5:1 · pior par: {pior[0]} = {pior[1]:.2f}:1")

    # bordas e reguas: minimo 3:1 contra o fundo que separam
    for regra in ("rule-strong", "focus"):
        if regra in pal:
            r = min(razao(pal[regra], pal["surface"]), razao(pal[regra], pal["surface-2"]))
            estado = "ok" if r >= 3 else "ABAIXO DE 3:1"
            print(f"  --{regra} sobre superficies = {r:.2f}:1  {estado}")
            if r < 3:
                falhas.append(f"{nome}: --{regra} sobre superficies = {r:.2f}:1")

print()
if falhas:
    print(f"{len(falhas)} par(es) abaixo do minimo:")
    for f in falhas:
        print("  " + f)
else:
    print("Todos os pares de texto passam de 4.5:1 e as bordas de 3:1 nos dois temas.")
