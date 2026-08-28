# -*- coding: utf-8 -*-
"""Extrai posicoes de PROGRAMA PARTIDARIO nacional, para todas as candidaturas
daquele partido, em todos os estados.

ESTADO B, E NUNCA A. Programa de partido nao e proposta da candidatura. O site
ja separa os dois, e a tela escreve "Proposta do PARTIDO, nao da candidatura" ao
lado. Confundir os dois seria atribuir a uma pessoa o que ela nao assinou.

SO PROGRAMA NACIONAL. Documento registrado no TSE por UMA candidatura NAO vale
para as outras: a Unidade Popular registrou programas diferentes por estado, e
um dos arquivos do acervo se chama literalmente
"programa-up-2026-ESPIRITO-SANTO--NAO-USAR-PARA-SP.pdf". Replicar aquilo seria
inventar. Aqui so entra documento publicado pelo PROPRIO PARTIDO como programa
nacional, e a URL fica gravada.

A MESMA TRAVA DE SEMPRE: o trecho tem de existir palavra por palavra no texto
extraido do documento. Se nao existir, recusa.

CAIXA. Programa costuma trazer as propostas como titulo em CAIXA ALTA. Isso e
tipografia, nao conteudo, e exibir assim grita na tela — a mesma decisao ja
tomada para os nomes que o TSE grava em caixa alta. A comparacao ignora caixa e
acento, e o item guarda a nota de que a fonte usa titulo em caixa.

USO
    python extrair_programa_partido.py --arquivo extracoes/partido-up.json
    python extrair_programa_partido.py --arquivo extracoes/partido-up.json --gravar
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import unicodedata
from datetime import date

import acervo


def normal(s: str) -> str:
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arquivo", required=True)
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()

    spec = json.loads(pathlib.Path(a.arquivo).read_text(encoding="utf-8"))
    sigla = spec["partido"]
    corpo = pathlib.Path(spec["texto_extraido"]).read_text(encoding="utf-8")
    corpo_n = normal(corpo)
    temas = {t["id_tema"] for t in acervo.ler("referencia.json")["temas"]}

    pid = next((p["id_partido"] for p in acervo.ler("referencia.json")["partidos"]
                if p["sigla"].upper() == sigla.upper()), None)
    if pid is None:
        raise SystemExit(f"partido {sigla} nao esta em referencia.json")

    aceitas, recusadas = [], []
    for p in spec["posicoes"]:
        if p["tema"] not in temas:
            recusadas.append((p, f"tema {p['tema']!r} nao existe")); continue
        if normal(p["trecho"]) not in corpo_n:
            recusadas.append((p, "TRECHO NAO E LITERAL no documento")); continue
        aceitas.append(p)

    print(f"{sigla}: {len(aceitas)} aceita(s), {len(recusadas)} recusada(s)")
    for p, e in recusadas:
        print(f"  RECUSADA — {e}\n    {p['trecho'][:90]!r}")
    if recusadas:
        raise SystemExit("PAROU: corrija antes de gravar.")

    # Onde este partido tem candidatura
    alvos = []
    for e in acervo.ler("estados.json")["estados"]:
        for c in acervo.ler("candidaturas.json", e["uf"])["candidaturas"]:
            if c["id_partido"] == pid:
                alvos.append((e["uf"], c["id_candidatura"]))
    # DOCUMENTO MAIS ESPECIFICO VENCE. Onde o partido ja tem posicoes vindas de um
    # programa registrado por aquela candidatura, o programa nacional NAO entra:
    # seriam duas fontes dizendo quase a mesma coisa, e a especifica e melhor.
    # Sao Paulo ja tem 20 posicoes da UP do PDF registrado no TSE por la.
    ufs, pulados = [], []
    for u in sorted({x for x, _ in alvos}):
        ja = [x for x in acervo.ler("posicoes.json", u)["posicoes"]
              if x.get("atribuido_a_id") == pid and x.get("atribuido_a_tipo") == "partido"
              and x.get("id_documento") != f"doc-programa-nacional-{sigla.lower()}"]
        (pulados if ja else ufs).append((u, len(ja)))
    ufs = [u for u, _ in ufs]
    for u, n in pulados:
        print(f"  {u} pulado: ja tem {n} posicao(oes) do {sigla} de programa mais especifico")
    print(f"  {len(alvos)} candidatura(s) do {sigla} em {len(ufs)} estado(s): {' '.join(ufs)}")
    print(f"  {len(aceitas)} posicao(oes) x {len(ufs)} estado(s) = "
          f"{len(aceitas) * len(ufs)} linha(s) de programa")

    if not a.gravar:
        print("\n(sem --gravar: nada foi escrito)")
        return

    doc = {
        "id_documento": f"doc-programa-nacional-{sigla.lower()}",
        "tipo": "programa_partidario",
        "titulo": spec["titulo"],
        "url": spec["url"],
        "publicado_em": spec.get("publicado_em"),
        "consultado_em": date.today().isoformat(),
        "_ambito": "nacional",
        "_nota": spec.get("nota", ""),
    }

    for uf in ufs:
        f_doc = acervo.de(uf) / "documentos.json"
        d = json.loads(f_doc.read_text(encoding="utf-8"))
        if not any(x["id_documento"] == doc["id_documento"] for x in d["documentos"]):
            d["documentos"].append(doc)
            f_doc.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n",
                             encoding="utf-8")

        f_pos = acervo.de(uf) / "posicoes.json"
        dp = json.loads(f_pos.read_text(encoding="utf-8"))
        ja = {x["id_posicao"] for x in dp["posicoes"]}
        n = 0
        # UMA LINHA POR CANDIDATURA, e nao por estado. Proposta de partido aparece
        # na celula de uma candidatura, entao precisa dizer DE QUAL — o validador
        # exige id_candidatura_contexto, e com razao: sem isso a linha flutua sem
        # dono e o site nao saberia sob quem exibir.
        for cid in [c for u, c in alvos if u == uf]:
          for i, p in enumerate(aceitas, 1):
            pid_pos = f"pos-{cid}-prog-{sigla.lower()}-{i:03d}"
            if pid_pos in ja:
                continue
            dp["posicoes"].append({
                "id_posicao": pid_pos,
                "id_candidatura_contexto": cid,
                "id_tema": p["tema"],
                # B: a proposta e do PARTIDO. A tela escreve isso ao lado.
                "atribuido_a_tipo": "partido",
                "atribuido_a_id": pid,
                "estado_cobertura": "B",
                "natureza": "promessa",
                "nivel_fonte": "oficial",
                "id_documento": doc["id_documento"],
                "citacao_literal": p["trecho"],
                "texto": p.get("resumo") or "",
                "url_especifica": spec["url"],
                "data_referencia": spec.get("publicado_em") or date.today().isoformat(),
                "revisado_por_humano": False,
                "conferido_por_ia": {
                    "data": date.today().isoformat(),
                    "forca": "alta",
                    "base": f"trecho conferido palavra por palavra contra {spec['texto_extraido']}",
                    "ressalva": ("Proposta do partido, nao da candidatura. O documento usa "
                                 "titulo em caixa alta; a caixa foi normalizada para leitura, "
                                 "as palavras nao."),
                },
                "_promovido_em": date.today().isoformat(),
            })
            n += 1
        if n:
            f_pos.write_text(json.dumps(dp, ensure_ascii=False, indent=1) + "\n",
                             encoding="utf-8")
    print(f"\ngravado em {len(ufs)} estado(s).")


if __name__ == "__main__":
    main()
