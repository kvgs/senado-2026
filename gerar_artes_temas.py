# -*- coding: utf-8 -*-
"""Carrossel de tres artes sobre os TEMAS: de que as candidaturas ao Senado
falam por conta propria, e de que nao falam.

A UNIDADE DE ANALISE E O TEMA, NUNCA A PESSOA. E a mesma regra da pagina de
analise do site: contar por candidatura seria ranquear com outro nome. Uma das
artes diz que so uma candidatura em 315 falou de habitacao — e nao diz qual, de
proposito. O fato interessante e sobre o conjunto, e nomear transformaria um
dado sobre o silencio de 314 num holofote sobre uma.

SO POSICAO PROPRIA (estado A). Programa de partido entra na conta separada, e a
segunda arte existe justamente para mostrar o tamanho da diferenca. Misturar os
dois daria a impressao de que as candidaturas falaram muito, quando quase tudo o
que o acervo tem foi escrito pelo diretorio nacional do partido.

TODO NUMERO SAI DO ACERVO NA HORA. Nenhum e digitado. Se a revisao reprovar uma
posicao, a proxima geracao muda o grafico — numero escrito a mao numa arte que
vai para o Instagram envelhece calado, e la nao da para corrigir depois.

REPROVADO NA REVISAO NAO CONTA. O mesmo filtro do site: posicao com revisao
"remover" ou "corrigir" nao aparece na pagina, entao nao pode aparecer aqui.

USO
    python gerar_artes_temas.py
"""
from __future__ import annotations

import collections
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

# Nome curto so onde o nome inteiro nao cabe em uma linha da arte. O tema
# continua sendo o mesmo do site; o que muda e quantas palavras cabem em 1080px.
CURTO = {
    "Organização do Estado e Prioridades Legislativas": "Organização do Estado",
    "Meio Ambiente e Mudança Climática": "Meio Ambiente e Clima",
    "Infraestrutura e Mobilidade Urbana": "Infraestrutura e Mobilidade",
    "Tecnologia e Inteligência Artificial": "Tecnologia e IA",
    "Cultura e Direitos Humanos": "Cultura e Direitos Humanos",
}


def medir() -> dict:
    ref = acervo.ler("referencia.json")
    nomes = {t["id_tema"]: t["nome"] for t in ref["temas"]}
    proprias, do_partido = collections.Counter(), collections.Counter()
    cands_do_tema = collections.defaultdict(set)
    total_cand = 0
    for e in acervo.ler("estados.json")["estados"]:
        uf = e["uf"]
        total_cand += len(acervo.ler("candidaturas.json", uf)["candidaturas"])
        for p in acervo.ler("posicoes.json", uf)["posicoes"]:
            if (p.get("revisao") or {}).get("resultado") in ("remover", "corrigir"):
                continue
            alvo = (uf, p.get("id_candidatura_contexto") or p.get("atribuido_a_id"))
            if p.get("estado_cobertura") == "A":
                proprias[p["id_tema"]] += 1
                cands_do_tema[p["id_tema"]].add(alvo)
            elif p.get("estado_cobertura") == "B":
                do_partido[p["id_tema"]] += 1
    linhas = [{"nome": nomes[t],
               "curto": CURTO.get(nomes[t], nomes[t]),
               "n": proprias.get(t, 0),
               "cands": len(cands_do_tema[t]),
               "partido": do_partido.get(t, 0)} for t in nomes]
    linhas.sort(key=lambda x: (-x["n"], x["nome"]))
    return {"linhas": linhas,
            "total_proprias": sum(proprias.values()),
            "total_partido": sum(do_partido.values()),
            "total_cand": total_cand,
            "estados": len(acervo.ler("estados.json")["estados"])}


# ---------------------------------------------------------------------------
def arte1(d: dict):
    """O ranking. Barra e o numero ao lado — sem eixo, sem grade: numa arte de
    Instagram a pessoa nao mede, ela compara comprimentos."""
    t = Tela(PAPEL, 96)
    t.y = 92
    t.mono(f"{d['total_cand']} CANDIDATURAS · {d['estados']} ESTADOS · ELEIÇÕES 2026",
           f("mono", 19), CIANO_FUNDO, espacamento=4)
    t.espaco(14)
    t.texto("De que as candidaturas ao Senado falam por conta própria",
            f("display", 62), TINTA, entre=1.1, larg=900)
    t.espaco(8)
    fs = f("corpo", 27)
    t.texto(f"{d['total_proprias']} posições que a própria candidatura declarou, "
            f"em site, entrevista ou documento assinado por ela. Programa de "
            f"partido não entra nesta conta.",
            fs, TINTA2, entre=1.38, larg=880)
    t.espaco(34)

    # ALTURA DA LINHA CALCULADA, e nao escolhida no olho. Sao dez temas num
    # formato fixo: com a linha chutada, os dois ultimos ficaram embaixo da
    # caixa de rodape na primeira versao, e o grafico publicava oito de dez.
    fn, fnum = f("corpo", 29), f("mono", 29)
    sobra = t.base_do_rodape() - 46 - t.y
    passo = sobra // len(d["linhas"])
    alt_barra = 12
    maior = max(x["n"] for x in d["linhas"]) or 1
    for x in d["linhas"]:
        t.d.text((t.m, t.y), x["curto"], font=fn, fill=TINTA)
        num = str(x["n"])
        larg_n = sum(t.d.textlength(c, font=fnum) + 2 for c in num)
        xx = L - t.m - larg_n
        for ch in num:
            t.d.text((xx, t.y + 2), ch, font=fnum, fill=TINTA)
            xx += t.d.textlength(ch, font=fnum) + 2
        yb = t.y + int(fn.size * 1.24)
        # A barra vive num trilho cinza da largura toda: assim o vazio de um tema
        # tem tamanho, e nao vira so uma barra curtinha perdida no branco.
        t.d.rectangle([t.m, yb, L - t.m, yb + alt_barra], fill=PAPEL2)
        larg = int((L - 2 * t.m) * x["n"] / maior)
        if larg:
            t.d.rectangle([t.m, yb, t.m + larg, yb + alt_barra], fill=CIANO_FUNDO)
        t.y += passo

    t.y = t.base_do_rodape() - 40
    t.mono("BARRA CHEIA = 21, O MAIOR NÚMERO DA TABELA", f("mono", 18), APAGADO,
           espacamento=3)
    t.rodape("kvgs.github.io/senado-2026", "DADOS ABERTOS · FONTE EM CADA LINHA",
             CIANO_FUNDO, APAGADO)
    t.salvar("tema-1-ranking.png")


def arte2(d: dict):
    """O contraste. Dois numeros e a razao entre eles, que e a coisa toda."""
    t = Tela(TINTA, 96)
    t.y = 100
    t.mono("QUEM ESTÁ FALANDO", f("mono", 19), CIANO, espacamento=4)
    t.espaco(16)
    t.texto("Quase tudo o que se sabe foi escrito pelo partido, não pela pessoa",
            f("display", 70), PAPEL, entre=1.12, larg=880)
    t.espaco(56)

    fnum, frot, fdesc = f("display", 112), f("mono", 20), f("corpo", 30)
    for n, rotulo, desc, cor in (
        (d["total_proprias"], "DA PRÓPRIA CANDIDATURA",
         "O que a pessoa declarou em site, entrevista ou documento que assinou.", CIANO),
        (d["total_partido"], "DO PROGRAMA DO PARTIDO",
         "O que o diretório nacional escreveu, e vale para todas as candidaturas "
         "da legenda.", SOBRE_ESCURO),
    ):
        t.d.rectangle([t.m, t.y, L - t.m, t.y + 1], fill=LINHA_ESCURA)
        t.y += 40
        t.d.text((t.m, t.y), f"{n:,}".replace(",", "."), font=fnum, fill=cor)
        larg_r = sum(t.d.textlength(c, font=frot) + 2.4 for c in rotulo)
        xx = L - t.m - larg_r
        for ch in rotulo:
            t.d.text((xx, t.y + 46), ch, font=frot, fill=APAGADO)
            xx += t.d.textlength(ch, font=frot) + 2.4
        t.y += int(fnum.size * 1.16) + 6
        t.texto(desc, fdesc, SOBRE_ESCURO, entre=1.4, larg=820)
        t.espaco(44)

    razao = round(d["total_partido"] / max(1, d["total_proprias"]))
    base = t.base_do_rodape()
    fc = f("corpo", 36)
    frase = (f"Para cada frase de uma candidatura, o acervo tem {razao} do programa "
             f"do partido dela. O site separa as duas coisas em toda linha, "
             f"porque não são a mesma coisa.")
    linhas = t.quebra(frase, fc, 860)
    alto = 2 + 44 + len(linhas) * int(fc.size * 1.42)
    t.y = base - 60 - alto
    t.d.rectangle([t.m, t.y, L - t.m, t.y + 2], fill=CIANO)
    t.y += 44
    t.texto(frase, fc, PAPEL, entre=1.42, larg=860)
    t.rodape("kvgs.github.io/senado-2026", "@CANDIDATURASENADO", CIANO, APAGADO)
    t.salvar("tema-2-quem-fala.png")


def arte3(d: dict):
    """O tema mais silencioso, e o convite. O numero grande e a quantidade de
    CANDIDATURAS, e nao de posicoes: "1" diz mais do que "1 posicao"."""
    ultimo = d["linhas"][-1]
    t = Tela(PAPEL2, 96)
    t.y = 100
    t.mono("O TEMA MAIS SILENCIOSO", f("mono", 19), CIANO_FUNDO, espacamento=4)
    t.espaco(16)
    t.texto(f"{ultimo['cands']} de {d['total_cand']} candidaturas disseram algo "
            f"sobre {ultimo['nome'].lower()}",
            f("display", 76), TINTA, entre=1.1, larg=880)
    t.espaco(48)

    # A grade de 315 quadradinhos: o silencio ocupa espaco, em vez de ser um
    # numero que se le e esquece. 35 x 9 da exatamente 315 — sem sobra na ultima
    # linha, que seria lida como "faltou alguem".
    cols, lado, gap = 35, 20, 5
    linhas_g = -(-d["total_cand"] // cols)
    larg_total = cols * lado + (cols - 1) * gap
    x0 = (L - larg_total) // 2
    # 315 nao se fatora num retangulo com a proporcao que eu queria: 35x9 fica
    # baixo demais e 21x15 alto demais. Entao a grade e CENTRADA na faixa que
    # sobra entre o titulo e o bloco de baixo, em vez de encostada no titulo —
    # assim o vazio vira margem dos dois lados, e nao um buraco de um lado so.
    alto_grade = linhas_g * (lado + gap) - gap + 26 + int(f("mono", 18).size * 1.4)
    faixa_ate = A - 96 - (3 + 34 + 31) - 48 - 200 - 52 - 88 - 30
    y0 = t.y + max(0, (faixa_ate - t.y - alto_grade) // 2)
    t.y = y0
    for i in range(d["total_cand"]):
        cx = x0 + (i % cols) * (lado + gap)
        cy = y0 + (i // cols) * (lado + gap)
        cheio = i < ultimo["cands"]
        # A borda do quadrado vazio precisa ser mais escura que a do site: aqui o
        # fundo ja e PAPEL2, e a linha clara sumia contra ele.
        t.d.rectangle([cx, cy, cx + lado, cy + lado],
                      fill=CIANO_FUNDO if cheio else PAPEL,
                      outline=CIANO_FUNDO if cheio else "#CFC7BF")
    t.y = y0 + linhas_g * (lado + gap) + 26
    t.mono("CADA QUADRADO É UMA CANDIDATURA AO SENADO", f("mono", 18), APAGADO,
           espacamento=3)

    # OS DOIS BLOCOS DE BAIXO SAO ANCORADOS NO PE, e nao empilhados a partir da
    # grade. Empilhados, sobrava um buraco de 130px entre eles — num formato fixo
    # o vazio no meio le como pagina cortada, e nao como respiro.
    base = t.base_do_rodape()
    fc = f("corpo", 32)
    frase = ("O site não diz que elas são contra nem a favor. Diz que não achamos "
             "nada — e mostra onde procuramos. Achou uma fonte que falta? Escreva.")
    linhas = t.quebra(frase, fc, 830)
    alto = 32 + len(linhas) * int(fc.size * 1.45) + 32
    topo_caixa = base - 48 - alto

    # O contraste no MESMO tema, que e o que explica o silencio: nao e que o
    # assunto nao esteja no acervo — e que quem escreveu foi o partido.
    fd = f("corpo", 32)
    contraste = (f"No mesmo tema o acervo tem {ultimo['partido']} propostas — todas do "
                 f"programa do partido, nenhuma escrita pela candidatura.")
    n_c = len(t.quebra(contraste, fd, 860))
    t.y = topo_caixa - 52 - n_c * int(fd.size * 1.4) - 30
    t.d.rectangle([t.m, t.y, L - t.m, t.y + 2], fill=CIANO_FUNDO)
    t.espaco(30)
    t.texto(contraste, fd, TINTA, entre=1.4, larg=860)

    t.y = topo_caixa
    t.d.rounded_rectangle([t.m, t.y, L - t.m, t.y + alto], 14, fill=TINTA)
    yy = t.y + 34
    for ln in linhas:
        t.d.text((t.m + 38, yy), ln, font=fc, fill=SOBRE_ESCURO)
        yy += int(fc.size * 1.45)
    t.rodape("contato.candidaturasenado@gmail.com", "@CANDIDATURASENADO",
             CIANO_FUNDO, APAGADO)
    t.salvar("tema-3-silencio.png")


def main() -> None:
    d = medir()
    print(f"medido do acervo: {d['total_proprias']} posicoes proprias, "
          f"{d['total_partido']} de partido, {d['total_cand']} candidaturas")
    for x in d["linhas"]:
        print(f"  {x['curto'][:30]:30} {x['n']:3} propria(s) · {x['cands']:3} candidatura(s)"
              f" · {x['partido']:5} de partido")
    print()
    arte1(d)
    arte2(d)
    arte3(d)


if __name__ == "__main__":
    main()
