# -*- coding: utf-8 -*-
"""Carrossel de analise de dados de um estado inteiro, medido do acervo.

SO PODE EXISTIR PARA ESTADO 100% REVISADO. Um grafico e uma afirmacao com cara de
fato: ele nao mostra o selo "nao revisado" que cada linha carrega no site. Publicar
grafico de acervo por revisar seria dar forca de medicao ao que ainda e rascunho.
O script PARA se houver linha pendente.

O QUE ESTE CARROSSEL NAO FAZ, E E A REGRA MAIS IMPORTANTE DELE. Nenhum grafico
compara candidaturas entre si. Contar propostas por pessoa e ordena-las e um ranking
— e o que ele mediria nao e qualidade de candidatura, e sim verba de campanha e
tamanho de assessoria. O proprio validar.py do projeto avisa sobre isso. Todos os
recortes aqui sao por TEMA, por ORIGEM da informacao e sobre a NOSSA busca.

AS FORMAS FORAM ESCOLHIDAS ANTES DA COR, e cada uma tem UMA serie:
  - de onde vem o que esta publicado -> uma barra empilhada, parte-do-todo, tres
    segmentos rotulados;
  - proposta propria por tema -> barras, uma cor so. Colorir cada barra mais escura
    conforme o valor seria rampa em categoria nominal, que duplica o comprimento na
    cor e nao acrescenta nada;
  - os sites -> numero, e nao grafico. Barra unica de um valor e pior que o numero.

A COR FOI MEDIDA, e nao escolhida no olho. Verde do Acre (#0B5D2A, 7,3:1 sobre o
papel) para o que e da propria candidatura; cinza medio (#8C8279, 3,4:1) para o que
e do partido; cinza claro para a ausencia. O primeiro par testado — verde #007A2E
com cinza #6B6560 — foi descartado: 1,05:1 entre eles, ou seja, a mesma barra para
quem nao distingue cor. O que separa os segmentos aqui e LUMINANCIA e rotulo
direto, que sobrevivem a daltonismo e a impressao em preto e branco.

USO
    python gerar_artes_analise_uf.py --uf AC
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib

import acervo
import gerar_artes as _ar
from gerar_artes import (A, APAGADO, L, LINHA, PAPEL, PAPEL2, SOBRE_ESCURO, TINTA,
                         TINTA2, Tela, f)
from gerar_artes_candidatura import PALETA, desenha_silhueta, slug

RAIZ = pathlib.Path(__file__).resolve().parent

# Luminancia crescente: escuro = da candidatura, medio = do partido, claro = ausencia.
# A ordem e a mesma em todos os graficos, e e o que o leitor aprende no primeiro.
NUM_EXTENSO = {0: "nenhuma", 1: "uma", 2: "duas", 3: "três", 4: "quatro",
               5: "cinco", 6: "seis", 7: "sete", 8: "oito", 9: "nove",
               10: "dez", 11: "onze", 12: "doze", 13: "treze", 14: "catorze",
               15: "quinze", 16: "dezesseis", 17: "dezessete", 18: "dezoito",
               19: "dezenove", 20: "vinte"}


def num_extenso(n: int, fem: bool = True) -> str:
    """Numero por extenso na frase, algarismo no grafico.

    Frase de arte se le em voz alta; grafico se le com o olho. O numero escrito
    aqui entra em texto corrido, e por isso vai por extenso — mas se for grande
    demais para a tabela, o algarismo e melhor que um palpite.

    O GENERO E PARAMETRO porque a tabela nasceu para "candidaturas" e a primeira
    frase masculina que a usou saiu "de DUAS estados".
    """
    p = NUM_EXTENSO.get(n, str(n))
    if not fem:
        p = {"uma": "um", "duas": "dois", "nenhuma": "nenhum"}.get(p, p)
    return p


# A COR DA SERIE E A DO ESTADO, e nao uma so para todos. Este numero continua
# aqui porque outros scripts o importam e porque e o padrao de quem nao passa cor,
# mas as artes usam PALETA[uf], a mesma do carrossel por candidatura. Sem isso, a
# analise do Amapa saia no verde do Acre: dois estados com a mesma cara no feed,
# que e exatamente o que a paleta existe para evitar.
#
# Medido antes de trocar: o azul do Amapa (#00548C) da 7,93:1 sobre o papel e
# 6,59:1 para o rotulo claro dentro da barra, contra 8,04:1 e 6,67:1 do verde do
# Acre. Nenhuma das duas separa por cor do cinza medio (2,1:1), e por isso o que
# separa os segmentos continua sendo luminancia e rotulo escrito.
ACENTO = "#0B5D2A"      # 7,33:1 sobre o papel — padrao, quando nao ha cor de UF
MEIO = "#8C8279"        # 3,43:1
CLARO = "#DDD6CF"       # 1,31:1 — abaixo de 3:1, e por isso SEMPRE com rotulo visivel
GAP = 6                 # folga em cor de papel entre segmentos que se tocam


def medir(uf: str) -> dict:
    pos_todas = acervo.ler("posicoes.json", uf)["posicoes"]
    pendentes = [p for p in pos_todas
                 if not p.get("revisado_por_humano")
                 and not (p.get("revisao") or {}).get("resultado")]
    if pendentes:
        raise SystemExit(
            f"PAROU: {uf} tem {len(pendentes)} linha(s) sem decisao da revisao. "
            "Grafico tem cara de fato e nao mostra o selo 'nao revisado' que cada "
            "linha carrega no site — publicar numero de acervo por revisar seria "
            "dar forca de medicao ao que ainda e rascunho.")

    pos = [p for p in pos_todas
           if (p.get("revisao") or {}).get("resultado") not in ("remover", "corrigir")]
    cands = acervo.ler("candidaturas.json", uf)["candidaturas"]
    ref = acervo.ler("referencia.json")
    temas = [t for t in ref["temas"] if "senador" in t.get("aplicavel_a_cargos", [])]
    est = next(e for e in acervo.ler("estados.json")["estados"] if e["uf"] == uf)

    def de(p):
        return p.get("id_candidatura_contexto") or p.get("atribuido_a_id")

    # Por tema: em quantas candidaturas ha proposta PROPRIA. E uma contagem de
    # cruzamentos, e nao de pessoas — nenhuma candidatura aparece nomeada.
    por_tema = []
    for t in temas:
        propria = len({de(p) for p in pos
                       if p["id_tema"] == t["id_tema"] and p["estado_cobertura"] == "A"})
        partido = len({de(p) for p in pos
                       if p["id_tema"] == t["id_tema"] and p["estado_cobertura"] == "B"})
        por_tema.append({"tema": t["nome"], "propria": propria, "partido": partido})

    fora = json.loads((RAIZ / "dados" / "sites-fora-do-registro.json")
                      .read_text(encoding="utf-8"))["sites"]
    achados = [x for x in fora if x["uf"] == uf]
    declararam_site = [c for c in cands
                       if any(not any(r in u.lower() for r in
                                      ("instagram", "facebook", "twitter", "x.com",
                                       "youtube", "tiktok", "kwai", "wa.me"))
                              for u in (c.get("contato") or {}).get("redes") or [])]
    # A CONTA DO "ANTES" TEM DE SEPARAR SITE DECLARADO DE SITE ACHADO. Escrita
    # como "proprias menos as que vieram de site", ela dava ZERO — e teria
    # publicado que o acervo nao tinha nenhuma proposta propria antes da busca.
    # Falso: uma candidatura DECLAROU o site ao TSE, e a proposta dela o coletor
    # acharia de qualquer jeito. O "antes" e o que vem de fonte declarada.
    ids_achados = {x["id_candidatura"] for x in achados}
    proprias = [p for p in pos if p["estado_cobertura"] == "A"]
    proprias_de_site = [p for p in proprias
                        if (p.get("id_documento") or "").startswith("doc-site-")]
    proprias_de_achado = [p for p in proprias_de_site
                          if (p.get("id_candidatura_contexto")
                              or p.get("atribuido_a_id")) in ids_achados]

    return {
        "uf": uf, "uf_nome": est["nome"],
        "candidaturas": len(cands), "temas": len(temas),
        "linhas": len(pos_todas),
        "publicadas": len(pos),
        "revisadas": sum(1 for p in pos if p.get("revisado_por_humano")),
        "retiradas": len(pos_todas) - len(pos),
        "origem": collections.Counter(p["estado_cobertura"] for p in pos),
        "por_tema": por_tema,
        "com_site": len(achados) + len(declararam_site),
        "declararam_site": len(declararam_site),
        "achados": len(achados),
        "proprias": len(proprias),
        "proprias_de_site": len(proprias_de_site),
        "proprias_de_achado": len(proprias_de_achado),
        "proprias_antes": len(proprias) - len(proprias_de_achado),
    }


# ------------------------------------------------------------------- desenho
def cabecalho(t: Tela, d: dict, cor: str, olho: str):
    t.y = 92
    t.mono(f"ELEIÇÕES 2026 · SENADO · {d['uf_nome'].upper()}", f("mono", 19),
           cor, espacamento=4)
    t.espaco(14)
    t.mono(olho, f("mono", 19), APAGADO, espacamento=3)
    t.espaco(16)


def legenda(t: Tela, itens: list[tuple[str, str]]):
    """Cor + nome, sempre presente quando ha mais de uma serie."""
    fr = f("corpo", 24, 500)
    x = t.m
    for cor, nome in itens:
        t.d.rectangle([x, t.y + 6, x + 20, t.y + 24], fill=cor)
        t.d.text((x + 30, t.y), nome, font=fr, fill=TINTA2)
        x += 30 + t.d.textlength(nome, font=fr) + 40
    t.y += 40


ORDINAL = {1: "O PRIMEIRO", 2: "O SEGUNDO", 3: "O TERCEIRO", 4: "O QUARTO",
           5: "O QUINTO", 6: "O SEXTO", 7: "O SÉTIMO", 8: "O OITAVO",
           9: "O NONO", 10: "O DÉCIMO"}


def chapeu_da_ordem(d: dict) -> str:
    """Em que posicao ESTE estado ficou pronto, pela DATA e nao pelo alfabeto.

    Estado conferido por inteiro e aquele em que toda posicao publicavel passou
    pela revisao humana. A ordem entre eles sai da data da ULTIMA revisao de cada
    um — que e o dia em que ele ficou pronto. A primeira versao disto ordenava
    pela ordem em que os estados aparecem no acervo, que e alfabetica: para AC e
    AP dava certo por coincidencia, e afirmaria "o segundo" sem saber.

    A conta e feita na hora. Lista escrita a mao envelhece no dia em que o
    proximo estado fica pronto — foi assim que "O PRIMEIRO ESTADO CONFERIDO POR
    INTEIRO", escrito para o Acre, saiu tambem na capa do Amapa.
    """
    prontos = []
    for uf in acervo.com_acervo():
        pos = [p for p in acervo.ler("posicoes.json", uf)["posicoes"]
               if (p.get("revisao") or {}).get("resultado") not in ("remover", "corrigir")]
        if not pos or not all(p.get("revisado_por_humano") for p in pos):
            continue
        datas = [(p.get("revisao") or {}).get("em") or "" for p in pos]
        prontos.append((max(datas), uf))
    prontos.sort()
    ufs = [uf for _, uf in prontos]
    if d["uf"] not in ufs:
        return "ESTADO CONFERIDO POR INTEIRO"
    if len(ufs) == 1:
        return "O PRIMEIRO ESTADO CONFERIDO POR INTEIRO"
    ord_ = ORDINAL.get(ufs.index(d["uf"]) + 1)
    if not ord_:
        return f"UM DOS {len(ufs)} ESTADOS CONFERIDOS POR INTEIRO"
    return f"{ord_} DE {len(ufs)} ESTADOS CONFERIDOS POR INTEIRO"


ORDINAL_PROSA = {1: "o primeiro", 2: "o segundo", 3: "o terceiro",
                 4: "o quarto", 5: "o quinto", 6: "o sexto", 7: "o sétimo",
                 8: "o oitavo", 9: "o nono", 10: "o décimo"}


def ordem_em_prosa(d: dict) -> str:
    """A mesma posicao do chapeu, mas escrita para caber numa frase.

    O chapeu vai em CAIXA ALTA e sem artigo, o que serve na tarja e nao serve no
    meio de um paragrafo: "O Amapa e PRIMEIRO DE 2 ESTADOS" nao e portugues. Duas
    formas para o mesmo dado, cada uma escrita para o lugar onde e lida.
    """
    chapeu = chapeu_da_ordem(d)
    if chapeu == "ESTADO CONFERIDO POR INTEIRO":
        return "um estado do site conferido por inteiro"
    if chapeu == "O PRIMEIRO ESTADO CONFERIDO POR INTEIRO":
        return "o primeiro estado do site conferido por inteiro"
    prontos = chapeu.split(" DE ")[1].split()[0]
    ordinal = ORDINAL_PROSA.get(
        [k for k, v in ORDINAL.items() if chapeu.startswith(v + " ")][0]
        if any(chapeu.startswith(v + " ") for v in ORDINAL.values()) else 0,
        "um")
    return (f"{ordinal} de {num_extenso(int(prontos), fem=False)} estados do site "
            "conferidos por inteiro")


def arte_capa(d: dict, cor: str, i: int, n: int):
    t = Tela(PAPEL2, 96)
    # "O PRIMEIRO" ERA VERDADE UMA VEZ SO. A frase foi escrita para o Acre e
    # ficou chumbada: o Amapa saiu com ela tambem, dizendo que era o primeiro
    # estado conferido por inteiro quando era o segundo. O chapeu agora sai da
    # ordem em que os estados FICARAM prontos, contada no acervo.
    cabecalho(t, d, cor, chapeu_da_ordem(d))
    t.texto(f"O que o acervo do {d['uf_nome']} mostra",
            f("display", 78), TINTA, entre=1.06, larg=880)
    t.espaco(24)
    t.texto(f"{d['candidaturas']} candidaturas, {d['temas']} temas. Cada informação "
            "publicada foi lida por uma pessoa, uma a uma.",
            f("corpo", 33, 400), TINTA2, entre=1.4, larg=860)

    # Numero heroi: e a resposta principal, e barra de um valor so seria pior.
    t.espaco(56)
    fnum = f("display", 190)
    t.d.text((t.m, t.y), str(d["revisadas"]), font=fnum, fill=cor)
    larg = t.d.textlength(str(d["revisadas"]), font=fnum)
    t.d.text((t.m + larg + 26, t.y + 84), "INFORMAÇÕES", font=f("mono", 28), fill=TINTA2)
    t.d.text((t.m + larg + 26, t.y + 124), "CONFERIDAS POR GENTE", font=f("mono", 28),
             fill=TINTA2)
    t.y += int(fnum.size * 0.92)
    t.espaco(18)
    r = d["retiradas"]
    if r:
        retirada = (f"Outra {r} foi retirada na revisão." if r == 1
                    else f"Outras {r} foram retiradas na revisão.")
    else:
        retirada = "Nenhuma foi retirada na revisão."
    t.texto(f"De {d['publicadas']} publicadas. {retirada}",
            f("corpo", 28, 400), APAGADO, entre=1.36, larg=840)

    livre = t.base_do_rodape() - 30 - (t.y + 30)
    if livre > 150:
        desenha_silhueta(t, d["uf"], cor, (t.m, t.y + 30, L - t.m, t.y + 30 + livre),
                         opacidade=44)
    t.rodape("kvgs.github.io/senado-2026", f"{i} DE {n} · ARRASTA", cor, APAGADO)
    t.salvar(f"{pasta(d)}/{i}-capa.png")


def arte_origem(d: dict, cor: str, i: int, n: int):
    """Uma barra empilhada: parte-do-todo com tres segmentos, todos rotulados."""
    t = Tela(PAPEL, 96)
    cabecalho(t, d, cor, "DE ONDE VEM CADA INFORMAÇÃO")
    t.texto("A maior parte do que existe é do partido, não da candidatura",
            f("display", 56), TINTA, entre=1.08, larg=880)
    t.espaco(22)
    t.texto(f"As {d['publicadas']} informações publicadas do {d['uf_nome']}, "
            "por origem.", f("corpo", 30, 400), TINTA2, entre=1.38, larg=860)
    t.espaco(40)

    # A TINTA DE CADA ROTULO FOI MEDIDA CONTRA O SEU FUNDO, e nao escolhida pelo
    # que parecia. Texto claro sobre o cinza medio dava 3,12:1 e reprova em 4,5:1;
    # em tinta escura da 5,00:1. Rotulo dentro da barra e texto, e nao enfeite.
    partes = [("Da candidatura", d["origem"]["A"], cor, SOBRE_ESCURO),   # 6,59:1 no AP
              ("Do partido", d["origem"]["B"], MEIO, TINTA),                # 5,00:1
              ("Sem conteúdo", d["origem"]["D"] + d["origem"]["C"], CLARO, TINTA)]  # 13,1:1
    total = sum(x[1] for x in partes)
    larg_util = L - 2 * t.m
    alt = 96
    x = t.m
    for k, (nome, valor, fundo, tinta) in enumerate(partes):
        w = int((larg_util - GAP * (len(partes) - 1)) * valor / total)
        t.d.rectangle([x, t.y, x + w, t.y + alt], fill=fundo)
        # ROTULO DENTRO SO SE COUBER; senao ele vai para a legenda abaixo.
        fv = f("display", 44)
        if t.d.textlength(str(valor), font=fv) + 36 < w:
            t.d.text((x + 18, t.y + 22), str(valor), font=fv, fill=tinta)
        x += w + GAP
    t.y += alt + 26
    legenda(t, [(cor, f"Da candidatura · {d['origem']['A']}"),
                (MEIO, f"Do partido · {d['origem']['B']}"),
                (CLARO, f"Sem conteúdo · {d['origem']['D'] + d['origem']['C']}")])

    t.espaco(30)
    t.texto("“Sem conteúdo” não quer dizer que a candidatura não tenha proposta: "
            "quer dizer que nós não localizamos, e cada uma dessas linhas diz onde "
            "procuramos.", f("corpo", 27, 400), TINTA2, entre=1.42, larg=850)

    livre = t.base_do_rodape() - 30 - (t.y + 30)
    if livre > 150:
        desenha_silhueta(t, d["uf"], cor, (t.m, t.y + 30, L - t.m, t.y + 30 + livre),
                         opacidade=30)
    t.rodape("kvgs.github.io/senado-2026", f"{i} DE {n}", cor, APAGADO)
    t.salvar(f"{pasta(d)}/{i}-de-onde-vem.png")


def arte_por_tema(d: dict, cor: str, i: int, n: int):
    """Barras de UMA serie: uma cor so para todas. Rampa por valor em categoria
    nominal duplicaria o comprimento na cor sem acrescentar informacao."""
    t = Tela(PAPEL, 96)
    cabecalho(t, d, cor, "PROPOSTA DA PRÓPRIA CANDIDATURA, POR TEMA")
    # TODO O TEXTO DESTE SLIDE E CONTA. A versao anterior foi escrita para o Acre
    # e ficou chumbada: no Amapa ela dizia "das OITO candidaturas" (sao nove),
    # "DOIS nao tem nenhuma" (sao quatro) e citava "Habitacao e Tecnologia", que
    # sao os zeros do ACRE. Tres frases falsas num slide de grafico, que e onde
    # numero tem mais cara de fato.
    n_cand = d["candidaturas"]
    valores = [x["propria"] for x in d["por_tema"]]
    zeros = [x["tema"] for x in d["por_tema"] if x["propria"] == 0]
    teto = max(valores) if valores else 0
    t.texto(f"Em quantas das {num_extenso(n_cand)} candidaturas cada tema tem "
            "proposta própria", f("display", 52), TINTA, entre=1.08, larg=880)
    t.espaco(20)
    if zeros:
        sub = (f"Nenhum tema passa de {num_extenso(teto)}. "
               + (f"{num_extenso(len(zeros)).capitalize()} não têm nenhuma."
                  if len(zeros) > 1 else "Um não tem nenhuma."))
    else:
        sub = f"Nenhum tema passa de {num_extenso(teto)}."
    t.texto(sub, f("corpo", 30, 500), TINTA2, entre=1.38, larg=860)
    t.espaco(34)

    linhas = sorted(d["por_tema"], key=lambda x: (-x["propria"], x["tema"]))
    maximo = d["candidaturas"]

    # O NOME DO TEMA NAO E CORTADO. Na primeira versao ele saia com [:34] e
    # "Tecnologia e Inteligencia Artifici" foi publicado assim — rotulo cortado e
    # o defeito que a lista de erros chama pelo nome. O corpo cede tamanho ate o
    # nome mais longo caber na coluna, e se nem no menor couber, o script para.
    x0 = t.m + 470
    larg_esc = L - t.m - x0
    col = x0 - t.m - 24
    for tam in range(26, 17, -1):
        ft = f("corpo", tam, 400)
        if max(t.d.textlength(r["tema"], font=ft) for r in linhas) <= col:
            break
    else:
        raise SystemExit("PAROU: nome de tema nao cabe na coluna nem no corpo minimo.")

    # A altura de linha sai do espaco livre, e nao de um numero fixo: assim o
    # grafico ocupa a tela em vez de deixar meio slide vazio embaixo.
    if zeros:
        lista = (zeros[0] if len(zeros) == 1
                 else ", ".join(zeros[:-1]) + " e " + zeros[-1])
        rodape_txt = (f"{lista} não {'tem' if len(zeros) == 1 else 'têm'} proposta "
                      "própria de ninguém no estado. O que aparece nesses temas vem "
                      "do programa dos partidos.")
    else:
        rodape_txt = ("Todos os dez temas têm proposta própria de pelo menos uma "
                      "candidatura no estado.")
    fr = f("corpo", 27, 400)
    alto_rodape = len(t.quebra(rodape_txt, fr, 860)) * 38 + 40
    livre = t.base_do_rodape() - 40 - alto_rodape - t.y
    passo = max(46, min(78, livre // len(linhas)))
    alt_barra = min(34, passo - 16)

    # Grade fina e recessiva, com o maximo a vista para a barra ter escala.
    fg = f("mono", 18)
    for v in range(0, maximo + 1, 2):
        gx = x0 + int(larg_esc * v / maximo)
        t.d.rectangle([gx, t.y, gx + 1, t.y + passo * len(linhas) - 14], fill=LINHA)
        t.d.text((gx - 4, t.y - 26), str(v), font=fg, fill=APAGADO)

    fv = f("corpo", 26, 600)
    for r in linhas:
        w = int(larg_esc * r["propria"] / maximo)
        t.d.text((t.m, t.y + (alt_barra - tam) // 2), r["tema"], font=ft, fill=TINTA2)
        if w > 0:
            t.d.rounded_rectangle([x0, t.y, x0 + max(w, 10), t.y + alt_barra],
                                  radius=11, corners=(False, True, True, False),
                                  fill=cor)
            t.d.text((x0 + w + 16, t.y + 1), str(r["propria"]), font=fv, fill=TINTA)
        else:
            # Zero e um dado, e nao a falta de um: mostra a trilha e o numero.
            t.d.rectangle([x0, t.y + alt_barra // 2 - 1, x0 + larg_esc,
                           t.y + alt_barra // 2 + 1], fill=LINHA)
            t.d.text((x0 + 8, t.y + 1), "0", font=fv, fill=APAGADO)
        t.y += passo

    t.espaco(24)
    for ln in t.quebra(rodape_txt, fr, 860):
        t.d.text((t.m, t.y), ln, font=fr, fill=TINTA2)
        t.y += 38
    t.rodape("kvgs.github.io/senado-2026", f"{i} DE {n}", cor, APAGADO)
    t.salvar(f"{pasta(d)}/{i}-por-tema.png")


def arte_sites(d: dict, cor: str, i: int, n: int):
    """Numeros, e nao grafico: sao tres valores soltos, e barra de valor unico
    seria pior que o numero."""
    t = Tela(PAPEL2, 96)
    cabecalho(t, d, cor, "O QUE O REGISTRO NO TSE NÃO MOSTRA")
    # A MANCHETE ESTAVA CONTRADIZENDO O PLACAR LOGO ABAIXO DELA. O texto foi
    # escrito para o Acre — "Uma candidatura declarou site ao TSE. Seis tinham" —
    # e no Amapa saiu igual, com o placar dizendo TRES declararam. Manchete e
    # numero na mesma tela, um desmentindo o outro.
    dec, com, ach = d["declararam_site"], d["com_site"], d["achados"]
    t.texto(f"{num_extenso(dec).capitalize()} "
            f"candidatura{'' if dec == 1 else 's'} "
            f"{'declarou' if dec == 1 else 'declararam'} site ao TSE. "
            f"{num_extenso(com).capitalize()} {'tinha' if com == 1 else 'tinham'}.",
            f("display", 58), TINTA, entre=1.08, larg=880)
    t.espaco(24)
    if ach == 1:
        abre = "O outro foi encontrado na mão, e teve"
    else:
        abre = f"Os outros {num_extenso(ach)} foram encontrados um a um, e cada um teve"
    t.texto(f"{abre} a atribuição conferida antes de entrar, contra o que a "
            "candidatura declarou no registro no TSE.",
            f("corpo", 29, 400), TINTA2, entre=1.4, larg=860)
    t.espaco(48)

    fnum, frot = f("display", 96), f("mono", 22)
    x = t.m
    for valor, l1, l2 in ((d["declararam_site"], "DECLARARAM", "SITE AO TSE"),
                          (d["com_site"], "TINHAM", "SITE"),
                          (d["proprias_de_achado"], "PROPOSTAS", "VIERAM DELES")):
        t.d.text((x, t.y), str(valor), font=fnum, fill=cor)
        t.d.text((x, t.y + 108), l1, font=frot, fill=APAGADO)
        t.d.text((x, t.y + 138), l2, font=frot, fill=APAGADO)
        x += 300
    t.y += 138 + 44

    t.espaco(16)
    antes = d["proprias_antes"]
    t.texto(f"Antes dessa busca o acervo tinha "
            + (f"{antes} proposta própria" if antes == 1
               else f"{antes} propostas próprias")
            + f" no {d['uf_nome']}. Depois, {d['proprias']}.",
            f("corpo", 31, 500), TINTA, entre=1.4, larg=860)
    t.espaco(20)
    t.texto("A regra do projeto é só seguir endereço que a candidatura declarou "
            "no registro — é o que garante que o texto é mesmo dela. Este número "
            "é o preço dessa regra, medido num estado.",
            f("corpo", 26, 400), APAGADO, entre=1.42, larg=850)

    livre = t.base_do_rodape() - 30 - (t.y + 30)
    if livre > 150:
        desenha_silhueta(t, d["uf"], cor, (t.m, t.y + 30, L - t.m, t.y + 30 + livre),
                         opacidade=30)
    t.rodape("kvgs.github.io/senado-2026", f"{i} DE {n}", cor, APAGADO)
    t.salvar(f"{pasta(d)}/{i}-os-sites.png")


def arte_nao_mede(d: dict, cor: str, i: int, n: int):
    t = Tela(PAPEL, 96)
    cabecalho(t, d, cor, "O QUE ESTES NÚMEROS NÃO DIZEM")
    t.texto("Nenhum gráfico aqui compara candidaturas entre si",
            f("display", 58), TINTA, entre=1.08, larg=880)
    t.espaco(26)
    fr = f("corpo", 28, 400)
    for titulo, txt in (
        ("Não é ranking",
         "Contar propostas por pessoa e ordenar mediria verba de campanha e "
         "tamanho de assessoria, não qualidade de candidatura. Por isso os "
         "recortes são por tema e por origem da informação."),
        ("Não mede quem propõe mais",
         "Quem tem menos linhas aqui pode ter publicado material que nós ainda "
         "não localizamos. A ausência no acervo é sobre o nosso levantamento."),
        ("Não avalia o conteúdo",
         "O projeto não diz se uma proposta é boa, viável ou verdadeira. Ele diz "
         "de onde ela saiu e mostra o trecho, para você julgar."),
    ):
        t.d.rectangle([t.m, t.y + 10, t.m + 14, t.y + 24], fill=cor)
        t.d.text((t.m + 28, t.y), titulo, font=f("corpo", 30, 600), fill=TINTA)
        t.y += 44
        for ln in t.quebra(txt, fr, 790):
            t.d.text((t.m + 28, t.y), ln, font=fr, fill=TINTA2)
            t.y += 39
        t.espaco(26)
        if t.y > t.base_do_rodape() - 60:
            raise SystemExit("PAROU: as ressalvas nao cabem no slide.")
    t.rodape("kvgs.github.io/senado-2026", f"{i} DE {n}", cor, APAGADO)
    t.salvar(f"{pasta(d)}/{i}-o-que-nao-mede.png")


def arte_fecho(d: dict, cor: str, i: int, n: int):
    t = Tela(PAPEL2, 96)
    cabecalho(t, d, cor, "COMO CONFERIR")
    t.texto("Cada número aqui sai do acervo na hora de gerar a imagem",
            f("display", 56), TINTA, entre=1.08, larg=880)
    t.espaco(26)
    t.texto("Nenhum foi digitado à mão. Se a revisão reprovar uma informação, a "
            "próxima geração muda o gráfico — número digitado numa arte envelhece "
            "calado, e no Instagram não dá para corrigir depois.",
            f("corpo", 30, 400), TINTA2, entre=1.4, larg=860)
    t.espaco(36)
    t.texto("No site, cada linha traz o documento de onde saiu, o trecho citado, o "
            "selo de origem e se já passou por revisão humana. Os dados são "
            "abertos e o código é público.",
            f("corpo", 30, 400), TINTA2, entre=1.4, larg=860)

    livre = t.base_do_rodape() - 30 - (t.y + 30)
    if livre > 150:
        desenha_silhueta(t, d["uf"], cor, (t.m, t.y + 30, L - t.m, t.y + 30 + livre),
                         opacidade=40)
    t.rodape("kvgs.github.io/senado-2026", "@CANDIDATURASENADO", cor, APAGADO)
    t.salvar(f"{pasta(d)}/{i}-fecho.png")


def pasta(d: dict) -> str:
    return f"7-{d['uf'].lower()}-analise"


def escreve_legenda(d: dict, cor_de: str, n_slides: int) -> None:
    """A legenda sai do mesmo lugar que os graficos.

    A do Acre foi escrita a mao e trazia os numeros do Acre. Isso funciona uma
    vez: no segundo estado, quem copia herda "o primeiro estado conferido por
    inteiro", "oito candidaturas" e "Habitacao e Tecnologia" — os tres erros que
    a arte tinha e que esta rodada corrigiu. Legenda escrita a mao envelhece com
    a arte.
    """
    nome = d["uf_nome"]
    tag = lambda s: "#" + s.lower().replace(" ", "").replace("-", "")
    tags = " ".join([tag("eleições2026"), tag("senado"), tag(nome),
                     tag("dadosabertos"), tag("votoconsciente"),
                     tag("transparência"), tag("jornalismodedados"),
                     tag("política"), tag("brasil")])
    zeros = [x["tema"] for x in d["por_tema"] if x["propria"] == 0]
    teto = max([x["propria"] for x in d["por_tema"]] or [0])
    A, B = d["origem"]["A"], d["origem"]["B"]
    vazio = d["origem"]["C"] + d["origem"]["D"]
    dec, com, ach = d["declararam_site"], d["com_site"], d["achados"]

    itens = [
        f"▪️ De cada dez informações publicadas, "
        f"{A / max(1, d['publicadas']) * 10:.1f}".replace(".", ",")
        + f" são da própria candidatura: {A} de {d['publicadas']}. "
        f"{B} vêm do programa do partido e {vazio} são temas em que não "
        "localizamos nada.",

        f"▪️ Nenhum tema tem proposta própria em mais de "
        f"{num_extenso(teto)} das {num_extenso(d['candidaturas'])} candidaturas."
        + (f" {', '.join(zeros)} não "
           f"{'tem' if len(zeros) == 1 else 'têm'} nenhuma: o que aparece ali é "
           "programa de partido." if zeros else ""),

        f"▪️ {num_extenso(dec).capitalize()} candidatura"
        f"{'' if dec == 1 else 's'} {'declarou' if dec == 1 else 'declararam'} "
        f"site ao TSE. {num_extenso(com).capitalize()} "
        f"{'tinha' if com == 1 else 'tinham'}."
        + (f" {'O outro foi' if ach == 1 else f'Os outros {num_extenso(ach)} foram'} "
           f"encontrado{'' if ach == 1 else 's'} um a um — e é de onde "
           f"{'saiu' if d['proprias_de_achado'] == 1 else 'saíram'} "
           f"{d['proprias_de_achado']} das {d['proprias']} propostas próprias do "
           f"estado. Antes dessa busca o acervo tinha {d['proprias_antes']}."
           if ach else ""),
    ]

    corpo = f"""# O que o acervo do {nome} mostra — análise

{n_slides} slides: capa com o número principal, três recortes de dados, as
ressalvas do que os números não medem, e o fecho.
Gerado por `python gerar_artes_analise_uf.py --uf {d["uf"]}`.

---

## Legenda — copie daqui até as hashtags, sem mexer

O {nome} é {ordem_em_prosa(d)} — e agora dá para olhar os números.

São {d["candidaturas"]} candidaturas e {d["temas"]} temas. As {d["revisadas"]} informações publicadas foram lidas uma a uma por uma pessoa. Aqui está o que elas mostram. 👇

""" + f"""{(chr(10) + chr(10)).join(itens)}

⚠️ O QUE ESTES NÚMEROS NÃO DIZEM: nenhum gráfico aqui compara candidaturas entre si. Contar propostas por pessoa e ordenar mediria verba de campanha e tamanho de assessoria, não qualidade de candidatura. Por isso todos os recortes são por tema e por origem da informação.

E "sem conteúdo" não quer dizer que a candidatura não tenha proposta: quer dizer que NÓS não localizamos — e cada uma dessas {vazio} linhas diz, no site, onde procuramos.

🔗 kvgs.github.io/senado-2026 — dados abertos, código público.

{tags}

---

## Como os números foram apurados

Todos saem do acervo **na hora de gerar a imagem**, e nenhum foi digitado. Se a
revisão reprovar uma informação, a próxima geração muda o gráfico.

O script **para com erro** se o estado tiver alguma linha sem decisão da revisão.
Gráfico tem cara de fato e não mostra o selo "não revisado" que cada linha
carrega no site.

## Decisões de visualização

- **Nenhum gráfico compara candidaturas.** É a regra que mais restringiu o que
  podia ser desenhado.
- **Uma série por gráfico.** As barras por tema têm uma cor só.
- **Os sites viraram número, não gráfico.** São três valores soltos; barra de
  valor único é pior que o número.
- **Zero é um dado.** Tema sem proposta própria aparece com a trilha da escala e
  o "0" escrito, e não como linha em branco.
- **A escala vai até o total de candidaturas**, e não até o maior valor. Cortar a
  escala faria "{teto} de {d['candidaturas']}" parecer muito.
- **A cor é a do estado**: {cor_de}
"""
    alvo = RAIZ / "artes-instagram" / pasta(d) / "LEGENDA.md"
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(corpo, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", required=True)
    a = ap.parse_args()
    uf = a.uf.upper()
    if uf not in PALETA:
        raise SystemExit(f"PAROU: {uf} nao tem cor definida em PALETA.")
    cor = PALETA[uf]["cor"]
    d = medir(uf)
    n = 6
    arte_capa(d, cor, 1, n)
    arte_origem(d, cor, 2, n)
    arte_por_tema(d, cor, 3, n)
    arte_sites(d, cor, 4, n)
    arte_nao_mede(d, cor, 5, n)
    arte_fecho(d, cor, 6, n)
    escreve_legenda(d, PALETA[uf]["de"], n)
    print(f"  {pasta(d)}/  ({n} slides · {d['publicadas']} publicadas, "
          f"{d['revisadas']} revisadas)")


if __name__ == "__main__":
    main()
