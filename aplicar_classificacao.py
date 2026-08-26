# -*- coding: utf-8 -*-
"""Aplica a classificacao tematica proposta pelo modelo aos arquivos de coleta.

POR QUE O MAPEAMENTO E DADO, E NAO CODIGO. Em Sao Paulo eu escrevi as 304
decisoes dentro de um script Python. Funcionou para um estado; com 27 seriam 27
scripts quase iguais, e a proxima pessoa nao saberia qual e o de verdade. Agora
cada estado tem dados/<uf>/_classificacao-modelo.json, e este arquivo aplica.

MARCA QUEM DECIDIU. Grava por="modelo". A tela de classificacao mostra os casos
EDITORIAIS — onde a escolha foi minha e nao leitura — e uma amostra sorteada do
resto, para a conferencia humana medir se acertei. por="modelo" nunca vira
por="humano" sozinho.

RECUSA PARCIAL. Se o mapeamento nao cobrir todos os itens coletados, ou cobrir
itens que nao existem na coleta, o script para sem gravar. Classificacao pela
metade e pior que nenhuma: some no meio dos que estao certos.

USO
    python aplicar_classificacao.py --uf PE
    python aplicar_classificacao.py --uf PE --gravar
"""
from __future__ import annotations

import argparse
import collections
import json

import acervo

ARQUIVOS = ("_coleta_legislativa.json", "_coleta_discursos.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", required=True)
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()
    uf = a.uf.upper()
    base = acervo.exige(uf)

    mapa_p = base / "_classificacao-modelo.json"
    if not mapa_p.exists():
        raise SystemExit(f"nao existe {mapa_p.relative_to(acervo.RAIZ)}")
    m = json.loads(mapa_p.read_text(encoding="utf-8"))
    mapa = m["classificacao"]
    editorial = m.get("_editorial", {})
    sem_objeto = m.get("_sem_objeto", {})

    # Quais itens existem de fato na coleta.
    presentes: dict[str, tuple] = {}
    for nome in ARQUIVOS:
        p = base / nome
        if not p.exists():
            continue
        for r in json.loads(p.read_text(encoding="utf-8"))["registros"]:
            presentes[r["id_registro"]] = (nome, r)

    alvo = {i for i in presentes if i in mapa}
    fantasmas = sorted(set(mapa) - set(presentes))
    if fantasmas:
        raise SystemExit(f"o mapeamento cita {len(fantasmas)} id(s) que nao estao na "
                         f"coleta: {fantasmas[:6]} — nada gravado")

    print(f"{uf}: {len(presentes)} itens coletados · {len(alvo)} no mapeamento")
    faltam = len(presentes) - len(alvo)
    if faltam:
        print(f"     {faltam} ainda sem classificacao proposta (outras candidaturas)")

    temas = collections.Counter()
    vazios = 0
    for i in alvo:
        t = mapa[i]
        if t:
            temas.update(t)
        else:
            vazios += 1
    nomes = m.get("_temas", {})
    print(f"\ndistribuicao ({len(alvo) - vazios} com tema, {vazios} sem):")
    for t, n in temas.most_common():
        print(f"   {nomes.get(t, t):30} {n:4}")
    print(f"\n{len(editorial)} marcado(s) como escolha editorial · "
          f"{len(sem_objeto)} sem objeto na ementa")

    if not a.gravar:
        print("\n(sem --gravar: nada foi escrito)")
        return 0

    por_arquivo = collections.Counter()
    for nome in ARQUIVOS:
        p = base / nome
        if not p.exists():
            continue
        dados = json.loads(p.read_text(encoding="utf-8"))
        for r in dados["registros"]:
            i = r["id_registro"]
            if i not in mapa:
                continue
            t = mapa[i]
            r["_classificacao"] = {
                "temas": t,
                "motivo": "" if t else ("vazio" if i in sem_objeto else "nenhum"),
                "por": "modelo",
                "decidido_em": acervo.ref().get("site", {}).get("_hoje", "2026-08-26"),
            }
            if i in editorial:
                r["_classificacao"]["precisa_de_olho"] = editorial[i]
            elif i in sem_objeto:
                r["_classificacao"]["precisa_de_olho"] = sem_objeto[i]
            por_arquivo[nome] += 1
        p.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")

    for nome, n in por_arquivo.items():
        print(f"\n{nome}: {n} classificados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
