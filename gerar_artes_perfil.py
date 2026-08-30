# -*- coding: utf-8 -*-
"""Carrossel de quatro artes: quem se candidata ao Senado em 2026.

SO O QUE O REGISTRO NO TSE DIZ. Genero, data de nascimento, escolaridade e
ocupacao sao campos que a propria candidatura preencheu no registro, e e assim
que as artes chamam: "declarou ao TSE". Nao ha aqui nenhuma leitura sobre o que
esses campos significam — a arte mostra a distribuicao e para.

O QUE NAO ENTRA. Nenhuma comparacao com cota de genero: a cota de 30% vale para
eleicao proporcional, e a de senador e majoritaria. Nenhuma frase sobre o que a
escolaridade de alguem indica. Nenhum nome: a unidade e o conjunto das 315.

TODO NUMERO SAI DO ACERVO NA HORA, e a idade e calculada para o DIA DA ELEICAO,
nao para hoje — idade "hoje" muda de valor conforme o dia em que a arte for
gerada, e uma arte publicada nao se corrige.

USO
    python gerar_artes_perfil.py
"""
from __future__ import annotations

import collections
import importlib.util
import pathlib
from datetime import date

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

ELEICAO = date(2026, 10, 4)
FAIXAS = [("35 a 39", 35, 39), ("40 a 49", 40, 49), ("50 a 59", 50, 59),
          ("60 a 69", 60, 69), ("70 a 79", 70, 79), ("80 ou mais", 80, 200)]


def medir() -> dict:
    gen, esc, ocup = collections.Counter(), collections.Counter(), collections.Counter()
    faixa = collections.Counter()
    idades, mandato = [], collections.Counter()
    total = 0
    for e in acervo.ler("estados.json")["estados"]:
        for c in acervo.ler("candidaturas.json", e["uf"])["candidaturas"]:
            total += 1
            p = c["pessoa"]
            gen[p.get("genero")] += 1
            esc[p.get("escolaridade")] += 1
            ocup[p.get("ocupacao_declarada")] += 1
            y, m, d = map(int, p["data_nascimento"].split("-"))
            a = ELEICAO.year - y - ((ELEICAO.month, ELEICAO.day) < (m, d))
            idades.append(a)
            for nome, lo, hi in FAIXAS:
                if lo <= a <= hi:
                    faixa[nome] += 1
                    break
            for x in (c.get("situacao_parlamentar") or []):
                if x.get("situacao") == "Exercício":
                    mandato[x.get("casa")] += 1
    idades.sort()
    return {
        "total": total,
        "mulheres": gen.get("Feminino", 0),
        "homens": gen.get("Masculino", 0),
        "idade_min": idades[0], "idade_max": idades[-1],
        "mediana": idades[len(idades) // 2],
        "faixas": [(n, faixa[n]) for n, _, _ in FAIXAS],
        "escolaridade": esc.most_common(),
        "ocupacoes": ocup.most_common(8),
        "senado": mandato.get("senado", 0),
        "camara": mandato.get("camara", 0),
        "estados": len(acervo.ler("estados.json")["estados"]),
    }


def grade(t: Tela, total: int, cheios: int, y0: int, cols=35, lado=20, gap=5) -> int:
    """A grade de quadradinhos: o conjunto ocupa espaco, em vez de virar um
    numero que se le e esquece. 35 x 9 da exatamente 315."""
    larg = cols * lado + (cols - 1) * gap
    x0 = (L - larg) // 2
    for i in range(total):
        cx = x0 + (i % cols) * (lado + gap)
        cy = y0 + (i // cols) * (lado + gap)
        cheio = i < cheios
        t.d.rectangle([cx, cy, cx + lado, cy + lado],
                      fill=CIANO_FUNDO if cheio else PAPEL,
                      outline=CIANO_FUNDO if cheio else "#CFC7BF")
    return y0 + (-(-total // cols)) * (lado + gap) - gap


def barras(t: Tela, itens, maior, *, fonte_rot, fonte_num, passo, alt=12):
    for rot, n in itens:
        t.d.text((t.m, t.y), rot, font=fonte_rot, fill=TINTA)
        num = str(n)
        larg_n = sum(t.d.textlength(c, font=fonte_num) + 2 for c in num)
        xx = L - t.m - larg_n
        for ch in num:
            t.d.text((xx, t.y + 2), ch, font=fonte_num, fill=TINTA)
            xx += t.d.textlength(ch, font=fonte_num) + 2
        yb = t.y + int(fonte_rot.size * 1.24)
        t.d.rectangle([t.m, yb, L - t.m, yb + alt], fill=PAPEL2)
        larg = int((L - 2 * t.m) * n / maior)
        if larg:
            t.d.rectangle([t.m, yb, t.m + larg, yb + alt], fill=CIANO_FUNDO)
        t.y += passo


# ---------------------------------------------------------------------------
def arte1(d: dict):
    """Capa: o conjunto, e a proporcao de mulheres dentro dele."""
    t = Tela(PAPEL2, 96)
    t.y = 96
    t.mono(f"REGISTRO NO TSE · {d['estados']} ESTADOS · ELEIÇÕES 2026",
           f("mono", 19), CIANO_FUNDO, espacamento=4)
    t.espaco(16)
    t.texto("Quem se candidata ao Senado", f("display", 78), TINTA, entre=1.1, larg=900)
    t.espaco(10)
    t.texto(f"São {d['total']} candidaturas nos {d['estados']} estados. "
            f"Tudo aqui é o que cada uma declarou no próprio registro.",
            f("corpo", 30), TINTA2, entre=1.4, larg=870)
    t.espaco(56)

    # A GRADE E CENTRADA NA FAIXA LIVRE. Encostada no subtitulo, sobrava um
    # buraco de 250px entre a legenda dela e o bloco de baixo — num formato fixo
    # o vazio de um lado so le como pagina cortada.
    alto_grade = 9 * 25 - 5 + 30 + int(f("mono", 18).size * 1.4)
    fim_faixa = t.base_do_rodape() - 60 - int(f("display", 104).size * 1.16)                 - 2 * int(f("corpo", 32).size * 1.4) - 30
    fim = grade(t, d["total"], d["mulheres"],
                t.y + max(0, (fim_faixa - t.y - alto_grade) // 2))
    t.y = fim + 30
    t.mono("CADA QUADRADO É UMA CANDIDATURA", f("mono", 18), APAGADO, espacamento=3)

    base = t.base_do_rodape()
    fnum, frot = f("display", 104), f("corpo", 32)
    t.y = base - 60 - int(fnum.size * 1.16) - 2 * int(frot.size * 1.4) - 30
    t.d.rectangle([t.m, t.y, L - t.m, t.y + 2], fill=CIANO_FUNDO)
    t.espaco(30)
    t.d.text((t.m, t.y), str(d["mulheres"]), font=fnum, fill=CIANO_FUNDO)
    larg_n = t.d.textlength(str(d["mulheres"]), font=fnum)
    t.d.text((t.m + larg_n + 22, t.y + 46),
             f"de {d['total']} declararam o gênero feminino", font=frot, fill=TINTA)
    t.y += int(fnum.size * 1.16)
    t.texto(f"As outras {d['homens']} declararam masculino. São os dois únicos "
            f"valores que a base do TSE traz.", frot, TINTA2, entre=1.4, larg=860)
    t.rodape("kvgs.github.io/senado-2026", "@CANDIDATURASENADO", CIANO_FUNDO, APAGADO)
    t.salvar("perfil-1-quem.png")


def arte2(d: dict):
    """Idade, calculada para o dia da eleicao."""
    t = Tela(PAPEL, 96)
    t.y = 92
    t.mono("IDADE NO DIA DA ELEIÇÃO · 4 DE OUTUBRO DE 2026",
           f("mono", 19), CIANO_FUNDO, espacamento=4)
    t.espaco(14)
    t.texto(f"A pessoa mais nova tem {d['idade_min']}. A mais velha, {d['idade_max']}.",
            f("display", 66), TINTA, entre=1.1, larg=900)
    t.espaco(10)
    t.texto(f"A idade do meio das {d['total']} candidaturas é {d['mediana']} anos. "
            f"A Constituição exige 35 para concorrer ao Senado.",
            f("corpo", 28), TINTA2, entre=1.38, larg=880)
    t.espaco(46)

    fr, fn = f("corpo", 31), f("mono", 31)
    sobra = t.base_do_rodape() - 56 - t.y
    barras(t, d["faixas"], max(n for _, n in d["faixas"]),
           fonte_rot=fr, fonte_num=fn, passo=sobra // len(d["faixas"]))
    t.y = t.base_do_rodape() - 44
    t.mono("QUANTAS CANDIDATURAS EM CADA FAIXA", f("mono", 18), APAGADO, espacamento=3)
    t.rodape("kvgs.github.io/senado-2026", "DADOS ABERTOS · REGISTRO NO TSE",
             CIANO_FUNDO, APAGADO)
    t.salvar("perfil-2-idade.png")


def arte3(d: dict):
    """Escolaridade declarada, a distribuicao inteira."""
    t = Tela(PAPEL, 96)
    t.y = 92
    t.mono("ESCOLARIDADE DECLARADA NO REGISTRO", f("mono", 19), CIANO_FUNDO, espacamento=4)
    t.espaco(14)
    maior_n = d["escolaridade"][0][1]
    t.texto(f"{maior_n} das {d['total']} declararam ensino superior completo",
            f("display", 66), TINTA, entre=1.1, larg=900)
    t.espaco(10)
    t.texto("A base do TSE tem sete níveis. Esta é a distribuição inteira, "
            "sem agrupar nada.", f("corpo", 28), TINTA2, entre=1.38, larg=880)
    t.espaco(46)

    fr, fn = f("corpo", 29), f("mono", 29)
    sobra = t.base_do_rodape() - 56 - t.y
    barras(t, d["escolaridade"], maior_n,
           fonte_rot=fr, fonte_num=fn, passo=sobra // len(d["escolaridade"]))
    t.y = t.base_do_rodape() - 44
    t.mono("CADA CANDIDATURA APARECE UMA VEZ", f("mono", 18), APAGADO, espacamento=3)
    t.rodape("kvgs.github.io/senado-2026", "DADOS ABERTOS · REGISTRO NO TSE",
             CIANO_FUNDO, APAGADO)
    t.salvar("perfil-3-escolaridade.png")


def arte4(d: dict):
    """Ocupacao declarada e quem ja tem cadeira no Congresso."""
    t = Tela(TINTA, 96)
    t.y = 100
    t.mono("OCUPAÇÃO DECLARADA NO REGISTRO", f("mono", 19), CIANO, espacamento=4)
    t.espaco(16)
    t.texto("O que dizem fazer da vida", f("display", 76), PAPEL, entre=1.1, larg=900)
    t.espaco(40)

    fr, fn = f("corpo", 30), f("mono", 30)
    maior = d["ocupacoes"][0][1]
    # O passo sai do espaco que sobra ate o bloco de baixo. Com passo fixo,
    # sobravam 200px de nada entre a ultima barra e a regua.
    fc_alt = int(f("corpo", 34).size * 1.42)
    fim_barras = t.base_do_rodape() - 56 - 2 - 40 - 3 * fc_alt
    passo = (fim_barras - t.y) // len(d["ocupacoes"])
    for rot, n in d["ocupacoes"]:
        t.d.text((t.m, t.y), rot, font=fr, fill=SOBRE_ESCURO)
        num = str(n)
        larg_n = sum(t.d.textlength(c, font=fn) + 2 for c in num)
        xx = L - t.m - larg_n
        for ch in num:
            t.d.text((xx, t.y + 2), ch, font=fn, fill=PAPEL)
            xx += t.d.textlength(ch, font=fn) + 2
        yb = t.y + int(fr.size * 1.24)
        t.d.rectangle([t.m, yb, L - t.m, yb + 11], fill="#221E1B")
        larg = int((L - 2 * t.m) * n / maior)
        if larg:
            t.d.rectangle([t.m, yb, t.m + larg, yb + 11], fill=CIANO)
        t.y += passo

    base = t.base_do_rodape()
    fc = f("corpo", 34)
    frase = (f"E {d['senado'] + d['camara']} das {d['total']} já ocupam uma cadeira no "
             f"Congresso: {d['senado']} são senadores e {d['camara']} são deputados "
             f"federais em exercício.")
    linhas = t.quebra(frase, fc, 860)
    alto = 2 + 40 + len(linhas) * int(fc.size * 1.42)
    t.y = base - 56 - alto
    t.d.rectangle([t.m, t.y, L - t.m, t.y + 2], fill=CIANO)
    t.espaco(40)
    t.texto(frase, fc, PAPEL, entre=1.42, larg=860)
    t.rodape("kvgs.github.io/senado-2026", "@CANDIDATURASENADO", CIANO, APAGADO)
    t.salvar("perfil-4-ocupacao.png")


def main() -> None:
    d = medir()
    print(f"{d['total']} candidaturas · {d['mulheres']} mulheres / {d['homens']} homens")
    print(f"idade na eleicao: {d['idade_min']} a {d['idade_max']}, mediana {d['mediana']}")
    print(f"faixas: {d['faixas']}")
    print(f"escolaridade: {d['escolaridade']}")
    print(f"ocupacoes: {d['ocupacoes']}")
    print(f"em exercicio: senado {d['senado']} · camara {d['camara']}\n")
    arte1(d); arte2(d); arte3(d); arte4(d)


if __name__ == "__main__":
    main()
