# -*- coding: utf-8 -*-
"""Gera analise/index.html — o que os dados dizem sobre a propria eleicao.

A UNIDADE DE ANALISE NUNCA E A PESSOA. Esta pagina conta sobre temas, fontes e o
proprio registro. Contar por candidatura seria ranquear com outro nome, que e o
que o resto do site existe para nao fazer — e a pagina escreve isso, porque um
leitor que ve numeros presume ranking ate que se diga o contrario.

TODO NUMERO SAI DO ACERVO, na hora. Nada aqui e digitado: se uma posicao entrar
ou sair, a proxima geracao muda o grafico. Numero escrito a mao em pagina de
analise envelhece calado, que e o pior jeito de errar.

A COR FOI VALIDADA, e nao escolhida no olho. O ciano do site (#0C6C8F) reprova
no piso de croma a esta espessura de marca — le como cinza. As series usam o
degrau mais proximo que passa nas cinco checagens, e o tema escuro tem degraus
proprios: a banda de luminosidade do escuro e mais estreita E mais escura, entao
nao e o claro invertido.

USO
    python gerar_analise.py
"""
from __future__ import annotations

import collections
import json
import pathlib
import re

import acervo

AQUI = pathlib.Path(__file__).resolve().parent
SAIDA = AQUI / "analise"

# Elementos que o navegador trata como inline. Altura declarada neles e ignorada.
INLINE = ("span", "i", "b", "em", "a", "label", "code")


def estilo_base() -> str:
    """Mesmo recorte que a pagina inicial faz: tokens, fontes e reset do template
    do estado. Uma fonte de verdade para a paleta; duas divergem."""
    t = (AQUI / "_template_site.html").read_text(encoding="utf-8")
    i = t.find("  :root{")
    j = t.find("-webkit-font-smoothing:antialiased}")
    if i < 0 or j < 0:
        raise SystemExit("nao achei o bloco de estilo base em _template_site.html")
    return t[i:t.index("}", j) + 1].replace("{{RAIZ}}", "../")


def conferir_layout(css: str, html: str) -> None:
    """Pega a classe de erro que o validador de cor nao ve: elemento inline com
    altura declarada. Uma barra assim ignora a altura e o filho vaza da caixa —
    aconteceu, e so apareceu quando alguem olhou a pagina renderizada.

    Precisa cruzar CSS e HTML: seletor de classe nao diz qual e a tag."""
    com_altura = set()
    for sel, corpo in re.findall(r"([^{}]+)\{([^}]*)\}", css):
        if ("height" not in corpo and "width" not in corpo) or "display:" in corpo:
            continue
        if "position:absolute" in corpo:
            continue
        for cls in re.findall(r"\.([a-zA-Z][\w-]*)", sel):
            com_altura.add(cls)
    ruins = set()
    for tag, attr in re.findall(r"<(" + "|".join(INLINE) + r")\b([^>]*)>", html):
        m = re.search(r'class="([^"]*)"', attr)
        if not m:
            continue
        for cls in m.group(1).split():
            if cls in com_altura:
                ruins.add(f'<{tag} class="{cls}">')
    if ruins:
        raise SystemExit(
            "PAROU: elemento inline com altura declarada — o navegador ignora a "
            "altura e o conteudo vaza da caixa." + chr(10)
            + chr(10).join("  " + r for r in sorted(ruins))
            + chr(10) + "Ponha display:block (ou inline-block) na regra.")


def medir() -> dict:
    """Todos os numeros, do acervo. Posicao reprovada na revisao nao conta."""
    ref = acervo.ler("referencia.json")
    nomes = {t["id_tema"]: t["nome"] for t in ref["temas"]}
    A, B = collections.Counter(), collections.Counter()
    cob, lixo = {}, collections.Counter()
    mand = {"com": 0, "com_site": 0, "sem": 0, "sem_site": 0}
    urls = 0
    for e in acervo.ler("estados.json")["estados"]:
        uf = e["uf"]
        pos = [p for p in acervo.ler("posicoes.json", uf)["posicoes"]
               if (p.get("revisao") or {}).get("resultado") not in ("remover", "corrigir")]
        for p in pos:
            (A if p.get("estado_cobertura") == "A" else B)[p["id_tema"]] += 1
        cands = acervo.ler("candidaturas.json", uf)["candidaturas"]
        com = {p.get("id_candidatura_contexto") or p.get("atribuido_a_id") for p in pos}
        n = sum(1 for c in cands if c["id_candidatura"] in com)
        cob[uf] = {"nome": e["nome"], "com": n, "total": len(cands),
                   "pct": round(100 * n / len(cands))}
        for c in cands:
            ct = c.get("contato") or {}
            tem = bool(ct.get("site"))
            chave = "com" if c.get("situacao_parlamentar") else "sem"
            mand[chave] += 1
            mand[chave + "_site"] += tem
            urls += len(ct.get("redes") or []) + len(c.get("_conferir_contato") or [])
            for p in (c.get("_conferir_contato") or []):
                lixo[p.split("— ")[-1].split(",")[0]] += 1
    sa, sb = sum(A.values()), sum(B.values())
    temas = [{"nome": nomes[t], "pa": round(100 * A.get(t, 0) / sa, 1),
              "pb": round(100 * B.get(t, 0) / sb, 1)} for t in nomes]
    return {"temas": sorted(temas, key=lambda t: t["pb"] - t["pa"], reverse=True),
            "totalA": sa, "totalB": sb, "cobertura": cob,
            "lixo": dict(lixo.most_common()), "urls": urls, "mandato": mand}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    d = medir()
    mapa = json.loads((AQUI / "dados" / "mapa-uf.json").read_text(encoding="utf-8"))
    ref = acervo.ler("referencia.json")
    ct = ref.get("contato") or {}
    temas, cob, lixo = d["temas"], d["cobertura"], d["lixo"]
    tot_lixo = sum(lixo.values())

    # --- 1. dumbbell ------------------------------------------------------
    LARG, ESQ, DIR = 760, 250, 30
    faixa = LARG - ESQ - DIR
    maxp = max(max(t["pa"], t["pb"]) for t in temas)
    def x(p): return ESQ + (p / maxp) * faixa
    ALT1 = 30 + len(temas) * 44 + 4
    grade = "".join(
        f'<line class="gr" x1="{x(v):.1f}" y1="18" x2="{x(v):.1f}" y2="{ALT1-28}"/>'
        f'<text class="eixo" x="{x(v):.1f}" y="{ALT1-10}" text-anchor="middle">{v}%</text>'
        for v in (0, 10, 20, 30))
    pares = "".join(
        f'<g class="par" tabindex="0" role="listitem" aria-label="{esc(t["nome"])}: '
        f'{t["pa"]}% do que as candidaturas dizem, {t["pb"]}% do que os programas de '
        f'partido dizem">'
        f'<text class="rot" x="{ESQ-14}" y="{30+i*44+4}" text-anchor="end">{esc(t["nome"])}</text>'
        f'<line class="haste" x1="{min(x(t["pa"]),x(t["pb"])):.1f}" y1="{30+i*44}" '
        f'x2="{max(x(t["pa"]),x(t["pb"])):.1f}" y2="{30+i*44}"/>'
        f'<circle class="mA" cx="{x(t["pa"]):.1f}" cy="{30+i*44}" r="6"/>'
        f'<circle class="mB" cx="{x(t["pb"]):.1f}" cy="{30+i*44}" r="6"/>'
        f'<title>{esc(t["nome"])} — candidatura {t["pa"]}% · partido {t["pb"]}%</title></g>'
        for i, t in enumerate(temas))

    # --- 2. mapa ----------------------------------------------------------
    def degrau(p): return 0 if p < 20 else 1 if p < 35 else 2 if p < 50 else 3 if p < 65 else 4
    paths = "".join(
        f'<path class="uf d{degrau(cob[uf]["pct"])}" d="{v}" tabindex="0" role="listitem" '
        f'aria-label="{esc(cob[uf]["nome"])}: {cob[uf]["com"]} de {cob[uf]["total"]} '
        f'candidaturas com alguma informação, {cob[uf]["pct"]} por cento">'
        f'<title>{esc(cob[uf]["nome"])} — {cob[uf]["com"]}/{cob[uf]["total"]} '
        f'({cob[uf]["pct"]}%)</title></path>'
        for uf, v in sorted(mapa["paths"].items()) if uf in cob)
    legenda = "".join(
        f'<span class="ch"><i class="d{i}"></i>{r}</span>'
        for r, i in (("menos de 20%", 0), ("20 a 34%", 1), ("35 a 49%", 2),
                     ("50 a 64%", 3), ("65% ou mais", 4)))
    tabela = "".join(
        f'<tr><th scope="row">{esc(v["nome"])}</th><td>{v["com"]}</td>'
        f'<td>{v["total"]}</td><td>{v["pct"]}%</td></tr>'
        for _, v in sorted(cob.items(), key=lambda kv: -kv[1]["pct"]))

    # --- 3. barras --------------------------------------------------------
    mx = max(lixo.values())
    barras = "".join(
        f'<div class="bl" tabindex="0" role="listitem" aria-label="{esc(k)}: {n} ocorrências">'
        f'<span class="bk">{esc(k)}</span>'
        f'<span class="bb"><i style="width:{100*n/mx:.1f}%"></i></span>'
        f'<span class="bn">{n}</span></div>' for k, n in lixo.items())

    m = d["mandato"]
    pm = round(100 * m["com_site"] / m["com"])
    ps = round(100 * m["sem_site"] / m["sem"])

    tpl = (AQUI / "_template_analise.html").read_text(encoding="utf-8")
    html = (tpl
            .replace("{{ESTILO_BASE}}", estilo_base())
            .replace("{{TOTAL_A}}", str(d["totalA"]))
            .replace("{{TOTAL_B}}", str(d["totalB"]))
            .replace("{{HABITACAO_B}}", str(next(t["pb"] for t in temas if t["nome"] == "Habitação")))
            .replace("{{HABITACAO_A}}", str(next(t["pa"] for t in temas if t["nome"] == "Habitação")))
            .replace("{{DUMBBELL}}", grade + pares)
            .replace("{{ALT1}}", str(ALT1))
            .replace("{{LARG1}}", str(LARG))
            .replace("{{MAPA}}", paths)
            .replace("{{VIEWBOX}}", mapa["viewBox"])
            .replace("{{TRANSFORM}}", mapa["transform"])
            .replace("{{LEGENDA}}", legenda)
            .replace("{{TABELA}}", tabela)
            .replace("{{COB_MIN}}", str(min(v["pct"] for v in cob.values())))
            .replace("{{COB_MAX}}", str(max(v["pct"] for v in cob.values())))
            .replace("{{BARRAS}}", barras)
            .replace("{{TOTAL_URLS}}", f'{d["urls"]:,}'.replace(",", "."))
            .replace("{{TOTAL_LIXO}}", str(tot_lixo))
            .replace("{{PCT_MANDATO}}", str(pm))
            .replace("{{PCT_SEM}}", str(ps))
            .replace("{{N_MANDATO}}", str(m["com"]))
            .replace("{{N_SEM}}", str(m["sem"]))
            .replace("{{EMAIL}}", ct.get("email", ""))
            .replace("{{INSTAGRAM_URL}}", ct.get("instagram_url", ""))
            .replace("{{INSTAGRAM}}", ct.get("instagram", "")))

    faltou = re.findall(r"\{\{[A-Z_0-9]+\}\}", html)
    if faltou:
        raise SystemExit(f"marcador nao substituido: {sorted(set(faltou))}")
    conferir_layout(html.split("</style>")[0], html)

    SAIDA.mkdir(exist_ok=True)
    (SAIDA / "index.html").write_text(html, encoding="utf-8")
    print(f"gerado: analise/index.html  ({len(html)/1024:.0f} KB)")
    print(f"  {len(temas)} temas · {len(cob)} estados · {tot_lixo} de {d['urls']} URLs com defeito")
    print(f"  todos os numeros medidos do acervo agora")


if __name__ == "__main__":
    main()
