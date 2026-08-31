# -*- coding: utf-8 -*-
"""Carrossel de quatro artes: por que em 2026 sao DOIS votos para senador.

O QUE ESTA AQUI NAO SAI DO ACERVO, e sim da Constituicao — e por isso a arte
mostra o artigo. Art. 46: o Senado e eleito pelo principio majoritario; cada
estado elege TRES senadores com mandato de OITO anos (§1º); e a representacao de
cada estado se renova de quatro em quatro anos, ALTERNADAMENTE, por um e dois
tercos (§2º). Dai 2022 ter sido um voto e 2026 serem dois.

O QUE NAO ENTRA: nenhuma frase sobre o que o eleitor sabe ou deixa de saber.
"Muita gente descobre na urna" seria uma afirmacao sobre pessoas que eu nao medi.
A arte diz a regra e para.

DO ACERVO vem so o que e do acervo: o numero de estados e o de candidaturas.

USO
    python gerar_artes_dois_votos.py
"""
from __future__ import annotations

import importlib.util
import pathlib

import acervo

_spec = importlib.util.spec_from_file_location(
    "artes", pathlib.Path(__file__).resolve().parent / "gerar_artes.py")
_ar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ar)

Tela, f, L, A = _ar.Tela, _ar.f, _ar.L, _ar.A
TINTA, TINTA2 = _ar.TINTA, _ar.TINTA2
PAPEL, PAPEL2, LINHA = _ar.PAPEL, _ar.PAPEL2, _ar.LINHA
CIANO, CIANO_FUNDO = _ar.CIANO, _ar.CIANO_FUNDO
SOBRE_ESCURO, APAGADO, LINHA_ESCURA = _ar.SOBRE_ESCURO, _ar.APAGADO, _ar.LINHA_ESCURA

FONTE_LEI = "CONSTITUIÇÃO, ART. 46, §1º E §2º"


def medir() -> dict:
    est = acervo.ler("estados.json")["estados"]
    total = sum(len(acervo.ler("candidaturas.json", e["uf"])["candidaturas"])
                for e in est)
    return {"estados": len(est), "candidaturas": total}


# ---------------------------------------------------------------------------
def arte1():
    """O gancho. Um numero grande e a frase mais curta que diz o fato."""
    t = Tela(TINTA, 96)
    t.y = 118
    t.mono("ELEIÇÕES 2026 · SENADO FEDERAL", f("mono", 20), CIANO, espacamento=4)
    t.espaco(30)
    t.texto("Este ano você vota em", f("display", 62), SOBRE_ESCURO, entre=1.1, larg=900)
    t.espaco(6)

    # O "2" ocupa o lugar de uma imagem: e o assunto inteiro do carrossel. E o
    # bloco e CENTRADO na faixa que sobra ate a frase de baixo — encostado no
    # titulo, sobravam 380px de nada, que num formato fixo le como corte.
    fg = f("display", 400)
    fc0 = f("corpo", 40)
    fim_faixa = t.base_do_rodape() - 70 - 2 - 46 - 2 * int(fc0.size * 1.4)
    t.y += max(0, (fim_faixa - t.y - int(fg.size * 0.92)) // 2)
    t.d.text((t.m - 14, t.y), "2", font=fg, fill=CIANO)
    larg2 = t.d.textlength("2", font=fg)
    t.d.text((t.m + larg2 + 18, t.y + 190), "senadores",
             font=f("display", 96), fill=PAPEL)
    t.y += int(fg.size * 0.92)

    base = t.base_do_rodape()
    fc = f("corpo", 40)
    frase = "Em 2022 foi um. Em 2030 será um de novo. Este ano são dois — e há um motivo."
    linhas = t.quebra(frase, fc, 850)
    alto = 2 + 46 + len(linhas) * int(fc.size * 1.4)
    t.y = base - 70 - alto
    t.d.rectangle([t.m, t.y, L - t.m, t.y + 2], fill=CIANO)
    t.espaco(46)
    t.texto(frase, fc, PAPEL, entre=1.4, larg=850)
    t.rodape("kvgs.github.io/senado-2026", "ARRASTA PARA O LADO", CIANO, APAGADO)
    t.salvar("votos-1-gancho.png")


def arte2():
    """As tres cadeiras de cada estado, duas em jogo."""
    t = Tela(PAPEL, 96)
    t.y = 96
    t.mono("POR QUE DOIS", f("mono", 20), CIANO_FUNDO, espacamento=4)
    t.espaco(16)
    t.texto("Cada estado tem três senadores — e eles não são trocados juntos",
            f("display", 64), TINTA, entre=1.1, larg=900)
    t.espaco(14)
    t.texto("O mandato dura oito anos, o dobro do de presidente e deputado. "
            "Para o Senado não parar inteiro de quatro em quatro anos, a troca "
            "é feita em pedaços.",
            f("corpo", 29), TINTA2, entre=1.4, larg=880)
    t.espaco(52)

    # Tres cadeiras, duas acesas. Forma simples: o leitor conta sem legenda.
    lado, gap = 190, 34
    x0 = (L - (3 * lado + 2 * gap)) // 2
    # Mesma conta da arte 1: o bloco fica no meio da faixa livre.
    fc0 = f("corpo", 34)
    fim_faixa = t.base_do_rodape() - 56 - 30 - 3 * int(fc0.size * 1.45) - 30
    alto_bloco = lado + 28 + int(f("mono", 18).size * 1.4)
    y0 = t.y + max(0, (fim_faixa - t.y - alto_bloco) // 2)
    for i in range(3):
        x = x0 + i * (lado + gap)
        emjogo = i < 2
        t.d.rounded_rectangle([x, y0, x + lado, y0 + lado], 16,
                              fill=CIANO_FUNDO if emjogo else PAPEL2,
                              outline=CIANO_FUNDO if emjogo else "#D8D0C8", width=2)
        rot = "EM JOGO" if emjogo else "SÓ EM 2030"
        fr = f("mono", 17)
        larg_r = sum(t.d.textlength(c, font=fr) + 2 for c in rot)
        xx = x + (lado - larg_r) // 2
        for ch in rot:
            t.d.text((xx, y0 + lado // 2 - 10), ch, font=fr,
                     fill=PAPEL if emjogo else APAGADO)
            xx += t.d.textlength(ch, font=fr) + 2
    t.y = y0 + lado + 28
    t.mono("AS TRÊS CADEIRAS DE UM ESTADO, EM 2026", f("mono", 18), APAGADO, espacamento=3)

    base = t.base_do_rodape()
    fc = f("corpo", 34)
    frase = ("Duas das três cadeiras estão em disputa agora. Como são duas vagas, "
             "a urna pede o voto para senador duas vezes.")
    linhas = t.quebra(frase, fc, 850)
    alto = 30 + len(linhas) * int(fc.size * 1.45) + 30
    t.y = base - 56 - alto
    t.d.rounded_rectangle([t.m, t.y, L - t.m, t.y + alto], 14, fill=TINTA)
    yy = t.y + 30
    for ln in linhas:
        t.d.text((t.m + 38, yy), ln, font=fc, fill=SOBRE_ESCURO)
        yy += int(fc.size * 1.45)
    t.rodape("kvgs.github.io/senado-2026", FONTE_LEI, CIANO_FUNDO, APAGADO)
    t.salvar("votos-2-por-que.png")


def arte3():
    """A alternancia, ano a ano. E a linha do tempo que explica tudo."""
    t = Tela(PAPEL2, 96)
    t.y = 96
    t.mono("A CADA QUATRO ANOS, ALTERNADAMENTE", f("mono", 20), CIANO_FUNDO, espacamento=4)
    t.espaco(16)
    t.texto("Um ano você vota em um. No outro, em dois.",
            f("display", 66), TINTA, entre=1.1, larg=900)
    t.espaco(46)

    anos = [("2018", 2, False), ("2022", 1, False), ("2026", 2, True),
            ("2030", 1, False), ("2034", 2, False)]
    fa, fv = f("display", 46), f("corpo", 30)
    sobra = t.base_do_rodape() - 70 - t.y
    passo = sobra // len(anos)
    for ano, votos, agora in anos:
        cor = CIANO_FUNDO if agora else TINTA2
        t.d.text((t.m, t.y), ano, font=fa, fill=cor)
        # As bolinhas dizem quantos votos: contar e mais rapido que ler.
        cx = t.m + 210
        for i in range(votos):
            r = 19
            t.d.ellipse([cx, t.y + 8, cx + 2 * r, t.y + 8 + 2 * r],
                        fill=cor if agora else "#C9C1B9",
                        outline=cor if agora else "#C9C1B9")
            cx += 2 * r + 14
        rot = f"{votos} voto" + ("s" if votos > 1 else "")
        if agora:
            rot += " — é este"
        t.d.text((t.m + 210 + votos * 52 + 26, t.y + 12), rot, font=fv,
                 fill=TINTA if agora else APAGADO)
        t.y += passo
        if ano != anos[-1][0]:
            t.d.rectangle([t.m, t.y - passo // 2 + 26, L - t.m,
                           t.y - passo // 2 + 27], fill="#E3DCD5")

    t.y = t.base_do_rodape() - 56
    t.mono("CADA BOLA É UM VOTO PARA SENADOR", f("mono", 18), APAGADO, espacamento=3)
    t.rodape("kvgs.github.io/senado-2026", FONTE_LEI, CIANO_FUNDO, APAGADO)
    t.salvar("votos-3-alternancia.png")


def arte4(d: dict):
    """O que fazer com a informacao, e o convite."""
    t = Tela(PAPEL, 96)
    t.y = 96
    t.mono("NA HORA DE VOTAR", f("mono", 20), CIANO_FUNDO, espacamento=4)
    t.espaco(16)
    t.texto("O que muda com dois votos", f("display", 74), TINTA, entre=1.1, larg=900)
    t.espaco(44)

    fh, fp = f("corpo", 33), f("corpo", 28)
    itens = [
        ("A urna pede senador duas vezes",
         "São dois nomes diferentes, um em cada vez."),
        ("Os dois mais votados são eleitos",
         "Não há segundo turno para o Senado."),
        ("Você não é obrigada a usar os dois",
         "Dá para votar em um e deixar o outro em branco ou nulo."),
        ("O mandato vai até 2035",
         "Oito anos — o dobro do de presidente, governador e deputado."),
    ]
    fc0 = f("corpo", 31)
    fim_itens = t.base_do_rodape() - 52 - 30 - 3 * int(fc0.size * 1.45) - 30
    respiro = max(26, (fim_itens - t.y - len(itens) * 96) // (2 * len(itens)))
    for i, (titulo, desc) in enumerate(itens):
        if i:
            t.d.rectangle([t.m, t.y, L - t.m, t.y], fill=LINHA)
            t.espaco(respiro)
        t.d.rectangle([t.m, t.y + 6, t.m + 5, t.y + 40], fill=CIANO_FUNDO)
        t.texto(titulo, fh, TINTA, entre=1.3, larg=830, x=t.m + 26)
        t.texto(desc, fp, TINTA2, entre=1.4, larg=830, x=t.m + 26)
        t.espaco(respiro)

    base = t.base_do_rodape()
    fc = f("corpo", 31)
    frase = (f"São {d['candidaturas']} candidaturas nos {d['estados']} estados. "
             f"O que cada uma defende, tema por tema e com a fonte ao lado, "
             f"está no site.")
    linhas = t.quebra(frase, fc, 830)
    alto = 30 + len(linhas) * int(fc.size * 1.45) + 30
    t.y = base - 52 - alto
    t.d.rounded_rectangle([t.m, t.y, L - t.m, t.y + alto], 14, fill=TINTA)
    yy = t.y + 30
    for ln in linhas:
        t.d.text((t.m + 38, yy), ln, font=fc, fill=SOBRE_ESCURO)
        yy += int(fc.size * 1.45)
    t.rodape("kvgs.github.io/senado-2026", "@CANDIDATURASENADO", CIANO_FUNDO, APAGADO)
    t.salvar("votos-4-na-urna.png")


def main() -> None:
    d = medir()
    print(f"do acervo: {d['candidaturas']} candidaturas em {d['estados']} estados")
    print(f"da Constituicao: 3 senadores por estado, mandato de 8 anos,")
    print(f"                 renovacao alternada de 1/3 e 2/3 ({FONTE_LEI})\n")
    arte1(); arte2(); arte3(); arte4(d)


if __name__ == "__main__":
    main()
