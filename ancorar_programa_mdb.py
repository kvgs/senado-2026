# -*- coding: utf-8 -*-
"""Faz o link do programa do MDB apontar para o documento, e para a PAGINA certa.

O DEFEITO. A revisao humana marcou uma linha do MDB com a nota "Nao achei no
site". A nota estava certa: o `url_especifica` das 304 posicoes tiradas desse
programa apontava para
https://www.mdb.org.br/documento-caminhos-para-o-brasil/, que e a pagina em que o
partido ANUNCIOU o documento — nao o documento. O texto citado esta num PDF de
51 MB hospedado na fundacao do partido, e esse endereco estava guardado apenas
numa nota interna do registro do documento.

E o mesmo defeito do programa do PL, pela quarta vez nesta temporada: a citacao
existe palavra por palavra no arquivo guardado, todo conferidor aprova, e quem
CLICA no link nao acha a frase. Nenhum conferidor deste projeto abre o endereco
publicado — a revisao humana e o unico lugar onde isso aparece.

O QUE ESTE SCRIPT FAZ
  - acha, para cada citacao, a PAGINA do PDF em que ela esta, lendo pagina por
    pagina com pypdf. A posicao do texto no arquivo achatado NAO serve: num PDF
    diagramado, o rodape de uma pagina aparece no meio do texto corrido da
    seguinte, e foi assim que metade das citacoes do PL ganhou o numero errado.
  - grava url_especifica = <PDF>#page=N por posicao
  - troca a url do documento para o PDF, e guarda a pagina de anuncio numa nota

O QUE ELE NAO FAZ. Nao mexe em revisao. Se uma linha do MDB foi conferida
olhando o link antigo, a conferencia se deu contra um endereco que nao mostra a
frase — reabrir ou nao e decisao da curadoria, como foi no caso do PL.

USO
    python ancorar_programa_mdb.py
    python ancorar_programa_mdb.py --gravar
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import unicodedata

import acervo

RAIZ = pathlib.Path(__file__).resolve().parent
PDF = RAIZ / "fontes" / "programa-mdb-2025-caminhos-para-o-brasil.pdf"
DOC = "doc-programa-nacional-mdb"
URL_PDF = ("https://fundacaoulysses.org.br/wp-content/uploads/2025/10/"
           "FUG-18x26cm-DIGITAL.pdf")
URL_ANUNCIO = "https://www.mdb.org.br/documento-caminhos-para-o-brasil/"


def nu(s: str) -> str:
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def paginas_do_pdf() -> list[str]:
    if not PDF.exists():
        raise SystemExit(
            f"PAROU: falta {PDF.relative_to(RAIZ)}. O PDF tem 51 MB e esta fora do "
            "Git; baixe de " + URL_PDF + " antes de rodar.")
    import pypdf
    r = pypdf.PdfReader(str(PDF))
    return [nu(p.extract_text() or "") for p in r.pages]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()

    pags = paginas_do_pdf()
    print(f"{PDF.name}: {len(pags)} paginas lidas uma a uma")

    achadas = perdidas = 0
    por_pagina: dict[int, int] = {}
    for uf in acervo.com_acervo():
        f = acervo.de(uf) / "posicoes.json"
        d = json.loads(f.read_text(encoding="utf-8"))
        mexeu = False
        for p in d["posicoes"]:
            if p.get("id_documento") != DOC:
                continue
            cit = nu(p.get("citacao_literal") or "")
            if not cit:
                continue
            pg = next((i + 1 for i, t in enumerate(pags) if cit in t), None)
            if pg is None:
                perdidas += 1
                print(f"  SEM PAGINA  [{uf}] {p['id_posicao']}")
                print(f"              {(p.get('citacao_literal') or '')[:90]}")
                continue
            achadas += 1
            por_pagina[pg] = por_pagina.get(pg, 0) + 1
            novo = f"{URL_PDF}#page={pg}"
            if p.get("url_especifica") != novo:
                p["url_especifica"] = novo
                p.setdefault("_url_antes", URL_ANUNCIO)
                mexeu = True
        if mexeu and a.gravar:
            f.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")

        fd = acervo.de(uf) / "documentos.json"
        dd = json.loads(fd.read_text(encoding="utf-8"))
        troca = False
        for doc in dd["documentos"]:
            if doc["id_documento"] == DOC and doc.get("url") != URL_PDF:
                doc["url"] = URL_PDF
                doc["_url_de_anuncio"] = (
                    "O partido apresentou o documento em " + URL_ANUNCIO + ", que "
                    "era o endereco publicado antes. Essa pagina ANUNCIA o "
                    "documento e nao o contem: a revisao humana marcou uma linha "
                    "com 'Nao achei no site' e estava certa. A url passou a ser o "
                    "PDF, e cada posicao aponta a pagina dele.")
                doc["_arquivo_bytes_aviso"] = (
                    "O PDF tem 51 MB. Abrir o link baixa o arquivo inteiro, o que e "
                    "pesado — e ainda assim melhor que um link em que a frase nao "
                    "esta.")
                troca = True
        if troca and a.gravar:
            fd.write_text(json.dumps(dd, ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")

    print(f"\n{achadas} citacao(oes) ancorada(s), {perdidas} sem pagina")
    if por_pagina:
        faixa = ", ".join(f"p{k} ({v})" for k, v in sorted(por_pagina.items()))
        print(f"paginas usadas: {faixa}")
    if not a.gravar:
        print("\n(sem --gravar: nada foi escrito)")


if __name__ == "__main__":
    main()
