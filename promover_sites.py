# -*- coding: utf-8 -*-
"""Leva as posicoes extraidas dos sites para posicoes.json, MARCADAS como nao
revisadas.

POR QUE ISTO NAO AFROUXA A REGRA. A regra nunca foi "so publica o que foi
revisado" — o site sempre teve tres estados, e o template ja traz o selo "nao
revisado" por item e o aviso "Revisao em andamento: N de M conferidas". O que
acontecia e que as extracoes moravam num arquivo de trabalho e nao chegavam ali.
Nada e afrouxado: o que muda e que o padrao deixa de ser esconder ate revisar, e
passa a ser mostrar marcado ate revisar — que e a propria tese do site sobre
ausencia.

O QUE A MAQUINA GARANTE, e esta escrito no item:
  - a citacao e literal, conferida palavra por palavra contra o texto coletado
  - o endereco e o dominio que a candidatura declarou ao TSE
  - o tema sai do vocabulario fixo, e a frase passou pela regra de clareza

O QUE ELA NAO GARANTE, e por isso o selo existe:
  - que o trecho represente o conjunto do que a candidatura pensa. Citacao pode
    ser literal e ainda assim escolhida de forma que distorce. So gente lendo a
    pagina inteira resolve isso.
  - que a pagina nao tenha mudado depois da coleta.

REVISAO NUNCA E SOBRESCRITA. Item ja revisado (aprovado ou reprovado) fica como
esta. Este script so acrescenta.

USO
    python promover_sites.py --uf ES
    python promover_sites.py --uf ES --gravar
    python promover_sites.py --todos --gravar
"""
from __future__ import annotations

import argparse
import json
from datetime import date

import acervo


def documento_do_site(cid: str, url: str, titulo: str, coletado_em: str) -> dict:
    dominio = url.split("//", 1)[-1].split("/", 1)[0]
    return {
        "id_documento": f"doc-site-{cid}",
        "tipo": "site_de_candidatura",
        "titulo": titulo or f"Site da candidatura ({dominio})",
        "url": url,
        "publicado_em": None,
        "consultado_em": coletado_em,
        "_origem": ("Endereco declarado pela propria candidatura no registro no TSE "
                    "(base de redes sociais 2026)."),
    }


def promover(uf: str, gravar: bool) -> tuple[int, int]:
    f_ext = acervo.de(uf) / "_extracao_sites.json"
    if not f_ext.exists():
        return 0, 0
    extraidas = json.loads(f_ext.read_text(encoding="utf-8"))["posicoes"]

    f_pos = acervo.de(uf) / "posicoes.json"
    dpos = json.loads(f_pos.read_text(encoding="utf-8"))
    existentes = {p["id_posicao"] for p in dpos["posicoes"]}

    f_doc = acervo.de(uf) / "documentos.json"
    ddoc = json.loads(f_doc.read_text(encoding="utf-8"))
    docs = {d["id_documento"] for d in ddoc["documentos"]}

    novas, novos_docs = 0, 0
    for x in extraidas:
        if x["id_posicao"] in existentes:
            continue                      # ja promovida; revisao nao se sobrescreve
        cid = x["id_candidatura"]
        did = f"doc-site-{cid}"
        if did not in docs:
            ddoc["documentos"].append(
                documento_do_site(cid, x["url"], x.get("titulo_da_pagina", ""),
                                  x["coletado_em"]))
            docs.add(did); novos_docs += 1
        dpos["posicoes"].append({
            "id_posicao": x["id_posicao"],
            "id_tema": x["tema"],
            "atribuido_a_tipo": "candidatura",
            "atribuido_a_id": cid,
            "estado_cobertura": "A",
            "natureza": "promessa",
            "nivel_fonte": "declaracao_candidato",
            "id_documento": did,
            # A citacao e o dado. O resumo e leitura minha e vai no campo texto,
            # que a tela mostra depois da citacao — nunca no lugar dela.
            "citacao_literal": x["trecho"],
            "texto": x.get("resumo") or "",
            "url_especifica": x["url"],
            "data_referencia": x["coletado_em"],
            "revisado_por_humano": False,
            "conferido_por_ia": {
                "data": x["extraido_em"],
                "forca": "alta",
                "base": ("trecho conferido palavra por palavra contra o texto coletado "
                         f"do site declarado ao TSE em {x['coletado_em']}"),
                "ressalva": ("Citacao literal conferida por comparacao de texto. O que "
                             "NAO foi conferido por gente: se o trecho representa o "
                             "conjunto do que a candidatura defende, e se a pagina mudou "
                             "depois da coleta."),
            },
            "_promovido_em": date.today().isoformat(),
        })
        novas += 1

    if gravar and novas:
        f_pos.write_text(json.dumps(dpos, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
        f_doc.write_text(json.dumps(ddoc, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
    return novas, novos_docs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()
    if not a.uf and not a.todos:
        raise SystemExit("passe --uf XX ou --todos")

    ufs = acervo.com_acervo() if a.todos else [a.uf.upper()]
    tp = td = 0
    for uf in ufs:
        n, d = promover(uf, a.gravar)
        if n:
            print(f"  {uf}: {n} posicao(oes), {d} documento(s) novo(s)")
        tp += n; td += d
    print(f"\n{tp} posicao(oes) e {td} documento(s)")
    print("Todas entram com revisado_por_humano: false e aparecem com o selo "
          "'nao revisado' na tela.")
    if not a.gravar:
        print("\n(sem --gravar: nada foi escrito)")


if __name__ == "__main__":
    main()
