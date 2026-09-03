# -*- coding: utf-8 -*-
"""Propaga a conferencia humana entre linhas que citam O MESMO TRECHO.

O PROBLEMA QUE ISTO RESOLVE. Um programa de partido nacional rende uma linha por
candidatura daquele partido, em todos os estados. O programa da Democracia Crista
tem 288 linhas no acervo e apenas 16 TEXTOS distintos. Quem revisa a 17a linha
esta lendo, palavra por palavra, o mesmo trecho do mesmo PDF que ja leu — 271
vezes. No acervo inteiro sao 2.473 linhas de programa partidario para 251 textos.

O QUE A CONFERENCIA DE UMA LINHA DE PROGRAMA CONFERE, e o que a tela de revisao
pede para aquele selo: se a REDACAO bate com o documento. Esse trabalho e
identico nas 288 linhas — mesmo arquivo, mesma frase, mesmo tema. O que muda de
uma linha para a outra e a candidatura, e a ligacao candidatura -> partido vem do
registro no TSE, que o validar.py ja confere (R1).

O QUE ISTO NAO FAZ, e a fronteira importa:
  - So programa de partido (doc-programa*). Site de candidatura e registro
    legislativo sao de uma pessoa so por natureza: cada um exige leitura propria,
    e propagar ali seria dizer que se leu o que nao se leu.
  - Nunca sobrescreve decisao existente. Linha com "corrigir" ou "remover" fica
    como esta.
  - Se ALGUEM marcou "corrigir" ou "remover" em qualquer linha daquele texto, o
    grupo inteiro e pulado e aparece no relatorio. Um trecho questionado num
    estado nao vira aprovado nos outros por tabela — seria usar a propagacao para
    apagar uma duvida.

CADA LINHA HERDADA DIZ DE ONDE VEIO: a candidatura, o estado, a data e quem
conferiu. Sem isso o selo afirmaria que uma pessoa leu aquela linha, e ninguem
leu — leu o trecho.

USO
    python propagar_conferencia.py
    python propagar_conferencia.py --gravar
"""
from __future__ import annotations

import argparse
import collections
import json
from datetime import date

import acervo

PREFIXO_DOC = "doc-programa"
DECIDIDOS = ("confere", "corrigir", "remover")


def chave(p: dict) -> tuple:
    return (p.get("id_documento"), p.get("citacao_literal") or "", p.get("id_tema"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gravar", action="store_true")
    ap.add_argument("--documento", help="limita a um documento, ex: doc-programa-nacional-dc")
    a = ap.parse_args()

    # 1. varre o acervo inteiro e agrupa por trecho
    grupos: dict[tuple, list] = collections.defaultdict(list)
    for uf in acervo.com_acervo():
        for p in acervo.ler("posicoes.json", uf)["posicoes"]:
            d = p.get("id_documento") or ""
            if not d.startswith(PREFIXO_DOC):
                continue
            if a.documento and d != a.documento:
                continue
            grupos[chave(p)].append((uf, p))

    herdar: dict[str, list] = collections.defaultdict(list)   # uf -> [(id_posicao, fonte)]
    conflitos, sem_fonte = [], 0

    for k, linhas in grupos.items():
        decisoes = [(uf, p, (p.get("revisao") or {}).get("resultado")) for uf, p in linhas]
        questionadas = [(uf, p) for uf, p, r in decisoes if r in ("corrigir", "remover")]
        if questionadas:
            conflitos.append((k, questionadas))
            continue
        # a fonte e a conferencia mais ANTIGA: e a que uma pessoa fez de fato,
        # olhando o documento pela primeira vez
        fontes = sorted(
            [(uf, p) for uf, p, r in decisoes
             if r == "confere" and p.get("revisado_por_humano")],
            key=lambda x: (x[1].get("revisao") or {}).get("em") or "9999")
        if not fontes:
            sem_fonte += 1
            continue
        uf_f, p_f = fontes[0]
        for uf, p in linhas:
            if p.get("revisado_por_humano") or (p.get("revisao") or {}).get("resultado") in DECIDIDOS:
                continue
            herdar[uf].append((p["id_posicao"], (uf_f, p_f)))

    total = sum(len(v) for v in herdar.values())
    print(f"{len(grupos)} trecho(s) distinto(s) de programa de partido")
    print(f"{total} linha(s) herdariam a conferencia de outra candidatura")
    print(f"{sem_fonte} trecho(s) ainda sem nenhuma conferencia humana — ficam na fila")
    if conflitos:
        print(f"\n{len(conflitos)} trecho(s) PULADO(S): alguem marcou corrigir/remover neles.")
        for k, qs in conflitos[:10]:
            uf, p = qs[0]
            r = (p.get("revisao") or {}).get("resultado")
            print(f"   [{uf}] {k[0]} · {k[2]} — {r}: {(p.get('revisao') or {}).get('nota') or '(sem nota)'}")
            print(f"        {k[1][:90]}")

    if not a.gravar:
        print("\n(sem --gravar: nada foi escrito)")
        return

    hoje = date.today().isoformat()
    for uf, itens in herdar.items():
        f = acervo.de(uf) / "posicoes.json"
        d = json.loads(f.read_text(encoding="utf-8"))
        por_id = {x["id_posicao"]: x for x in d["posicoes"]}
        for pid, (uf_f, p_f) in itens:
            p = por_id[pid]
            rev_f = p_f.get("revisao") or {}
            cid_f = p_f.get("id_candidatura_contexto") or p_f.get("atribuido_a_id")
            p["revisado_por_humano"] = True
            p["revisao"] = {
                "em": rev_f.get("em") or hoje,
                "resultado": "confere",
                "nota": "",
                "por_quem": rev_f.get("por_quem") or p_f.get("revisado_por"),
                "_herdada_de": {
                    "id_posicao": p_f["id_posicao"],
                    "uf": uf_f,
                    "id_candidatura": cid_f,
                    "conferida_em": rev_f.get("em"),
                },
                "_por_que": (
                    "Mesmo trecho, do mesmo documento, no mesmo tema. O que a "
                    "conferencia de uma linha de programa de partido verifica e se "
                    "a redacao bate com o documento, e isso foi verificado uma vez "
                    "por uma pessoa. A propagacao foi autorizada pela curadoria em "
                    + hoje + "."),
                "_propagada_em": hoje,
            }
        f.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"  {uf}: {len(itens)} linha(s)")
    print(f"\n{total} linha(s) gravada(s) como conferidas, cada uma dizendo de onde herdou")


if __name__ == "__main__":
    main()
