# -*- coding: utf-8 -*-
"""Valida e grava posicoes extraidas do material coletado nos sites.

A TRAVA CENTRAL: CITACAO TEM DE SER LITERAL. Cada posicao carrega um trecho, e o
script confere que esse trecho existe PALAVRA POR PALAVRA no texto coletado
daquela URL. Se nao existir, a posicao e recusada e nada e gravado.

Isso nao e zelo: numa revisao anterior, "controle estatal dos precos" tinha
virado "congelamento de precos" — outra politica, frase parecida. Conferir a
mao nao pega isso de forma confiavel em centenas de itens. Conferir por
comparacao de texto pega sempre.

O QUE A TRAVA NAO GARANTE. Que a citacao esteja no contexto certo, que o tema
escolhido seja o melhor, ou que o trecho represente o que a candidatura pensa.
Isso e julgamento, e vai para a tela de revisao. A trava garante uma coisa so, e
e a que a maquina erra sozinha: que ninguem seja citado dizendo o que nao disse.

SELO. Site declarado pela candidatura = declaracao do candidato (roxo). Prova
que publicou, nunca que e verdade. Nenhuma posicao daqui entra no site sem
alguem ter aberto a fonte.

USO
    python extrair_posicoes.py --uf ES --arquivo extracao-es.json
    python extrair_posicoes.py --uf ES --arquivo extracao-es.json --gravar
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import date

import acervo


def normal(s: str) -> str:
    """Forma para comparar: sem acento, minusculas, espaco colapsado. O texto da
    pagina passa por HTML e pode ter espaco duplo ou nao-quebravel onde a leitura
    ve um espaco so — comparar cru geraria falso negativo."""
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def carregar_coleta(uf: str) -> dict[str, dict]:
    f = acervo.de(uf) / "_coleta_sites.json"
    if not f.exists():
        raise SystemExit(f"nao ha coleta de sites em {uf}. Rode coletar_sites.py --uf {uf}")
    return {r["id_candidatura"]: r for r in json.loads(f.read_text(encoding="utf-8"))["registros"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", required=True)
    ap.add_argument("--arquivo", required=True, help="JSON com as posicoes propostas")
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()
    uf = a.uf.upper()

    coleta = carregar_coleta(uf)
    temas = {t["id_tema"]: t["nome"] for t in acervo.ler("referencia.json")["temas"]}
    cands = {c["id_candidatura"]: c for c in acervo.ler("candidaturas.json", uf)["candidaturas"]}

    propostas = json.loads(open(a.arquivo, encoding="utf-8").read())
    if isinstance(propostas, dict):
        propostas = propostas["posicoes"]

    aceitas, recusadas = [], []
    for p in propostas:
        cid, url, trecho = p.get("id_candidatura"), p.get("url"), p.get("trecho") or ""
        erro = None

        if cid not in cands:
            erro = f"id_candidatura nao existe em {uf}"
        elif cid not in coleta:
            erro = "esta candidatura nao tem coleta de site"
        elif p.get("tema") not in temas:
            erro = f"tema {p.get('tema')!r} nao esta na referencia"
        elif len(trecho.strip()) < 25:
            erro = f"trecho curto demais ({len(trecho.strip())} caracteres): nao sustenta nada"
        else:
            pagina = next((x for x in coleta[cid]["paginas"] if x["url"] == url), None)
            if pagina is None:
                urls = [x["url"] for x in coleta[cid]["paginas"]]
                erro = f"url nao esta entre as paginas coletadas desta candidatura: {urls}"
            elif normal(trecho) not in normal(pagina["texto"]):
                # A TRAVA. Nao ha excecao, nem parametro para desligar.
                erro = "TRECHO NAO E LITERAL: nao aparece palavra por palavra no texto coletado"

        if erro:
            recusadas.append((p, erro))
            continue

        aceitas.append({
            "id_posicao": f"pos-{cid}-site-{len(aceitas) + 1:03d}",
            "id_candidatura": cid,
            "atribuido_a_id": cid,
            "atribuido_a_tipo": "candidatura",
            "tema": p["tema"],
            "trecho": trecho.strip(),
            "resumo": (p.get("resumo") or "").strip() or None,
            "url": url,
            "titulo_da_pagina": pagina["titulo"],
            "selo": "declaracao_do_candidato",
            "estado_cobertura": "A",
            "coletado_em": coleta[cid]["coletado_em"],
            "extraido_em": date.today().isoformat(),
            "extraido_por": "modelo",
            "revisado_por_humano": False,
            "_nota_selo": ("Declaracao da candidatura no site que ela declarou ao TSE. Prova "
                           "que publicou isto, nao que seja verdade."),
            "_como_conferir": ("Abra a URL e procure o trecho. Ele foi conferido palavra por "
                               "palavra contra o texto coletado em " + coleta[cid]["coletado_em"] +
                               "; se a pagina mudou desde entao, a conferencia manda."),
        })

    print(f"{uf}: {len(aceitas)} aceita(s), {len(recusadas)} recusada(s)")
    for p, e in recusadas:
        print(f"  RECUSADA  {p.get('id_candidatura')} — {e}")
        print(f"            trecho: {(p.get('trecho') or '')[:90]!r}")
    por_tema: dict[str, int] = {}
    for x in aceitas:
        por_tema[x["tema"]] = por_tema.get(x["tema"], 0) + 1
    for t, n in sorted(por_tema.items(), key=lambda kv: -kv[1]):
        print(f"    {n:3}  {temas[t]}")

    if not a.gravar:
        print("\n(sem --gravar: nada foi escrito)")
        return
    if recusadas:
        raise SystemExit("\nPAROU: ha posicao recusada. Corrija ou remova antes de gravar — "
                         "gravar parte agora deixaria a extracao pela metade sem registro disso.")

    f = acervo.de(uf) / "_extracao_sites.json"
    f.write_text(json.dumps({"posicoes": aceitas}, ensure_ascii=False, indent=2) + "\n",
                 encoding="utf-8")
    print(f"\ngravado: {f}")


if __name__ == "__main__":
    main()
