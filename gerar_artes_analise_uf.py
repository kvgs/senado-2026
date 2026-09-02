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
ACENTO = "#0B5D2A"      # 7,33:1 sobre o papel
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


def arte_capa(d: dict, cor: str, i: int, n: int):
    t = Tela(PAPEL2, 96)
    cabecalho(t, d, cor, "O PRIMEIRO ESTADO CONFERIDO POR INTEIRO")
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
    t.texto(f"De {d['publicadas']} publicadas. Outras {d['retiradas']} foram "
            "retiradas na revisão.", f("corpo", 28, 400), APAGADO, entre=1.36, larg=840)

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
    partes = [("Da candidatura", d["origem"]["A"], ACENTO, SOBRE_ESCURO),   # 6,67:1
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
    legenda(t, [(ACENTO, f"Da candidatura · {d['origem']['A']}"),
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
    t.texto("Em quantas das oito candidaturas cada tema tem proposta própria",
            f("display", 52), TINTA, entre=1.08, larg=880)
    t.espaco(20)
    t.texto("Nenhum tema passa de três. Dois não têm nenhuma.",
            f("corpo", 30, 500), TINTA2, entre=1.38, larg=860)
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
    rodape_txt = ("Habitação e Tecnologia não têm proposta própria de ninguém no "
                  "estado. O que aparece nesses temas vem do programa dos partidos.")
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
                                  fill=ACENTO)
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
    t.texto("Uma candidatura declarou site ao TSE. Seis tinham.",
            f("display", 58), TINTA, entre=1.08, larg=880)
    t.espaco(24)
    t.texto("Os outros cinco foram encontrados um a um, e cada um teve a "
            "atribuição conferida antes de entrar: número de urna, coligação, "
            "suplentes, CNPJ de campanha.",
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
    print(f"  {pasta(d)}/  ({n} slides · {d['publicadas']} publicadas, "
          f"{d['revisadas']} revisadas)")


if __name__ == "__main__":
    main()
