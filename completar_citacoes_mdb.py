# -*- coding: utf-8 -*-
"""Estende ate o fim da frase as citacoes do MDB que paravam no meio.

O ACHADO. Ao conferir por que um link nao mostrava o texto, apareceu outra coisa:
tres citacoes do programa do MDB terminavam no meio da frase. A mais visivel:

    guardada: "...reconhecimento facial em todas as areas centrais e de grande
               circulacao nos principais centros urbanos"
    fonte:    "...nos principais centros urbanos, AEROPORTOS, ESTACOES
               RODOVIARIAS E METROS DO BRASIL."

Nenhuma delas distorce o sentido — o que foi cortado e continuacao de uma
enumeracao, nao ressalva nem condicao. Mas citacao que para no meio da frase faz
o leitor achar que a proposta e menor do que e, e a promessa do site e mostrar o
que a fonte diz, inteiro.

Seis outras citacoes tambem "continuavam", mas em FRASE NOVA: terminam em ponto e
o que vem depois e outra proposta. Essas estao certas e nao sao tocadas. A
diferenca e o que separa corte de fim de frase.

A LINHA VOLTA PARA REVISAO. Mudar o texto citado invalida a conferencia humana
que existia: o selo diria "conferido" sobre uma frase que ninguem leu. A decisao
anterior e preservada em revisao._antes, com o texto antigo ao lado.

USO
    python completar_citacoes_mdb.py
    python completar_citacoes_mdb.py --gravar
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from datetime import date

import acervo

RAIZ = pathlib.Path(__file__).resolve().parent
EXTRACAO = RAIZ / "fontes" / "programa-mdb-2025-caminhos.txt"
DOC = "doc-programa-nacional-mdb"


def fonte() -> str:
    """O texto da fonte com a hifenizacao de fim de linha desfeita.

    O PDF quebra palavra no fim da linha ("aeropor- tos"). Isso e diagramacao, e
    nao grafia: sem desfazer, a frase inteira nunca casa.
    """
    t = EXTRACAO.read_text(encoding="utf-8")
    return re.sub(r"\s+", " ", re.sub(r"-\s*\n\s*", "", t))


def completa(cit: str, src: str) -> str | None:
    """A mesma citacao ate o fim da frase, ou None se ja termina bem."""
    # A CITACAO QUE JA TERMINA EM PONTO ESTA INTEIRA. Sem esta linha, a primeira
    # versao "estendia" as seis que ja acabavam bem: emendava nelas a frase
    # SEGUINTE, e numa delas colou o cabecalho corrido do PDF ("NOSSO PAIS,
    # NOSSA CAUSA."). Um corretor que estraga o que estava certo e pior que o
    # defeito que ele conserta.
    if cit.rstrip()[-1:] in ".!?":
        return None
    j = src.lower().find(cit.lower())
    if j < 0:
        return None
    resto = src[j + len(cit):]
    if not resto or resto[0] in ".!?":
        return None                      # ja acaba onde a frase acaba
    fim = src.find(".", j + len(cit))
    if fim < 0:
        return None
    inteira = src[j:fim + 1].strip()
    # Se o "resto" contem o marcador de item do documento, a citacao ja terminou
    # e o que vem e outra proposta: nao juntar duas propostas numa citacao so.
    if " - " in src[j + len(cit):fim]:
        return None
    return inteira


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()

    src = fonte()
    mudadas: dict[str, str] = {}
    tocadas = 0
    perdiam_revisao = 0

    for uf in acervo.com_acervo():
        f = acervo.de(uf) / "posicoes.json"
        d = json.loads(f.read_text(encoding="utf-8"))
        mexeu = False
        for p in d["posicoes"]:
            if p.get("id_documento") != DOC:
                continue
            cit = (p.get("citacao_literal") or "").strip()
            nova = mudadas.get(cit) or completa(cit, src)
            if not nova or nova == cit:
                continue
            mudadas[cit] = nova
            tocadas += 1
            antes = p.get("revisao")
            p["citacao_literal"] = nova
            if p.get("revisado_por_humano") or antes:
                perdiam_revisao += 1
            p["revisado_por_humano"] = False
            historia = (antes or {}).get("_antes") or []
            if antes:
                historia = historia + [{k: v for k, v in antes.items() if k != "_antes"}]
            p["revisao"] = {
                "_antes": historia,
                "_reaberta_em": date.today().isoformat(),
                "_motivo": ("A citacao foi estendida ate o fim da frase: antes parava "
                            "no meio e o resto da enumeracao ficava de fora. Texto "
                            "anterior: " + cit),
            }
            mexeu = True
        if mexeu and a.gravar:
            f.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")

    print(f"{len(mudadas)} citacao(oes) distinta(s) estendida(s), "
          f"em {tocadas} linha(s) do acervo")
    print(f"{perdiam_revisao} linha(s) tinham decisao de revisao e voltam para a fila")
    for velho, novo in mudadas.items():
        print("\n  antes:", velho[-96:])
        print("  agora:", novo[-96:])
    if not a.gravar:
        print("\n(sem --gravar: nada foi escrito)")


if __name__ == "__main__":
    main()
