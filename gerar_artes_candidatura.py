# -*- coding: utf-8 -*-
"""Um carrossel por candidatura: uma imagem por tema, com o que o acervo tem.

O QUE ESTE CARROSSEL FAZ DE DIFERENTE DOS OUTROS. Os anteriores mostram muita
gente de relance. Este mostra UMA candidatura nos dez temas — e por isso ele e o
primeiro que precisa dizer, em cada slide, DE QUEM e a proposta e o que falta.

OS CINCO ROTULOS SAO OS DO SITE, e nao tres. O pedido falava em "candidato,
partido ou nao achamos". O site distingue mais que isso, e a distincao e a tese do
projeto:

  A            proposta da propria candidatura
  B            proposta do PARTIDO, aplicada a candidatura
  C            tem material publicado e NAO aborda este tema
  D            nao localizamos fonte — afirmacao sobre a NOSSA busca
  sem registro este cruzamento ainda nao foi trabalhado

Juntar C, D e "sem registro" num "nao achamos" faria a arte mentir sobre nos
mesmos: quem publicou material e nao falou do tema, quem nao tem material que
achassemos, e quem simplesmente nao chegou a nossa fila sao tres situacoes
diferentes. A frase de cada uma e a mesma que esta na tela do site.

A IDENTIDADE DO ESTADO E A SILHUETA DELE, mais uma cor tirada da bandeira. A
silhueta sai da malha do IBGE que o projeto ja usa no mapa da pagina inicial
(dados/mapa-uf.json) — serve para os 27 sem eu desenhar nada, e nenhum estado se
confunde com outro. A cor vem da bandeira, ESCURECIDA ate passar 4,5:1 sobre o
papel: o verde oficial do Acre da 3,33:1 e nao serve para texto.

O SCRIPT PARA em vez de desenhar por cima do rodape, e para em vez de inventar
paleta de estado que ninguem escolheu. Ja foi publicada uma arte com a ultima
fileira sobre o rodape sem ninguem ver.

USO
    python gerar_artes_candidatura.py --uf AC --numero 100
    python gerar_artes_candidatura.py --uf AC --todos
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import unicodedata

from PIL import Image, ImageDraw

import acervo
import gerar_artes as _ar
from gerar_artes import (A, APAGADO, L, LINHA, PAPEL, PAPEL2, SOBRE_ESCURO, TINTA,
                         TINTA2, Tela, f)

RAIZ = pathlib.Path(__file__).resolve().parent

# ---------------------------------------------------------------- paleta por UF
# A cor sai da BANDEIRA do estado, escurecida ate passar 4,5:1 sobre o papel
# (#F7F4F1). Cada linha diz de onde a cor veio, porque "verde do Acre" e uma
# afirmacao sobre a bandeira e alguem tem de poder conferir.
#
# Estado que nao esta aqui faz o script PARAR. Escolher cor por conta propria
# seria inventar identidade visual para um lugar sem ninguem ter decidido.
PALETA = {
    "AC": {"cor": "#007A2E", "de": "verde da bandeira do Acre, escurecido de "
                                   "#009B3A (3,33:1) para 5,01:1 sobre o papel"},
}

SELO = {
    "oficial": "documento oficial",
    "verificada": "conferida por reportagem",
    "secundaria": "fonte secundária",
    "declaracao_candidato": "declaração da candidatura",
    "registro_legislativo": "registro legislativo",
}

# As frases sao as do site. Mudar aqui e mudar o que o projeto afirma.
ROTULO = {
    "A": ("PROPOSTA PRÓPRIA", "acento",
          "Da própria candidatura.", "Proposta própria"),
    "B": ("PROPOSTA DO PARTIDO", "neutro",
          "Do programa do partido, não da candidatura.", "Proposta do partido"),
    "C": ("NÃO ABORDA ESTE TEMA", "ausente",
          "A candidatura publicou material e não trata deste tema.",
          "Não aborda este tema"),
    "D": ("NÃO LOCALIZAMOS FONTE", "ausente",
          "Isto é uma afirmação sobre a nossa busca, não sobre a candidatura.",
          "Não localizamos fonte"),
    "-": ("AINDA NÃO TRABALHADO", "ausente",
          "Diferente de “não aborda” e de “não localizamos”: este cruzamento "
          "ainda não passou pela nossa fila.", "Ainda não trabalhado"),
}
ORDEM = {"A": 0, "B": 1, "C": 2, "D": 3, "-": 4}

def recusados() -> dict[str, dict]:
    """Partidos cujo programa nao foi aplicado, e o motivo — de dados/.

    Sem isto, a capa do Petecao mostra 0, 0 e 10 e o leitor conclui que a pessoa
    nao tem propostas. O que houve foi uma decisao NOSSA sobre o documento do
    PSD. Numero sobre o nosso acervo com cara de numero sobre a candidatura e a
    coisa que este projeto mais tenta nao fazer.
    """
    arq = RAIZ / "dados" / "programas-recusados.json"
    if not arq.exists():
        return {}
    return {x["id_partido"]: x
            for x in json.loads(arq.read_text(encoding="utf-8"))["recusados"]}


CINZA_CAIXA = "#F0EDEA"
CINZA_BORDA = "#DDD6CF"


def sem_acento(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", sem_acento(s).lower()).strip("-")


# ------------------------------------------------------------------- silhueta
def silhueta(uf: str) -> list[list[tuple[float, float]]]:
    """Aneis da UF, em coordenadas de tela ja com o y do IBGE desfeito."""
    d = json.loads((RAIZ / "dados" / "mapa-uf.json").read_text(encoding="utf-8"))
    cam = d["paths"].get(uf)
    if not cam:
        raise SystemExit(f"PAROU: {uf} nao esta em dados/mapa-uf.json")
    aneis = []
    for parte in cam.split("Z"):
        pts = [tuple(float(v) for v in par.split(","))
               for par in re.findall(r"[ML](-?\d+,-?\d+)", parte)]
        if len(pts) >= 3:
            # O IBGE aplica scale(0.0001,-0.0001): o y e negado na exibicao.
            aneis.append([(x, -y) for x, y in pts])
    if not aneis:
        raise SystemExit(f"PAROU: a silhueta de {uf} saiu vazia")
    return aneis


def desenha_silhueta(t: Tela, uf: str, cor: str, caixa: tuple[int, int, int, int],
                     opacidade: int = 255):
    """Desenha a UF INTEIRA dentro de `caixa` = (x0, y0, x1, y1), centrada.

    A escala sai do lado mais apertado, e nao da altura. Dimensionada so pela
    altura, a silhueta do Acre — que e larga e baixa — saiu pelas duas bordas da
    tela e virou um borrao sem forma. Estado tem proporcao propria: Amapa e alto,
    Acre e largo, e uma conta que ignora isso corta um deles.
    """
    x0, y0, x1, y1 = caixa
    aneis = silhueta(uf)
    xs = [p[0] for a in aneis for p in a]
    ys = [p[1] for a in aneis for p in a]
    esc = min((x1 - x0) / (max(xs) - min(xs)), (y1 - y0) / (max(ys) - min(ys)))
    larg, alt = (max(xs) - min(xs)) * esc, (max(ys) - min(ys)) * esc
    ox = x0 + ((x1 - x0) - larg) / 2 - min(xs) * esc
    oy = y0 + ((y1 - y0) - alt) / 2 - min(ys) * esc

    # Camada propria, para a opacidade valer sobre o papel sem sujar o texto.
    capa = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    dd = ImageDraw.Draw(capa)
    rgb = tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))
    for anel in aneis:
        dd.polygon([(ox + x * esc, oy + y * esc) for x, y in anel],
                   fill=rgb + (opacidade,))
    t.img.alpha_composite(capa) if t.img.mode == "RGBA" else \
        t.img.paste(Image.alpha_composite(t.img.convert("RGBA"), capa).convert("RGB"), (0, 0))


# --------------------------------------------------------------------- acervo
def medir(uf: str, numero: str | None = None) -> dict:
    uf_l = uf.lower()
    cands = acervo.ler("candidaturas.json", uf)["candidaturas"]
    pos = [p for p in acervo.ler("posicoes.json", uf)["posicoes"]
           if (p.get("revisao") or {}).get("resultado") not in ("remover", "corrigir")]
    docs = {d["id_documento"]: d
            for d in acervo.ler("documentos.json", uf)["documentos"]}
    ref = acervo.ler("referencia.json")
    temas = [t for t in ref["temas"] if "senador" in t.get("aplicavel_a_cargos", [])]
    partidos = {p["id_partido"]: p["sigla"] for p in ref["partidos"]}
    est = next(e for e in acervo.ler("estados.json")["estados"] if e["uf"] == uf)

    escolhidas = sorted(cands, key=lambda c: int(c["numero_urna"]))
    if numero:
        escolhidas = [c for c in escolhidas if str(c["numero_urna"]) == str(numero)]
        if not escolhidas:
            raise SystemExit(f"PAROU: nenhuma candidatura com numero {numero} em {uf}")

    saida = []
    for c in escolhidas:
        cid = c["id_candidatura"]
        blocos = []
        for t in temas:
            minhas = [p for p in pos
                      if (p.get("id_candidatura_contexto") or p.get("atribuido_a_id")) == cid
                      and p.get("id_tema") == t["id_tema"]]
            minhas.sort(key=lambda p: ORDEM.get(p.get("estado_cobertura"), 9))
            if minhas:
                p = minhas[0]
                doc = docs.get(p.get("id_documento"), {})
                blocos.append({
                    "tema": t["nome"], "estado": p.get("estado_cobertura") or "-",
                    "citacao": p.get("citacao_literal") or "",
                    "texto": p.get("texto") or "",
                    "selo": SELO.get(p.get("nivel_fonte"), p.get("nivel_fonte") or ""),
                    "fonte": doc.get("titulo", ""),
                    "partido": partidos.get(p.get("atribuido_a_id"), "") if
                               p.get("atribuido_a_tipo") == "partido" else "",
                    "revisado": bool(p.get("revisado_por_humano")),
                    "mais": len(minhas) - 1,
                })
            else:
                blocos.append({"tema": t["nome"], "estado": "-", "citacao": "",
                               "texto": "", "selo": "", "fonte": "", "partido": "",
                               "revisado": False, "mais": 0})
        arq = (c.get("foto") or {}).get("arquivo")
        saida.append({
            "cid": cid, "nome": c["pessoa"]["nome_urna"],
            "recusa": recusados().get(c["id_partido"]),
            "numero": str(c["numero_urna"]),
            "sigla": partidos.get(c["id_partido"], c["id_partido"]),
            "foto": RAIZ / arq if arq else None,
            "blocos": blocos,
            "n_proprias": sum(1 for b in blocos if b["estado"] == "A"),
            "n_partido": sum(1 for b in blocos if b["estado"] == "B"),
            "n_vazios": sum(1 for b in blocos if b["estado"] in ("-", "C", "D")),
        })
    return {"uf": uf, "uf_nome": est["nome"], "regiao": est["regiao"],
            "gente": saida, "n_temas": len(temas)}


# ---------------------------------------------------------------------- artes
def pasta(uf: str, nome: str, numero: str) -> str:
    return f"6-{uf.lower()}-{numero}-{slug(nome)}"


def arte_capa(d: dict, p: dict, cor: str, i: int, n_slides: int):
    t = Tela(PAPEL2, 96)
    t.y = 96
    t.mono(f"ELEIÇÕES 2026 · SENADO · {d['uf_nome'].upper()}",
           f("mono", 20), cor, espacamento=4)
    t.espaco(22)

    if p["foto"] and p["foto"].exists():
        foto = Image.open(p["foto"]).convert("RGB")
        lar = 232
        alt = int(foto.height * lar / foto.width)
        t.img.paste(foto.resize((lar, alt), Image.LANCZOS), (96, t.y))
        t.d.rectangle([96, t.y, 96 + lar, t.y + alt], outline=cor, width=3)
        x_txt = 96 + lar + 34
        t.d.text((x_txt, t.y + 4), p["numero"], font=f("mono", 62), fill=cor)
        yy = t.y + 4 + 74
        for ln in t.quebra(p["nome"], f("display", 58), L - 96 - x_txt):
            t.d.text((x_txt, yy), ln, font=f("display", 58), fill=TINTA)
            yy += 64
        t.d.text((x_txt, yy + 6), p["sigla"], font=f("mono", 26), fill=TINTA2)
        t.y = max(t.y + alt, yy + 46)
    t.espaco(40)

    t.texto(f"O que o site já levantou, tema a tema",
            f("display", 54), TINTA, entre=1.1, larg=880)
    t.espaco(20)
    t.texto("Cada slide traz um dos dez temas e diz de quem é a proposta — "
            "da candidatura ou do partido — ou o que ainda não há.",
            f("corpo", 33), TINTA2, entre=1.4, larg=860)

    # O placar da propria candidatura: nao compara com ninguem, e por isso pode
    # existir. Contagem entre candidaturas viraria ranking, que este projeto nao faz.
    t.espaco(46)
    fnum, frot = f("display", 74), f("mono", 22)
    x = t.m
    for valor, rotulo in ((p["n_proprias"], "PRÓPRIAS"),
                          (p["n_partido"], "DO PARTIDO"),
                          (p["n_vazios"], "SEM CONTEÚDO")):
        t.d.text((x, t.y), str(valor), font=fnum, fill=cor if valor else APAGADO)
        t.d.text((x, t.y + 82), rotulo, font=frot, fill=APAGADO)
        x += 300
    t.y += 82 + 34

    # A RESSALVA E OBRIGATORIA, e vem colada no placar. Sem ela, "0 PRÓPRIAS" le
    # como afirmacao sobre a pessoa, quando e afirmacao sobre o nosso trabalho.
    t.espaco(10)
    fa = f("corpo", 25)
    aviso = ("Estes três números são sobre o nosso levantamento, "
             "não sobre a candidatura.")
    if p["recusa"] and not p["n_partido"]:
        aviso += (f" O programa do {p['recusa']['sigla']} não entrou no acervo: "
                  f"{p['recusa']['motivo_curto']}.")
    for ln in t.quebra(aviso, fa, 880):
        t.d.text((t.m, t.y), ln, font=fa, fill=APAGADO)
        t.y += int(fa.size * 1.36)

    # A silhueta entra DEPOIS, na faixa que sobrou, e inteira. O vazio entre o
    # placar e o rodape era o problema; agora ele e o lugar da identidade do estado.
    livre = t.base_do_rodape() - 30 - (t.y + 30)
    if livre > 150:
        desenha_silhueta(t, d["uf"], cor,
                         (t.m, t.y + 30, L - t.m, t.y + 30 + livre), opacidade=48)
        t.d.text((t.m, t.base_do_rodape() - 62), d["uf_nome"].upper(),
                 font=f("mono", 26), fill=cor)

    t.rodape("kvgs.github.io/senado-2026", f"{i} DE {n_slides} · ARRASTA",
             cor, APAGADO)
    t.salvar(f"{pasta(d['uf'], p['nome'], p['numero'])}/{i}-capa.png")


def caixa_rotulo(t: Tela, estado: str, cor: str, sigla: str) -> None:
    """A tarja que diz DE QUEM e — a informacao mais importante do slide."""
    rot, tipo, _, _ = ROTULO[estado]
    if estado == "B" and sigla:
        rot = f"PROPOSTA DO {sigla}"
    fundo, tinta = ((cor, SOBRE_ESCURO) if tipo == "acento"
                    else (CINZA_CAIXA, TINTA) if tipo == "neutro"
                    else (PAPEL2, APAGADO))
    fr = f("mono", 24)
    larg = t.d.textlength(rot, font=fr) + 46
    t.d.rounded_rectangle([t.m, t.y, t.m + larg, t.y + 52], 26, fill=fundo,
                          outline=None if tipo == "acento" else CINZA_BORDA,
                          width=0 if tipo == "acento" else 2)
    t.d.text((t.m + 23, t.y + 13), rot, font=fr, fill=tinta)
    t.y += 52


def arte_tema(d: dict, p: dict, b: dict, cor: str, i: int, n_slides: int,
              n_tema: int):
    t = Tela(PAPEL, 96)
    desenha_silhueta(t, d["uf"], cor, (L - 96 - 210, 74, L - 96, 74 + 150),
                     opacidade=30)
    t.y = 92
    t.mono(f"{p['numero']} · {p['nome'].upper()} · {p['sigla']}",
           f("mono", 19), APAGADO, espacamento=3)
    t.espaco(14)
    t.mono(f"TEMA {n_tema} DE {d['n_temas']}", f("mono", 19), cor, espacamento=3)
    t.espaco(16)
    t.texto(b["tema"], f("display", 62), TINTA, entre=1.06, larg=820)
    t.espaco(30)
    caixa_rotulo(t, b["estado"], cor, b["partido"])
    t.espaco(30)

    # O PE DO SLIDE E MEDIDO ANTES do corpo, para o corpo saber ate onde vai e para
    # o vazio do meio deixar de existir. Na primeira versao o texto ficava colado no
    # topo e sobravam 400px de nada no centro do slide.
    pes = []
    if b["selo"]:
        pes.append("Origem: " + b["selo"] +
                   (" · conferida por gente" if b["revisado"]
                    else " · ainda não revisada por gente"))
    if b["fonte"]:
        pes.append("Fonte: " + b["fonte"])
    if b["mais"]:
        pes.append(f"Há mais {b['mais']} informação(ões) neste tema no site.")
    fp = f("corpo", 22)
    alto_pe = (sum(len(t.quebra(x, fp, 830)) for x in pes) * int(fp.size * 1.36) + 34
               if pes else 0)
    base = t.base_do_rodape() - 34 - alto_pe - 34
    topo_corpo = t.y
    if b["citacao"]:
        # A CITACAO E O DADO, e o resumo vem depois dela — nunca no lugar dela. O
        # corpo cede tamanho para nao cortar palavra da fonte.
        tam = 36
        while tam >= 22:
            fc = f("corpo", tam)
            linhas = t.quebra("“" + b["citacao"] + "”", fc, 860)
            alto_cit = len(linhas) * int(fc.size * 1.42)
            fr = f("corpo", 32, 500)
            l_res = t.quebra(b["texto"], fr, 830) if b["texto"] else []
            alto = alto_cit + (30 + len(l_res) * int(fr.size * 1.4) if l_res else 0) + 90
            if t.y + alto <= base:
                break
            tam -= 2
        else:
            raise SystemExit(
                f"PAROU: a citacao de {p['nome']} em {b['tema']} nao cabe nem no "
                "corpo minimo. O desenho passaria por cima do rodape, e isso ja foi "
                "publicado uma vez sem ninguem ver. Encurte a citacao na revisao.")
        t.y = topo_corpo + max(0, (base - topo_corpo - alto) // 2)
        t.d.rectangle([t.m, t.y, t.m + 4, t.y + alto_cit - 8], fill=cor)
        yy = t.y
        for ln in linhas:
            t.d.text((t.m + 26, yy), ln, font=fc, fill=TINTA)
            yy += int(fc.size * 1.42)
        t.y = yy
        if l_res:
            t.espaco(30)
            for ln in l_res:
                t.d.text((t.m, t.y), ln, font=fr, fill=TINTA2)
                t.y += int(fr.size * 1.4)
    else:
        _, _, frase, _ = ROTULO[b["estado"]]
        # SEM CENTRAR. Centrado, o texto ficava solto no meio da tela com um vazio
        # acima da tarja — parecia erro. A frase vem logo abaixo da tarja, que e o
        # que ela explica, e o resto do espaco fica para a silhueta.
        fa = f("corpo", 34)
        linhas = t.quebra(frase, fa, 850)
        for ln in linhas:
            t.d.text((t.m, t.y), ln, font=fa, fill=TINTA2)
            t.y += int(fa.size * 1.42)
        # Tema sem conteudo deixava 700px de nada no meio do slide. A silhueta
        # ocupa o espaco SEM inventar informacao: o vazio continua legivel como
        # vazio, que e o que este projeto quer dizer, e o slide para de parecer
        # defeito de geracao.
        sobra = base - t.y - 40
        if sobra > 180:
            desenha_silhueta(t, d["uf"], cor,
                             (t.m, t.y + 40, L - t.m, t.y + 40 + sobra),
                             opacidade=30)

    # O pe: o selo da fonte e o aviso de revisao. Sem isto a arte afirmaria com
    # mais forca do que o acervo.
    if pes:
        t.y = t.base_do_rodape() - 34 - alto_pe
        t.d.rectangle([t.m, t.y, L - t.m, t.y + 1], fill=LINHA)
        t.y += 22
        for x in pes:
            for ln in t.quebra(x, fp, 830):
                t.d.text((t.m, t.y), ln, font=fp, fill=APAGADO)
                t.y += int(fp.size * 1.36)

    t.rodape("kvgs.github.io/senado-2026", f"{i} DE {n_slides}", cor, APAGADO)
    t.salvar(f"{pasta(d['uf'], p['nome'], p['numero'])}/"
             f"{i}-{n_tema:02d}-{slug(b['tema'])}.png")


def arte_sem_conteudo(d: dict, p: dict, vazios: list, cor: str, i: int,
                      n_slides: int):
    """Todos os temas sem conteudo num slide, agrupados pelo TIPO de ausencia.

    Antes, cada tema vazio ocupava um slide inteiro. No Petecao isso dava dez
    slides quase iguais, e o carrossel falava mais da nossa fila do que da
    candidatura. Juntar encurta e, principalmente, deixa a desigualdade legivel
    de uma vez.

    O AGRUPAMENTO E POR TIPO, e nao tudo numa lista so. "Publicou material e nao
    falou do tema", "nao localizamos fonte" e "ainda nao entrou na nossa fila"
    continuam sendo tres coisas diferentes — juntar as tres num monte desfaria
    exatamente a distincao que este carrossel existe para mostrar.
    """
    t = Tela(PAPEL, 96)
    desenha_silhueta(t, d["uf"], cor, (L - 96 - 210, 74, L - 96, 74 + 150),
                     opacidade=30)
    t.y = 92
    t.mono(f"{p['numero']} · {p['nome'].upper()} · {p['sigla']}",
           f("mono", 19), APAGADO, espacamento=3)
    t.espaco(14)
    t.mono(f"{len(vazios)} DE {d['n_temas']} TEMAS", f("mono", 19), cor,
           espacamento=3)
    t.espaco(16)
    t.texto("Temas sem conteúdo no acervo", f("display", 58), TINTA,
            entre=1.06, larg=800)
    t.espaco(22)
    t.texto("Isto é uma afirmação sobre o nosso levantamento, e não sobre a "
            "candidatura.", f("corpo", 30, 500), TINTA2, entre=1.38, larg=840)
    t.espaco(36)

    por_tipo = {}
    for b in vazios:
        por_tipo.setdefault(b["estado"], []).append(b["tema"])

    for est in ("C", "D", "-"):
        nomes = por_tipo.get(est)
        if not nomes:
            continue
        _, tipo, frase, titulo = ROTULO[est]
        t.d.rectangle([t.m, t.y + 10, t.m + 14, t.y + 24], fill=CINZA_BORDA)
        t.d.text((t.m + 28, t.y), f"{titulo} ({len(nomes)})",
                 font=f("corpo", 29, 600), fill=TINTA)
        t.y += 44
        fl = f("corpo", 28, 400)
        for ln in t.quebra(" · ".join(nomes), fl, 790):
            t.d.text((t.m + 28, t.y), ln, font=fl, fill=TINTA2)
            t.y += 39
        t.espaco(8)
        fe = f("corpo", 23, 400)
        for ln in t.quebra(frase, fe, 780):
            t.d.text((t.m + 28, t.y), ln, font=fe, fill=APAGADO)
            t.y += 32
        t.espaco(26)
        if t.y > t.base_do_rodape() - 40:
            raise SystemExit(
                f"PAROU: a lista de temas sem conteudo de {p['nome']} nao cabe no "
                "slide. O desenho passaria por cima do rodape, e isso ja foi "
                "publicado uma vez sem ninguem ver.")

    # Quando so ha um tipo de ausencia, a lista e curta e sobra meia tela. A
    # silhueta ocupa sem inventar informacao.
    sobra = t.base_do_rodape() - 30 - (t.y + 30)
    if sobra > 200:
        desenha_silhueta(t, d["uf"], cor,
                         (t.m, t.y + 30, L - t.m, t.y + 30 + sobra), opacidade=30)

    t.rodape("kvgs.github.io/senado-2026", f"{i} DE {n_slides}", cor, APAGADO)
    t.salvar(f"{pasta(d['uf'], p['nome'], p['numero'])}/{i}-temas-sem-conteudo.png")


def arte_fecho(d: dict, p: dict, cor: str, i: int, n_slides: int):
    t = Tela(PAPEL2, 96)
    t.y = 100
    t.mono(f"{d['uf_nome'].upper()} · {p['numero']} {p['nome'].upper()}",
           f("mono", 20), cor, espacamento=4)
    t.espaco(20)
    t.texto("A página com as fontes de cada linha está no site",
            f("display", 62), TINTA, entre=1.08, larg=880)
    t.espaco(26)
    t.texto("Lá cada informação traz o documento de onde saiu, o selo de origem e "
            "o que ainda não foi encontrado. Nada aqui é resumo sem fonte.",
            f("corpo", 33), TINTA2, entre=1.4, larg=860)

    t.espaco(44)
    t.mono("O QUE CADA TARJA QUER DIZER", f("mono", 19), APAGADO, espacamento=3)
    t.espaco(18)
    fr, ft = f("corpo", 26), f("corpo", 27)
    for est in ("A", "B", "C", "D", "-"):
        _, tipo, frase, titulo = ROTULO[est]
        # Quadradinho DESENHADO. O caractere "▪" nao existe na fonte do corpo e
        # saia como retangulo vazio — o famoso tofu — em todos os cinco itens.
        t.d.rectangle([t.m, t.y + 10, t.m + 14, t.y + 24],
                      fill=cor if tipo == "acento" else
                           TINTA2 if tipo == "neutro" else CINZA_BORDA)
        t.d.text((t.m + 28, t.y), titulo, font=ft, fill=TINTA)
        t.y += 36
        for ln in t.quebra(frase, fr, 800):
            t.d.text((t.m + 28, t.y), ln, font=fr, fill=TINTA2)
            t.y += int(fr.size * 1.34)
        t.y += 14

    livre = t.base_do_rodape() - 30 - (t.y + 24)
    if livre > 150:
        desenha_silhueta(t, d["uf"], cor,
                         (t.m, t.y + 24, L - t.m, t.y + 24 + livre), opacidade=40)

    t.rodape("kvgs.github.io/senado-2026", "@CANDIDATURASENADO", cor, APAGADO)
    t.salvar(f"{pasta(d['uf'], p['nome'], p['numero'])}/{i}-fecho.png")


LEGENDA = """# {numero} {nome} ({sigla}) — {uf_nome}

{n_slides} slides: capa, um slide por tema COM conteúdo, um slide juntando todos
os temas sem conteúdo, e o fecho com a legenda das tarjas.
Gerado por `python gerar_artes_candidatura.py --uf {uf} --numero {numero}`.

---

## Legenda

**O que já foi levantado sobre {nome} ({sigla}), tema a tema.**

São {n_temas} temas. Em cada slide a tarja diz **de quem é a proposta** — da
candidatura ou do partido — ou o que ainda não há.

Neste levantamento: **{n_proprias} tema(s) com proposta própria**, **{n_partido} com
proposta do partido** e **{n_vazios} sem conteúdo**.

⚠️ Estes três números são sobre **o nosso levantamento**, e não sobre a
candidatura. Tema sem conteúdo aqui quer dizer que nós ainda não localizamos ou
ainda não trabalhamos aquele cruzamento — não que a pessoa não tenha o que dizer.

Cada informação traz a citação literal do documento de onde saiu, o selo de
origem e se já passou por revisão humana. No site tem a página completa, com o
link de cada fonte.

🔗 kvgs.github.io/senado-2026

{hashtags}

---

## O que a arte NÃO faz

- **Não ordena candidaturas.** Este carrossel é de uma candidatura só, e a ordem
  entre elas, quando houver, é a do número de urna.
- **Não conta ponto.** O placar da capa compara a candidatura com ela mesma nos
  dez temas; comparar entre pessoas mediria verba de campanha e cobertura de
  imprensa, não qualidade de candidatura.
- **Não promete nada** sobre próximos posts.

## Números desta candidatura

- {n_proprias} proposta(s) própria(s), {n_partido} do partido, {n_vazios} sem conteúdo
- Cor e silhueta: {cor_de}
"""


def escreve_legenda(d: dict, p: dict, n_slides: int, cor_de: str) -> None:
    tags = ["#eleições2026", "#senado", "#" + slug(d["uf_nome"]).replace("-", ""),
            "#" + slug(p["nome"]).replace("-", ""), "#" + p["sigla"].lower(),
            "#dadosabertos", "#votoconsciente", "#transparência"]
    txt = LEGENDA.format(
        numero=p["numero"], nome=p["nome"], sigla=p["sigla"], uf=d["uf"],
        uf_nome=d["uf_nome"], n_slides=n_slides, n_temas=d["n_temas"],
        n_proprias=p["n_proprias"], n_partido=p["n_partido"],
        n_vazios=p["n_vazios"], cor_de=cor_de, hashtags=" ".join(tags))
    alvo = _ar.SAIDA / pasta(d["uf"], p["nome"], p["numero"]) / "LEGENDA.md"
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(txt, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", required=True)
    ap.add_argument("--numero")
    ap.add_argument("--todos", action="store_true")
    a = ap.parse_args()
    uf = a.uf.upper()
    if not a.numero and not a.todos:
        raise SystemExit("passe --numero NNN ou --todos")
    if uf not in PALETA:
        raise SystemExit(
            f"PAROU: {uf} nao tem cor definida em PALETA. A cor de cada estado sai "
            "da bandeira dele e precisa ser escolhida e conferida no contraste — "
            "inventar uma aqui seria criar identidade visual para um lugar sem "
            "ninguem ter decidido. Acrescente a linha de {uf} em PALETA.")
    cor = PALETA[uf]["cor"]

    d = medir(uf, None if a.todos else a.numero)
    for p in d["gente"]:
        # Tema com conteudo ganha slide proprio; os vazios se juntam num so.
        com = [(k, b) for k, b in enumerate(p["blocos"], 1)
               if b["estado"] in ("A", "B")]
        vazios = [b for b in p["blocos"] if b["estado"] not in ("A", "B")]
        n_slides = 1 + len(com) + (1 if vazios else 0) + 1
        i = 1
        arte_capa(d, p, cor, i, n_slides)
        for k, b in com:
            i += 1
            arte_tema(d, p, b, cor, i, n_slides, k)
        if vazios:
            i += 1
            arte_sem_conteudo(d, p, vazios, cor, i, n_slides)
        arte_fecho(d, p, cor, n_slides, n_slides)
        escreve_legenda(d, p, n_slides, PALETA[uf]["de"])
        print(f"  {pasta(uf, p['nome'], p['numero'])}/  ({n_slides} slides · "
              f"{p['n_proprias']} próprias, {p['n_partido']} do partido, "
              f"{p['n_vazios']} sem conteúdo, num slide só)")


if __name__ == "__main__":
    main()
