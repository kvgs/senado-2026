# -*- coding: utf-8 -*-
"""Onde cada arquivo de dados mora. Um lugar so, para nao existirem dois.

POR QUE ISTO EXISTE. Ate agora havia um acervo, de Sao Paulo, e cada ferramenta
escrevia `RAIZ / "dados" / "candidaturas.json"` na mao — em nove ferramentas.
Com dois estados isso vira nove chances de ler o acervo do estado errado, e ler
o estado errado NAO da erro: da resultado plausivel e falso.

A DIVISAO

  nacional     referencia.json (temas, partidos, selos), estados.json, mapa-uf.json
               Valem para os 27. Um tema nao muda de nome por estado.

  por estado   candidaturas, posicoes, documentos, registros legislativos,
               pesquisas, respostas e os arquivos de coleta.
               Vivem em dados/<uf>/, minusculo.

POR QUE PASTA POR ESTADO, e nao um campo `uf` em cada registro. A curadoria e
por estado: a revisao de Pernambuco nao deve poder tocar em Sao Paulo, e o
validador precisa poder dizer "o acervo de PE esta consistente" sem carregar os
outros 26. Pasta separada da isso de graca; campo `uf` exigiria filtro correto em
toda consulta, e um filtro esquecido mistura estados calado.

A UF PADRAO fica em referencia.json -> site.uf. As ferramentas aceitam --uf para
trabalhar em outro sem editar arquivo nenhum.
"""
from __future__ import annotations

import json
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent
NACIONAL = RAIZ / "dados"

# Arquivos que valem para o pais inteiro. Se um deles aparecer dentro de
# dados/<uf>/, e sinal de que alguem duplicou dado nacional por estado.
DE_TODOS = ("referencia.json", "estados.json", "mapa-uf.json")


def ref() -> dict:
    return json.loads((NACIONAL / "referencia.json").read_text(encoding="utf-8"))


def uf_padrao() -> str:
    u = ((ref().get("site") or {}).get("uf") or "").strip().upper()
    if not u:
        raise SystemExit("dados/referencia.json nao diz site.uf — nao sei que estado usar")
    return u


def de(uf: str | None = None) -> pathlib.Path:
    """Pasta do acervo de um estado. Nao cria: se nao existe, o estado nao existe."""
    u = (uf or uf_padrao()).lower()
    return NACIONAL / u


def exige(uf: str | None = None) -> pathlib.Path:
    """Como de(), mas para se a pasta nao existir — em vez de deixar cada
    ferramenta estourar depois com 'arquivo nao encontrado' sem dizer por que."""
    p = de(uf)
    if not p.is_dir():
        tem = ", ".join(sorted(x.name.upper() for x in NACIONAL.iterdir()
                               if x.is_dir() and len(x.name) == 2)) or "nenhum"
        raise SystemExit(f"nao existe acervo para {p.name.upper()} em {p}.\n"
                         f"estados com acervo: {tem}")
    return p


def com_acervo() -> list[str]:
    """UFs que tem pasta. Ordenado, para a saida das ferramentas ser estavel."""
    return sorted(x.name.upper() for x in NACIONAL.iterdir()
                  if x.is_dir() and len(x.name) == 2)


def ler(nome: str, uf: str | None = None) -> dict:
    """Le um arquivo do acervo do estado, ou o nacional se for um dos DE_TODOS."""
    base = NACIONAL if nome in DE_TODOS else exige(uf)
    return json.loads((base / nome).read_text(encoding="utf-8"))


def estado(uf: str | None = None) -> dict:
    """A linha de estados.json daquela UF: nome, preposicao, assembleia, contagem."""
    u = (uf or uf_padrao()).upper()
    for e in ler("estados.json")["estados"]:
        if e["uf"] == u:
            return e
    raise SystemExit(f"{u} nao esta em dados/estados.json")


def por_extenso(uf: str | None = None) -> str:
    """"por Sao Paulo", "pelo Acre", "pela Bahia" — concordancia sai do dado."""
    e = estado(uf)
    return {"de": "por", "do": "pelo", "da": "pela"}[e["preposicao"]] + " " + e["nome"]
