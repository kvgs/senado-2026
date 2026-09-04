# -*- coding: utf-8 -*-
"""Confere se alguma citacao de site veio de conteudo OCULTO na pagina.

O CASO QUE ORIGINOU ISTO. O site da Alliny Serrao mantinha um bloco dentro de
<!-- -->: a Lei 2.750/2022, com titulo, numero e descricao. O navegador nao
mostra nada disso, mas o extrator do coletor tirava as tags sem tirar os
comentarios — e a linha entrou no acervo como declaracao da candidatura.

Quem pegou foi a revisao humana, com a nota "Nao achei no site". Nenhum
conferidor automatico pegaria: todos comparam a citacao com o texto que o
extrator produziu, e o defeito estava no extrator. Este script e o unico do
projeto que vai ao HTML CRU da pagina publicada e pergunta outra coisa — nao "a
citacao existe no que extraimos", e sim "a citacao esta em pedaco que o
navegador MOSTRA".

O QUE ELE OLHA
  - comentario HTML <!-- -->
  - <script>, <style>, <template> e <noscript>
  - atributo hidden e style com display:none

O QUE ELE NAO RESOLVE. Conteudo escondido por CSS de arquivo externo ou por
JavaScript continua invisivel para ele. Aqui, como sempre, quem confere de
verdade e quem abre a pagina.

USO
    python conferir_oculto.py
    python conferir_oculto.py --uf AP
"""
from __future__ import annotations

import argparse
import re
import time
import unicodedata
import urllib.error
import urllib.request

import acervo

AGENTE = ("senado-2026/1.0 (+https://kvgs.github.io/senado-2026/; "
          "conferencia de citacao contra a pagina publicada)")
PAUSA = 2.0


def nu(s: str) -> str:
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def baixar(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def partes_ocultas(html: str) -> str:
    """So o que o navegador NAO mostra, junto num texto so."""
    fora = []
    fora += re.findall(r"<!--.*?-->", html, flags=re.S)
    fora += re.findall(r"<(?:script|style|template|noscript)\b.*?</(?:script|style|template|noscript)>",
                       html, flags=re.S | re.I)
    fora += re.findall(r"<[^>]*\bhidden\b[^>]*>.*?</[a-z]+>", html, flags=re.S | re.I)
    fora += re.findall(r"<[^>]*style=[\"'][^\"']*display\s*:\s*none[^\"']*[\"'][^>]*>.*?</[a-z]+>",
                       html, flags=re.S | re.I)
    return nu(re.sub(r"<[^>]+>", " ", " ".join(fora)))


def visivel(html: str) -> str:
    s = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    s = re.sub(r"<(?:script|style|template|noscript)\b.*?</(?:script|style|template|noscript)>",
               " ", s, flags=re.S | re.I)
    return nu(re.sub(r"<[^>]+>", " ", s))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf")
    a = ap.parse_args()
    ufs = [a.uf.upper()] if a.uf else acervo.com_acervo()

    alvos: dict[str, list] = {}
    for uf in ufs:
        docs = {d["id_documento"]: d for d in acervo.ler("documentos.json", uf)["documentos"]}
        for p in acervo.ler("posicoes.json", uf)["posicoes"]:
            doc = docs.get(p.get("id_documento") or "")
            if not doc or doc.get("tipo") != "site_de_candidatura":
                continue
            if (p.get("revisao") or {}).get("resultado") == "remover":
                continue
            cit = (p.get("citacao_literal") or "").strip()
            if not cit:
                continue
            url = p.get("url_especifica") or doc.get("url") or ""
            alvos.setdefault(url, []).append((uf, p["id_posicao"], cit))

    print(f"{sum(len(v) for v in alvos.values())} citacao(oes) de site em "
          f"{len(alvos)} endereco(s)\n")
    ocultas, sumidas, ok, off = [], [], 0, []
    for url, itens in alvos.items():
        html = baixar(url)
        time.sleep(PAUSA)
        if html is None:
            off.append((url, len(itens)))
            continue
        vis, esc = visivel(html), partes_ocultas(html)
        for uf, pid, cit in itens:
            n = nu(cit)
            if n in vis:
                ok += 1
            elif n in esc:
                ocultas.append((uf, pid, url, cit))
            else:
                sumidas.append((uf, pid, url, cit))

    print(f"{ok} citacao(oes) estao no que a pagina MOSTRA hoje")
    if ocultas:
        print(f"\n{len(ocultas)} EM CONTEUDO OCULTO — a pagina traz o texto, e o "
              "navegador nao mostra:")
        for uf, pid, url, cit in ocultas:
            print(f"   [{uf}] {pid}\n        {url}\n        {cit[:100]}")
    if sumidas:
        print(f"\n{len(sumidas)} NAO ESTAO MAIS NA PAGINA. Pode ser que o site "
              "tenha mudado depois da coleta — a data de referencia da linha diz "
              "de quando ela e:")
        for uf, pid, url, cit in sumidas:
            print(f"   [{uf}] {pid}\n        {url}\n        {cit[:100]}")
    if off:
        print(f"\n{len(off)} endereco(s) nao responderam agora — nao da para "
              "concluir nada sobre eles:")
        for url, n in off:
            print(f"   {url}  ({n} citacao(oes))")


if __name__ == "__main__":
    main()
