# -*- coding: utf-8 -*-
"""Reels vertical (1080x1920) de um estado, com os numeros medidos do acervo.

O QUE ISTO E, E O QUE NAO E. Nao ha geracao de video aqui: os quadros sao
desenhados um por um com o mesmo Pillow, a mesma tipografia e a mesma paleta das
artes estaticas, e o ffmpeg junta em MP4. O que se anima e a APRESENTACAO — texto
entrando, contador subindo, barra crescendo. Nenhum dado e inventado para caber no
ritmo.

SEM AUDIO. Este script nao produz som. Reels toca sem som por padrao, e a trilha
entra no proprio Instagram, onde ela e licenciada. Video com musica colada aqui
seria uso nao licenciado.

AS MESMAS DUAS TRAVAS DO CARROSSEL DE ANALISE:
  - so roda para estado 100% revisado, porque numero animado tem ainda mais cara
    de fato do que numero impresso, e nao mostra o selo "nao revisado";
  - nenhuma cena compara candidaturas entre si.

TEXTO GRANDE, E NAO E ESTILO. Reels e visto num telefone na mao, muitas vezes em
movimento e quase sempre sem som: o que nao se le em dois segundos nao se le. O
corpo minimo aqui e 46px em 1080 de largura — o dobro do que a arte estatica usa.

USO
    python gerar_reels_uf.py --uf AC
    python gerar_reels_uf.py --uf AC --fps 30 --so-quadros
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import textwrap
import sys

from PIL import Image, ImageDraw

import acervo
from gerar_artes import APAGADO, PAPEL, PAPEL2, SOBRE_ESCURO, TINTA, TINTA2, f
from gerar_artes_analise_uf import ACENTO, CLARO, MEIO, medir
from gerar_artes_candidatura import PALETA, silhueta

RAIZ = pathlib.Path(__file__).resolve().parent
SAIDA = RAIZ / "artes-instagram"
LARG, ALT = 1080, 1920          # 9:16, o vertical do Reels
MARGEM = 88

# A AREA SEGURA E MENOR QUE A TELA, e ignorar isso foi o primeiro erro daqui.
# O Instagram desenha a propria interface por cima do Reels: no alto, o nome do
# perfil e o botao de fechar; embaixo, a legenda, o audio e a coluna de botoes de
# curtir e compartilhar. O rodape estava em ALT-150 — atras dos botoes. Quem
# assistisse nunca veria o endereco do site, que e a unica razao de o video
# existir.
SEGURO_TOPO = 230
SEGURO_BASE = 1560


# --------------------------------------------------------------- utilidades
def suave(x: float) -> float:
    """Aceleracao e desaceleracao. Movimento linear denuncia que e script."""
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def quebra(d: ImageDraw.ImageDraw, txt: str, fonte, larg: int) -> list[str]:
    linhas, atual = [], ""
    for p in txt.split():
        teste = (atual + " " + p).strip()
        if d.textlength(teste, font=fonte) <= larg:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def mistura(c1: str, c2: str, t: float) -> tuple[int, int, int]:
    a = tuple(int(c1[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(c2[i:i + 2], 16) for i in (1, 3, 5))
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


NUMERAL = {0: "nenhuma", 1: "uma", 2: "duas", 3: "três", 4: "quatro", 5: "cinco",
           6: "seis", 7: "sete", 8: "oito", 9: "nove", 10: "dez", 11: "onze",
           12: "doze"}


def num(n: int, fem: bool = True) -> str:
    """Numero escrito. Frase de video se le em voz alta na cabeca de quem ve."""
    if n not in NUMERAL:
        raise SystemExit(f"PAROU: {n} nao esta escrito em NUMERAL. Acrescente a "
                         "palavra em vez de deixar sair o algarismo no meio da frase.")
    p = NUMERAL[n]
    if not fem:
        p = {"uma": "um", "duas": "dois", "nenhuma": "nenhum"}.get(p, p)
    return p


def desenha_uf(img: Image.Image, uf: str, cor: str, caixa, opacidade: int):
    x0, y0, x1, y1 = caixa
    aneis = silhueta(uf)
    xs = [p[0] for a in aneis for p in a]
    ys = [p[1] for a in aneis for p in a]
    esc = min((x1 - x0) / (max(xs) - min(xs)), (y1 - y0) / (max(ys) - min(ys)))
    lg, al = (max(xs) - min(xs)) * esc, (max(ys) - min(ys)) * esc
    ox = x0 + ((x1 - x0) - lg) / 2 - min(xs) * esc
    oy = y0 + ((y1 - y0) - al) / 2 - min(ys) * esc
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(capa)
    rgb = tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))
    for anel in aneis:
        dd.polygon([(ox + x * esc, oy + y * esc) for x, y in anel],
                   fill=rgb + (opacidade,))
    img.alpha_composite(capa)


def rodape(d: ImageDraw.ImageDraw, cor: str):
    """Dentro da area segura, e nao no pe da tela."""
    y = SEGURO_BASE - 92
    d.rectangle([MARGEM, y, LARG - MARGEM, y + 3], fill=cor)
    d.text((MARGEM, y + 26), "kvgs.github.io/senado-2026", font=f("mono", 34), fill=cor)
    fr = f("mono", 30)
    txt = "@CANDIDATURASENADO"
    d.text((LARG - MARGEM - d.textlength(txt, font=fr), y + 30), txt,
           font=fr, fill=APAGADO)


def janela(t: float, inicio: float, dur: float) -> float:
    """Quanto de uma animacao que comeca em `inicio` e dura `dur` ja passou.

    O TEMPO AQUI E EM SEGUNDOS, e nao em fracao da cena. A primeira versao usava
    fracao ((p - 0.30) / 0.45) e o efeito era invisivel no codigo: o titulo da
    cena da barra levava 3,5s para acabar de entrar, e nesse meio as quatro
    linhas ficavam cada uma num alpha diferente. No telefone isso nao lia como
    animacao, lia como um degrade cinza com a ultima linha apagada. Em segundos
    da para dizer a regra: texto de Reels tem de estar legivel em menos de 1s.
    """
    return suave((t - inicio) / max(0.001, dur))


def entra(d: ImageDraw.ImageDraw, txt: str, fonte, cor, x: int, y: int,
          larg: int, t: float, inicio: float = 0.0, entre: float = 1.16,
          dur_linha: float = 0.34, atraso: float = 0.11):
    """Linhas entrando de baixo, uma depois da outra. Devolve o y final.

    Com os valores padrao, um titulo de quatro linhas fecha em 0,67s.
    """
    linhas = quebra(d, txt, fonte, larg)
    passo = int(fonte.size * entre)
    for k, ln in enumerate(linhas):
        p = janela(t, inicio + k * atraso, dur_linha)
        if p <= 0:
            continue
        dy = int((1 - p) * 46)
        alpha = int(255 * p)
        capa = Image.new("RGBA", (LARG, passo + 40), (0, 0, 0, 0))
        ImageDraw.Draw(capa).text((x, 0), ln, font=fonte, fill=cor + (alpha,)
                                  if isinstance(cor, tuple) else cor)
        base = Image.new("RGBA", (LARG, passo + 40), (0, 0, 0, 0))
        base.paste(capa, (0, 0))
        d._image.alpha_composite(Image.blend(
            Image.new("RGBA", base.size, (0, 0, 0, 0)), base, p), (0, y + k * passo + dy))
    return y + len(linhas) * passo


# ------------------------------------------------------------------- cenas
def cena_abre(t: float, dur: float, d: dict, cor: str) -> Image.Image:
    img = Image.new("RGBA", (LARG, ALT), PAPEL2)
    dr = ImageDraw.Draw(img)
    dr._image = img
    desenha_uf(img, d["uf"], cor, (MARGEM, 1010, LARG - MARGEM, 1440),
               opacidade=int(46 * janela(t, 0.2, 1.4)))
    dr.text((MARGEM, 250), f"ELEIÇÕES 2026 · SENADO", font=f("mono", 32), fill=cor)
    # "pelo Acre" vem inteiro do acervo.por_extenso, que ja resolve a
    # concordancia ("por Sao Paulo", "pela Bahia"). A primeira versao ainda
    # colava o nome do estado depois e o video abria com "pelo Acre Acre."
    y = entra(dr, f"{d['candidaturas']} candidaturas ao Senado {d['prep']}.",
              f("display", 104), TINTA, MARGEM, 320, LARG - 2 * MARGEM, t)
    entra(dr, "Você sabe o que elas propõem?", f("display", 104), cor,
          MARGEM, y + 30, LARG - 2 * MARGEM, t, inicio=1.0)
    rodape(dr, cor)
    return img


def cena_contador(t: float, dur: float, d: dict, cor: str) -> Image.Image:
    """De 1 para 20: o contador sobe, e o numero de chegada sai do acervo."""
    img = Image.new("RGBA", (LARG, ALT), PAPEL)
    dr = ImageDraw.Draw(img); dr._image = img
    dec, com = d["declararam_site"], d["com_site"]
    entra(dr, f"{num(dec).capitalize()} candidatura{'s' if dec != 1 else ''} "
              f"declarou site ao TSE." if dec == 1 else
              f"{num(dec).capitalize()} candidaturas declararam site ao TSE.",
          f("display", 82), TINTA2, MARGEM, 280, LARG - 2 * MARGEM, t)
    entra(dr, f"{num(com).capitalize()} {'tinha' if com == 1 else 'tinham'}.",
          f("display", 96), cor, MARGEM, 470, LARG - 2 * MARGEM, t, inicio=0.8)

    passo = janela(t, 1.5, 2.0)
    valor = int(d["proprias_antes"] + (d["proprias"] - d["proprias_antes"]) * passo)
    fnum = f("display", 300)
    if passo > 0:
        w = dr.textlength(str(valor), font=fnum)
        dr.text(((LARG - w) / 2, 700), str(valor), font=fnum, fill=cor)
        fr = f("mono", 38)
        for k, ln in enumerate(("PROPOSTAS DA PRÓPRIA", "CANDIDATURA NO ACERVO")):
            w = dr.textlength(ln, font=fr)
            dr.text(((LARG - w) / 2, 1080 + k * 52), ln, font=fr, fill=TINTA2)
    ach = d["achados"]
    frase = ("O outro site foi encontrado na mão." if ach == 1 else
             f"Os outros {num(ach, fem=False)} sites foram encontrados um a um.")
    entra(dr, f"{frase} Antes disso o acervo tinha {num(d['proprias_antes'])}.",
          f("corpo", 48, 500), TINTA2, MARGEM, 1250, LARG - 2 * MARGEM,
          t, inicio=3.8)
    rodape(dr, cor)
    return img


def cena_barra(t: float, dur: float, d: dict, cor: str) -> Image.Image:
    """A barra empilhada crescendo: 20 da candidatura, 60 do partido, 32 sem."""
    img = Image.new("RGBA", (LARG, ALT), PAPEL)
    dr = ImageDraw.Draw(img); dr._image = img
    # "MENOS DE DUAS" E CONTA, E NAO REDACAO. Sai de A/publicadas: no Acre da
    # 1,79 por dez, e o arredondamento para cima e a palavra honesta. Escrita a
    # mao, esta frase sairia com o numero do Acre no primeiro outro estado.
    por_dez = d["origem"]["A"] / max(1, d["publicadas"]) * 10
    if por_dez >= 5:
        raise SystemExit(
            f"PAROU: {por_dez:.1f} de cada dez informacoes sao da propria "
            "candidatura. A frase desta cena foi escrita para o caso em que a "
            "propria candidatura e minoria; com esse numero a historia e outra e "
            "o texto precisa ser reescrito a mao.")
    inteiro = por_dez == int(por_dez)
    quanto = (num(int(por_dez)) if inteiro
              else "menos de " + num(int(por_dez) + 1))
    entra(dr, f"De cada dez informações publicadas, {quanto} "
              f"{'é' if quanto == 'uma' else 'são'} da própria candidatura.",
          f("display", 76), TINTA, MARGEM, 270, LARG - 2 * MARGEM, t)

    partes = [("Da candidatura", d["origem"]["A"], ACENTO, SOBRE_ESCURO),
              ("Do partido", d["origem"]["B"], MEIO, TINTA),
              ("Sem conteúdo", d["origem"]["D"] + d["origem"]["C"], CLARO, TINTA)]
    total = sum(x[1] for x in partes)
    disponivel = LARG - 2 * MARGEM
    # A BARRA CRESCE COMO UMA SO, DA ESQUERDA PARA A DIREITA.
    #
    # Na primeira versao cada segmento crescia a partir da SUA posicao final, e
    # nos primeiros quadros o video mostrava tres tirinhas soltas com buracos
    # entre elas — nao lia como barra, lia como defeito. Agora existe uma frente
    # que avanca: cada segmento e cortado onde a frente esta.
    cresce = janela(t, 1.0, 1.6)
    y0, alto, gap = 800, 130, 8
    util = disponivel - gap * (len(partes) - 1)
    frente = util * cresce
    x, acumulado = MARGEM, 0.0
    for nome, valor, fundo, tinta in partes:
        cheio = util * valor / total
        w = int(max(0.0, min(cheio, frente - acumulado)))
        if w > 2:
            dr.rectangle([x, y0, x + w, y0 + alto], fill=fundo)
            fv = f("display", 66)
            # O numero so entra quando cabe: rotulo cortado pela propria barra e
            # o defeito que a lista de erros chama pelo nome.
            if dr.textlength(str(valor), font=fv) + 40 < w:
                dr.text((x + 22, y0 + 28), str(valor), font=fv, fill=tinta)
        acumulado += cheio
        x += int(cheio) + gap

    y = y0 + alto + 44
    fr = f("corpo", 42, 500)
    for k, (nome, valor, fundo, _) in enumerate(partes):
        if janela(t, 2.7 + k * 0.22, 0.3) <= 0:
            continue
        dr.rectangle([MARGEM, y + 8, MARGEM + 28, y + 36], fill=fundo)
        # SO O NOME. O numero ja esta escrito dentro do proprio segmento, e
        # escrever duas vezes na mesma tela nao reforca: faz procurar a
        # diferenca entre os dois.
        dr.text((MARGEM + 44, y), nome, font=fr, fill=TINTA2)
        y += 62
    entra(dr, "“Sem conteúdo” é sobre a nossa busca, não sobre a candidatura.",
          f("corpo", 40, 400), APAGADO, MARGEM, y + 26, LARG - 2 * MARGEM,
          t, inicio=3.8)
    rodape(dr, cor)
    return img


def cena_zero(t: float, dur: float, d: dict, cor: str) -> Image.Image:
    img = Image.new("RGBA", (LARG, ALT), PAPEL2)
    dr = ImageDraw.Draw(img); dr._image = img
    zeros = [x["tema"] for x in d["por_tema"] if x["propria"] == 0]
    entra(dr, f"{num(len(zeros), fem=False).capitalize()} tema"
              f"{'' if len(zeros) == 1 else 's'} "
              f"{'não tem' if len(zeros) == 1 else 'não têm'} proposta própria de "
              f"ninguém no estado.",
          f("display", 82), TINTA, MARGEM, 300, LARG - 2 * MARGEM, t)
    y = 700
    for k, nome in enumerate(zeros):
        if janela(t, 1.0 + k * 0.5, 0.35) <= 0:
            continue
        fnum = f("display", 92)
        dr.text((MARGEM, y), "0", font=fnum, fill=cor)
        w = dr.textlength("0", font=fnum)
        # O NOME DO TEMA ENCOLHE ATE CABER, e nao e cortado. "Tecnologia e
        # Inteligencia Artificial" em 52px passava 17px da margem direita —
        # invisivel no olho, visivel na medicao. Cortar em "Artifici" ja
        # aconteceu neste projeto, e e pior: inventa outro nome de tema.
        cabe = LARG - MARGEM - (MARGEM + w + 34)
        for tam in range(52, 33, -2):
            ft = f("corpo", tam, 500)
            if dr.textlength(nome, font=ft) <= cabe:
                break
        else:
            raise SystemExit(f"PAROU: '{nome}' nao cabe na linha nem em 34px.")
        dr.text((MARGEM + w + 34, y + 22 + (52 - tam) // 2), nome, font=ft, fill=TINTA)
        y += 150
    entra(dr, "O que aparece nesses temas vem do programa dos partidos.",
          f("corpo", 44, 400), TINTA2, MARGEM, y + 40, LARG - 2 * MARGEM,
          t, inicio=1.2 + 0.5 * len(zeros))
    rodape(dr, cor)
    return img


def cena_fecha(t: float, dur: float, d: dict, cor: str) -> Image.Image:
    img = Image.new("RGBA", (LARG, ALT), PAPEL2)
    dr = ImageDraw.Draw(img); dr._image = img
    desenha_uf(img, d["uf"], cor, (MARGEM, 1050, LARG - MARGEM, 1440),
               opacidade=int(52 * janela(t, 0.2, 1.6)))
    entra(dr, f"Cada informação com a fonte, o trecho citado e quem conferiu.",
          f("display", 88), TINTA, MARGEM, 300, LARG - 2 * MARGEM, t)
    entra(dr, f"{d['revisadas']} informações do {d['uf_nome']}, conferidas uma a uma.",
          f("corpo", 48, 500), TINTA2, MARGEM, 640, LARG - 2 * MARGEM,
          t, inicio=1.1)
    pl = janela(t, 1.9, 1.2)
    if pl > 0:
        fr = f("mono", 46)
        dr.text((MARGEM, 860), "kvgs.github.io/senado-2026", font=fr,
                fill=mistura(PAPEL2, cor, pl))
        dr.text((MARGEM, 924), "@candidaturasenado", font=fr,
                fill=mistura(PAPEL2, TINTA2, pl))
    # SEM RODAPE AQUI. O endereco e a chamada desta cena, em corpo grande; o
    # rodape o repetia pequeno vinte linhas abaixo, e endereco duas vezes na
    # mesma tela nao reforca, confunde qual dos dois e o clicavel.
    return img


def escreve_legenda(d: dict, cenas: list, saida: pathlib.Path, dur: float) -> None:
    """A legenda sai do mesmo lugar que o vídeo.

    Mesma razão do carrossel de região: escrita à mão, ela ficaria com os números
    de outro estado na primeira cópia-e-cola.
    """
    nome = d["uf_nome"]
    tag = lambda s: "#" + s.lower().replace(" ", "").replace("-", "")
    tags = " ".join([tag("eleições2026"), tag("senado"), tag(nome),
                     tag("dadosabertos"), tag("votoconsciente"),
                     tag("transparência"), tag("jornalismodedados"),
                     tag("política"), tag("brasil")])
    zeros = [x["tema"] for x in d["por_tema"] if x["propria"] == 0]
    # Vírgula decimal. "1.8" é notação de planilha, e a legenda é texto corrido.
    por_dez = f"{d['origem']['A'] / max(1, d['publicadas']) * 10:.1f}".replace(".", ",")
    dec, com, ach = d["declararam_site"], d["com_site"], d["achados"]

    itens = [
        f"▪️ **De cada dez informações publicadas, {por_dez} são da própria "
        f"candidatura** ({d['origem']['A']} de {d['publicadas']}). "
        f"{d['origem']['B']} vêm do programa do partido e "
        f"{d['origem']['C'] + d['origem']['D']} são temas em que não localizamos nada.",

        f"▪️ **{num(dec).capitalize()} candidatura{'' if dec == 1 else 's'} "
        f"{'declarou' if dec == 1 else 'declararam'} site ao TSE. "
        f"{num(com).capitalize()} {'tinha' if com == 1 else 'tinham'}.** "
        f"Os outros {num(ach, fem=False)} foram encontrados um a um — e é de onde "
        f"saíram {d['proprias_de_achado']} das {d['proprias']} propostas próprias "
        f"do estado.",

        f"▪️ **{num(len(zeros), fem=False).capitalize()} "
        f"tema{'' if len(zeros) == 1 else 's'} "
        f"{'não tem' if len(zeros) == 1 else 'não têm'} proposta própria de "
        f"ninguém:** {', '.join(zeros)}. O que aparece ali vem do programa dos "
        f"partidos.",
    ]
    # A quebra de linha aqui e a do TEXTO, e nao a da indentacao do codigo. Sem
    # isto a legenda chega ao Instagram partida no meio das frases, nos pontos em
    # que a f-string virava de linha no fonte.
    bullets = "\n\n".join(textwrap.fill(x, 88) for x in itens)
    abertura = textwrap.fill(
        f"O {nome} é o primeiro estado do site conferido por inteiro: "
        f"{d['revisadas']} informações lidas uma a uma por uma pessoa, cada uma "
        f"com a fonte, o trecho citado e a data.", 88)

    corpo = f"""# Reels — {nome}

Vídeo vertical de {dur:.0f}s, {len(cenas)} cenas, **sem áudio**.
Gerado por `python gerar_reels_uf.py --uf {d["uf"]}`.

---

## Legenda

**{d["candidaturas"]} candidaturas ao Senado {d["prep"]}. Você sabe o que elas propõem?**

{abertura}

{bullets}

**"Sem conteúdo" é sobre a nossa busca, não sobre a candidatura.** Cada uma dessas
linhas diz, no site, onde procuramos e quando.

🔗 kvgs.github.io/senado-2026 — dados abertos, código público.

{tags}

---

## Antes de postar

**O vídeo não tem trilha.** Reels toca sem som por padrão e este script não produz
áudio; a música entra no próprio Instagram, onde ela é licenciada. Trilha colada
aqui seria uso não licenciado.

**A área segura foi respeitada.** O Instagram desenha a própria interface por cima
do Reels — perfil no alto, legenda, áudio e botões embaixo. Tudo o que se lê está
entre {SEGURO_TOPO} e {SEGURO_BASE} de {ALT}.

## Como os números foram apurados

Todos saem do acervo na hora de gerar o vídeo, **e as frases também**: "menos de
duas", "seis tinham", "dois temas" são contas, e não redação. O script para com erro
quando a redação não cabe no dado — por exemplo se a própria candidatura deixar de
ser minoria, porque aí a história é outra e o texto precisa ser reescrito à mão.

O roteiro também muda com o acervo: a cena dos sites achados só existe onde houve
site achado, e a dos temas em zero só existe onde há tema em zero. Cena com o número
zero e a frase de outro estado é o defeito que isto evita.

**A trava do carrossel de análise vale aqui, e mais forte:** só roda para estado
100% revisado. Número animado tem ainda mais cara de fato do que número impresso, e
não mostra o selo "não revisado" que cada linha carrega no site.

## O que se vê em cada cena

"""
    linhas = "\n".join(f"{k + 1}. `{fn.__name__}` — {seg:.1f}s"
                       for k, (fn, seg) in enumerate(cenas))
    (saida / "LEGENDA.md").write_text(corpo + linhas + "\n", encoding="utf-8")


def cenas_para(d: dict) -> list[tuple]:
    """O roteiro depende do que o acervo tem, e nao e uma lista fixa.

    Duas cenas contam uma historia que pode nao existir no estado: a dos sites
    achados fora do registro e a dos temas sem nenhuma proposta propria. Onde a
    historia nao existe, a cena sai — em vez de aparecer com o numero zero e uma
    frase que ficou de outro estado.
    """
    cenas = [(cena_abre, 4.0)]
    if d["achados"] > 0:
        cenas.append((cena_contador, 6.0))
    cenas.append((cena_barra, 7.0))
    zeros = [x for x in d["por_tema"] if x["propria"] == 0]
    if zeros:
        if len(zeros) > 5:
            raise SystemExit(
                f"PAROU: {len(zeros)} temas sem proposta propria nao cabem na "
                "cena, que foi desenhada para uma lista curta. Aqui a lista e a "
                "noticia e cortar em cinco esconderia o resto: a cena precisa "
                "ser redesenhada antes de rodar este estado.")
        cenas.append((cena_zero, 4.0 + 0.5 * len(zeros)))
    cenas.append((cena_fecha, 5.0))
    return cenas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", required=True)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--so-quadros", action="store_true", dest="so_quadros",
                    help="salva alguns PNG para conferir sem gerar o video")
    a = ap.parse_args()
    uf = a.uf.upper()
    if uf not in PALETA:
        raise SystemExit(f"PAROU: {uf} nao tem cor definida em PALETA.")
    cor = PALETA[uf]["cor"]
    d = medir(uf)                        # a trava de estado revisado esta aqui
    d["prep"] = acervo.por_extenso(uf)

    pasta = SAIDA / f"8-{uf.lower()}-reels"
    pasta.mkdir(parents=True, exist_ok=True)
    cenas = cenas_para(d)
    total = sum(dur for _, dur in cenas)
    print(f"{uf}: {len(cenas)} cenas, {total:.0f}s, {a.fps} qps "
          f"({int(total * a.fps)} quadros de {LARG}x{ALT})")

    escreve_legenda(d, cenas, pasta, total)

    if a.so_quadros:
        # Amostra vai para uma subpasta propria, e nao para o lado do MP4: nas
        # pastas de arte o numero do arquivo e a ordem do slide, e dez PNG de
        # conferencia ali dentro leem como se fossem o post.
        conf = pasta / "_quadros"
        conf.mkdir(exist_ok=True)
        for fn, dur in cenas:
            for frac in (0.35, 0.99):
                img = fn(dur * frac, dur, d, cor)
                nome = f"{fn.__name__}-{int(frac*100)}.png"
                img.convert("RGB").save(conf / nome)
                print(f"  _quadros/{nome}")
        return

    saida = pasta / f"reels-{uf.lower()}.mp4"
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{LARG}x{ALT}", "-framerate", str(a.fps), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(saida)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    n = 0
    try:
        for fn, dur in cenas:
            for k in range(int(dur * a.fps)):
                img = fn(k / a.fps, dur, d, cor).convert("RGB")
                proc.stdin.write(img.tobytes())
                n += 1
                if n % 60 == 0:
                    print(f"    {n} quadros", end="\r", flush=True)
        proc.stdin.close()
    except BrokenPipeError:
        pass
    err = proc.stderr.read().decode("utf-8", "replace")
    if proc.wait() != 0:
        raise SystemExit("PAROU: o ffmpeg falhou.\n" + err[-1500:])
    kb = saida.stat().st_size / 1024
    print(f"  {saida.relative_to(RAIZ)}  {n} quadros · {kb/1024:.1f} MB")


if __name__ == "__main__":
    main()
