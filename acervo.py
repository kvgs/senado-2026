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


# ---------------------------------------------------------------- quem revisa
# Enquanto havia uma pessoa, "humano" e "ela" eram a mesma coisa e bastava um
# booleano. Com colaboradores, revisado_por_humano=true deixa de dizer QUEM
# conferiu — e se um erro aparecer numa posicao publicada, nao da para revisar de
# novo so o que aquela pessoa fez.
#
# O identificador NAO vem de git config user.name. Ali esta o nome civil de quem
# mantem o projeto, e este repositorio e publico: herdar dali reporia nos dados
# exatamente o nome que a curadoria pediu para tirar. Quem trabalha ESCOLHE um
# apelido, sabendo que ele fica visivel.
ARQ_QUEM = RAIZ / ".quem"          # fora do git, por maquina


def quem(argumento: str | None = None) -> str:
    """Apelido de quem esta decidindo. Ordem: --quem, variavel de ambiente,
    arquivo local, e por fim pergunta uma vez e guarda."""
    import os
    import sys

    v = (argumento or os.environ.get("SENADO_QUEM") or "").strip()
    if not v and ARQ_QUEM.exists():
        v = ARQ_QUEM.read_text(encoding="utf-8").strip()
    if not v and not sys.stdin.isatty():
        # Sem ninguem no teclado, perguntar PENDURA o processo em vez de falhar.
        # Acontece em teste e em qualquer execucao automatizada.
        raise SystemExit(
            "nao sei quem esta revisando, e nao ha terminal para perguntar."
            + chr(10) + "passe --quem SEU_APELIDO, ou defina SENADO_QUEM no ambiente.")
    if not v:
        print("Quem esta revisando? Escolha um apelido curto — ele vai junto de cada")
        print("decisao e FICA VISIVEL no repositorio publico. Sugestao: o seu usuario")
        print("do GitHub. Nao use nome civil se nao quiser que ele apareca.")
        v = input("apelido: ").strip()
        if v:
            ARQ_QUEM.write_text(v, encoding="utf-8")
            print(f"guardado em {ARQ_QUEM.name} (fora do git); apague o arquivo para trocar")
    if not v:
        raise SystemExit("sem apelido nao da para registrar quem decidiu")
    return v


def por_extenso(uf: str | None = None) -> str:
    """"por Sao Paulo", "pelo Acre", "pela Bahia" — concordancia sai do dado."""
    e = estado(uf)
    return {"de": "por", "do": "pelo", "da": "pela"}[e["preposicao"]] + " " + e["nome"]
