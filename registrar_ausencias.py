# -*- coding: utf-8 -*-
"""Registra estado D — "nao localizamos fonte" — onde a busca REALMENTE foi feita.

O PROBLEMA QUE ISTO RESOLVE. Tema sem nenhum registro no acervo aparecia no site e
na arte como "este cruzamento ainda nao foi trabalhado" — a frase mais fraca das
cinco, escolhida por OMISSAO e nao por medicao. Para a maioria das candidaturas
ela e falsa: o programa nacional do partido foi lido inteiro, e o site declarado,
quando existe, tambem. O que houve foi busca sem achado, e isso tem nome no modelo
do projeto: estado D.

A DIFERENCA IMPORTA PORQUE MUDA DE QUEM E A DIVIDA. "Ainda nao trabalhado" e uma
divida nossa: falta a gente ir olhar. "Nao localizamos" e uma constatacao sobre a
fonte: olhamos e nao havia. Sem essa distincao, a curadoria nao pode cobrar a
candidatura sobre o que falta — porque nao sabe se a lacuna e dela ou nossa.

O ESCOPO E MEDIDO, NAO SUPOSTO. Cada registro diz exatamente o que foi lido: o
programa do partido, com a URL e a data da extracao, e o site declarado ao TSE,
com o tamanho do texto coletado e a data. Escrever "buscamos" sem dizer onde seria
a mesma omissao com outra roupa.

QUEM NAO TEM FONTE LIDA NAO GANHA REGISTRO. Se o programa do partido foi recusado
(dados/programas-recusados.json) e nao ha site coletado, entao nao houve busca em
lugar nenhum, e dizer "nao localizamos" seria mentir sobre nos. Esses casos ficam
como estao, e o script os LISTA em vez de deixa-los em silencio.

NAO SOBRESCREVE registro existente. Onde a curadoria ja escreveu um motivo
especifico — e ha casos em que o especifico e muito melhor que o geral, como o
site que cita obras do mandato passado —, o registro fica como esta.

USO
    python registrar_ausencias.py --uf AC
    python registrar_ausencias.py --uf AC --gravar
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import pathlib
from datetime import date

import acervo

RAIZ = pathlib.Path(__file__).resolve().parent
HOJE = date.today().isoformat()


def mil(n: int) -> str:
    """33722 -> 33.722. Numero de cinco digitos corrido nao se le."""
    return f"{n:,}".replace(",", ".")


def plural(n: int, um: str, muitos: str) -> str:
    return f"{n} {um if n == 1 else muitos}"


# A REDACAO E DA CURADORIA, palavra por palavra, com um "social" que estava
# truncado. O "AINDA" em maiuscula e dela e muda o sentido da frase: diz que nao
# coletar rede social e decisao de hoje, e nao regra permanente — o que importa
# porque ha candidatura cujo UNICO canal declarado ao TSE e o Instagram.
def escopo_da_busca(lidas: list[str], nao_lidas: list[str]) -> str:
    txt = "Foram lidos: " + "; ".join(lidas) + "."
    if nao_lidas:
        txt += (" NÃO foram lidos, e são canais que a candidatura declarou ao TSE: "
                + "; ".join(nao_lidas) + ". O projeto AINDA não coleta rede social.")
    return txt


def fontes_lidas(uf: str) -> tuple[dict, dict, set]:
    """(programa por partido, site por candidatura, partidos recusados)."""
    prog = {}
    for f in glob.glob(str(RAIZ / "extracoes" / "partido-*.json")):
        d = json.load(open(f, encoding="utf-8"))
        sigla = os.path.basename(f)[len("partido-"):-len(".json")]
        # Data da extracao: a nota traz "consultada em DD/mmm/AAAA" em varias.
        prog[sigla] = {"url": d.get("url", ""), "titulo": d.get("titulo", ""),
                       "trechos": len(d.get("posicoes") or []),
                       "nota": (d.get("nota") or "")[:200]}
    sites = {}
    p = RAIZ / "dados" / uf.lower() / "_coleta_sites.json"
    if p.exists():
        for r in json.loads(p.read_text(encoding="utf-8"))["registros"]:
            paginas = [x for x in (r.get("paginas") or [])
                       if x.get("caracteres_de_texto")]
            if paginas:
                sites[r["id_candidatura"]] = {
                    "url": r.get("url_fora_do_registro") or r.get("url_declarada"),
                    "caracteres": sum(x["caracteres_de_texto"] for x in paginas),
                    "paginas": len(paginas), "em": r["coletado_em"]}
    rec = set()
    pr = RAIZ / "dados" / "programas-recusados.json"
    if pr.exists():
        rec = {x["id_partido"]
               for x in json.loads(pr.read_text(encoding="utf-8"))["recusados"]}
    return prog, sites, rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", required=True)
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()
    uf = a.uf.upper()
    dpast = acervo.exige(uf)

    cands = acervo.ler("candidaturas.json", uf)["candidaturas"]
    arq = dpast / "posicoes.json"
    dpos = json.loads(arq.read_text(encoding="utf-8"))
    vivas = [p for p in dpos["posicoes"]
             if (p.get("revisao") or {}).get("resultado") not in ("remover", "corrigir")]
    ja = {p["id_posicao"] for p in dpos["posicoes"]}
    temas = acervo.ler("referencia.json")["temas"]
    siglas = {p["id_partido"]: p["sigla"]
              for p in acervo.ler("referencia.json")["partidos"]}
    prog, sites, recusados = fontes_lidas(uf)

    novos, sem_fonte = [], []
    for c in sorted(cands, key=lambda c: int(c["numero_urna"])):
        cid, part = c["id_candidatura"], c["id_partido"]
        lidas, escopo = [], []
        pr = prog.get(part)
        if pr and part not in recusados:
            lidas.append("programa")
            # SEM URL AQUI. O endereco pertence ao registro do documento, que o
            # site ja mostra com link. Colado neste texto ele envelhece sozinho:
            # o "link" do programa do PL e https://www.in.gov.br/, a home da
            # Imprensa Nacional, que a revisao humana ja pegou como errada — e
            # este campo passaria a publicar o erro num segundo lugar.
            escopo.append(f"o programa nacional do {siglas.get(part, part)}, lido "
                          "por inteiro — rendeu "
                          + plural(pr["trechos"], "trecho", "trechos"))
        s = sites.get(cid)
        if s:
            lidas.append("site")
            # O TSE devolve o endereco em caixa alta; minusculo e como se le.
            end = (s["url"] or "").lower().replace("https://", "").replace("http://", "")
            escopo.append(f"o site da candidatura ({end}), "
                          + plural(s["paginas"], "página", "páginas")
                          + f" e {mil(s['caracteres'])} caracteres, "
                          f"coletado em {s['em']}")
        # O QUE FOI DECLARADO E NAO FOI LIDO TAMBEM E ESCOPO. A candidatura
        # declarou perfis ao TSE; o projeto nao coleta rede social — post nao e
        # documento de campanha e muda de hora em hora. Mas calar isso faz o
        # registro dizer "procuramos em tudo" quando havia canal oficial por ler.
        # A curadoria apontou: "outro canal oficial dele seria o instagram".
        ct = c.get("contato") or {}
        nao_lidas = []
        if ct.get("instagram"):
            nao_lidas.append(f"o Instagram {ct['instagram']}")
        for u in (ct.get("redes") or []):
            baixo = u.lower()
            if "instagram" in baixo or u == ct.get("site_do_partido"):
                continue
            nao_lidas.append(u.lower().replace("https://", "").replace("http://", ""))

        if not lidas:
            sem_fonte.append((c["numero_urna"], c["pessoa"]["nome_urna"],
                              siglas.get(part, part),
                              "programa do partido recusado" if part in recusados
                              else "partido sem programa extraído"))
            continue

        for t in temas:
            tid = t["id_tema"]
            if any((p.get("id_candidatura_contexto") or p.get("atribuido_a_id")) == cid
                   and p.get("id_tema") == tid for p in vivas):
                continue
            idp = f"pos-{cid[4:]}-busca-{tid}" if cid.startswith("sen-") else \
                  f"pos-{cid}-busca-{tid}"
            idp = f"pos-{cid}-busca-{tid}".replace("pos-sen-", "pos-sen-")
            if idp in ja:
                continue          # registro existente nao e sobrescrito
            novos.append({
                "id_posicao": idp,
                "id_candidatura_contexto": cid,
                "id_tema": tid,
                "atribuido_a_tipo": "candidatura",
                "atribuido_a_id": cid,
                "estado_cobertura": "D",
                "natureza": "ausencia",
                "nivel_fonte": None,
                "citacao_literal": "",
                "texto": (f"Não localizamos proposta sobre {t['nome'].lower()}. "
                          "Isto é uma afirmação sobre a nossa busca: as fontes "
                          "abaixo foram lidas e nenhuma delas trouxe posição "
                          "sobre este tema."),
                "busca_realizada_em": HOJE,
                "escopo_da_busca": escopo_da_busca(escopo, nao_lidas),
                "revisado_por_humano": False,
                "_gerado_por": "registrar_ausencias.py",
            })

    print(f"{uf}: {len(novos)} registro(s) D a criar")
    por_cand = {}
    for r in novos:
        por_cand.setdefault(r["id_candidatura_contexto"], []).append(r["id_tema"])
    nomes = {c["id_candidatura"]: (c["numero_urna"], c["pessoa"]["nome_urna"])
             for c in cands}
    for cid, tids in por_cand.items():
        n, nome = nomes[cid]
        print(f"  {n:>4} {nome[:26]:26} {len(tids)} tema(s): {' '.join(tids)}")
    if sem_fonte:
        print(f"\n{len(sem_fonte)} candidatura(s) SEM NENHUMA FONTE LIDA — nao "
              "recebem registro D, porque dizer 'nao localizamos' exigiria ter "
              "procurado em algum lugar:")
        for n, nome, sigla, motivo in sem_fonte:
            print(f"  {n:>4} {nome[:26]:26} {sigla:14} {motivo}")

    if not a.gravar:
        print("\n(sem --gravar: nada escrito)")
        return 0
    dpos["posicoes"].extend(novos)
    arq.write_text(json.dumps(dpos, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print(f"\ngravado: {arq}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
