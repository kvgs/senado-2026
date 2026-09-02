# -*- coding: utf-8 -*-
"""Le dados/institucional-senado.json e CONFERE cada citacao contra a fonte.

POR QUE ISTO EXISTE. As artes que explicam o cargo nao saem do acervo: saem da
Constituicao e do demonstrativo de remuneracao do Senado. Sem acervo, nao ha
revisao humana linha por linha, e a tentacao e escrever o artigo de cabeca.

A licao do link do PL nesta mesma temporada: quatro versoes erradas do mesmo
link passaram por todos os conferidores, porque todos comparavam a citacao com o
arquivo guardado e nenhum abria o endereco publicado. Aqui o conferidor abre o
arquivo guardado — que e o que a arte cita — e para se a frase nao estiver la.

O QUE ELE PEGA
  - citacao que nao existe na fonte (frase inventada ou parafraseada);
  - fato apontando para documento que nao esta na lista;
  - arquivo de fonte que sumiu de fontes/;
  - hash diferente do registrado: o arquivo lido hoje nao e o que foi conferido.

O QUE ELE NAO PEGA, e continua sendo trabalho humano: se a FRASE da tela e uma
leitura honesta da citacao. "Deputado representa o povo" nao esta escrito assim
em nenhum artigo — e leitura do art. 45, e quem responde por ela e a curadoria.

USO
    python institucional.py            # confere e mostra o relatorio
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
import unicodedata

RAIZ = pathlib.Path(__file__).resolve().parent
ARQ = RAIZ / "dados" / "institucional-senado.json"


def ler() -> dict:
    return json.loads(ARQ.read_text(encoding="utf-8"))


def esp(s: str) -> str:
    """Espacos, quebras de linha e hifenacao de fim de linha achatados.

    O PDF quebra frase no meio da linha e as vezes parte palavra com hifen. Isso
    e formatacao, e nao diferenca de texto — mas cada um desses ja quebrou uma
    conferencia neste projeto, por isso o achatamento vem antes da comparacao.
    """
    s = s.replace("­", "")                      # hifen de quebra invisivel
    s = re.sub(r"-\s*\n\s*", "", s)                   # palavra partida na linha
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s).strip()


def frouxo(s: str) -> str:
    """Ultimo recurso: sem acento e sem maiuscula.

    Serve para dizer "esta la, com acento diferente" em vez de "nao esta la",
    que sao problemas diferentes e pedem correcoes diferentes.
    """
    s = unicodedata.normalize("NFKD", esp(s).lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _texto_da_fonte(doc: dict) -> str:
    """A extracao do PDF, refeita se nao existir.

    `fontes/*.txt` esta no .gitignore: extracao e trabalho DERIVADO, e o que
    vale e o PDF. Mas o conferidor precisa dela, entao num clone limpo ele a
    refaz em vez de parar — parar ali seria transformar uma convencao de
    versionamento em impedimento para conferir.
    """
    p = RAIZ / doc["extracao"]
    if not p.exists():
        pdf = RAIZ / doc["arquivo"]
        if not pdf.exists():
            raise SystemExit(
                f"PAROU: nao ha {doc['arquivo']} nem {doc['extracao']}. Sem o "
                "documento nao da para conferir citacao nenhuma, e arte com "
                "citacao nao conferida nao sai.")
        import pypdf
        print(f"  (refazendo {doc['extracao']} a partir do PDF)")
        r = pypdf.PdfReader(str(pdf))
        txt = "".join(f"\n[[pagina {i + 1}]]\n" + (pg.extract_text() or "")
                      for i, pg in enumerate(r.pages))
        p.write_text(re.sub(r"[ \t]+", " ", txt), encoding="utf-8")
    return esp(p.read_text(encoding="utf-8"))


def _confere_hash(doc: dict) -> str | None:
    p = RAIZ / doc["arquivo"]
    if not p.exists():
        return f"arquivo ausente: {doc['arquivo']}"
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != doc["sha256"]:
        return (f"sha256 diferente do registrado em {doc['arquivo']}\n"
                f"       registrado: {doc['sha256']}\n"
                f"       no disco:   {h}\n"
                "       O arquivo mudou depois de conferido. Reconferir as "
                "citacoes antes de gerar arte.")
    return None


def conferir(silencioso: bool = False) -> list[dict]:
    """Devolve a lista de fatos, ou PARA se algum nao se sustentar na fonte."""
    d = ler()
    docs = {x["id_documento"]: x for x in d["documentos"]}
    problemas: list[str] = []

    for doc in d["documentos"]:
        erro = _confere_hash(doc)
        if erro:
            problemas.append(f"[{doc['id_documento']}] {erro}")

    textos = {i: _texto_da_fonte(x) for i, x in docs.items()}
    fatos = sorted(d["fatos"], key=lambda f: f["ordem"])
    linhas = []

    for ft in fatos:
        idd = ft["id_documento"]
        if idd not in docs:
            problemas.append(f"[{ft['id']}] aponta para documento inexistente: {idd}")
            continue
        src = textos[idd]
        for campo in ("citacao_literal", "citacao_apoio"):
            cit = ft.get(campo)
            if not cit:
                continue
            if esp(cit) in src:
                linhas.append(("literal", ft["id"], campo, ft["dispositivo"]))
            elif frouxo(cit) in frouxo(src):
                problemas.append(
                    f"[{ft['id']}] {campo} so casa SEM ACENTO E SEM CAIXA. A "
                    "fonte escreve de outro jeito, e a arte tem de escrever "
                    f"como a fonte:\n       {esp(cit)}")
            else:
                problemas.append(
                    f"[{ft['id']}] {campo} NAO EXISTE na fonte "
                    f"({docs[idd]['arquivo']}):\n       {esp(cit)}")

    if problemas:
        print("PAROU: a arte nao sai com citacao que a fonte nao sustenta.\n",
              file=sys.stderr)
        for p in problemas:
            print(f"  - {p}", file=sys.stderr)
        raise SystemExit(1)

    if not silencioso:
        print(f"{len(fatos)} fatos, {len(linhas)} citacoes conferidas palavra "
              f"por palavra em {len(docs)} documentos.")
        for tipo, fid, campo, disp in linhas:
            marca = "citacao" if campo == "citacao_literal" else "apoio  "
            print(f"  ok  {marca}  {fid:<26} {disp}")
    return fatos


def documento(id_documento: str) -> dict:
    return {x["id_documento"]: x for x in ler()["documentos"]}[id_documento]


if __name__ == "__main__":
    conferir()
