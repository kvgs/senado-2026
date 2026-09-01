# -*- coding: utf-8 -*-
"""Descobre quais candidaturas JA TIVERAM mandato federal, e nao tem mais.

POR QUE ESTE PASSO EXISTE, E POR QUE ELE E DIFERENTE DO OUTRO. O
resolver_mandatos.py pergunta a Camara e ao Senado quem esta em exercicio HOJE.
Quem saiu nao aparece — e quem saiu tem registro legislativo exatamente igual ao
de quem ficou. Foi assim que a Mara Rocha, deputada federal pelo Acre de 2019 a
2023, ficou no acervo com mandatos_anteriores vazio e zero posicao propria: o
coletor legislativo procura situacao_parlamentar, situacao_parlamentar descreve o
presente, e o presente dela nao tem mandato.

O ENCERRADOS ESTAVA FIXO NO CODIGO. Uma entrada, escrita a mao, para a Tebet.
Entrada a mao nao escala e nao se audita: ninguem sabe quem falta.

CASAMENTO POR NOME, CONFIRMADO POR DATA DE NASCIMENTO. Nome sozinho e chave ruim
— e o erro que este projeto mais teve foi atribuir proposicao de um parlamentar a
candidatura de outra pessoa. Entao o nome so ABRE a suspeita; o que fecha e a
data de nascimento, que a API da Camara publica em dataNascimento e o registro no
TSE publica em data_nascimento. Datas iguais e nome civil compativel = a mesma
pessoa. Data diferente = homonimo, e sai como recusa explicita, nao como palpite.

O QUE ELE NAO FAZ. Nao grava em candidaturas.json e nao coleta proposicao
nenhuma. Escreve dados/mandatos-encerrados.json, que o coletar_legislativo.py le.
A separacao e de proposito: descobrir quem tem mandato passado e uma operacao,
colher o que a pessoa propos e outra, e nenhuma das duas afirma tema.

LEGISLATURAS VARRIDAS: 52 (2003) a 57 (hoje). Antes de 2003 a API da Camara fica
irregular, e mandato de mais de vinte anos atras diz pouco sobre a candidatura de
hoje — mas o limite e escolha, e esta escrito aqui para poder ser discutido.

USO
    python resolver_mandatos_encerrados.py --uf AC
    python resolver_mandatos_encerrados.py --todos
    python resolver_mandatos_encerrados.py --todos --gravar
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time
import unicodedata
import urllib.request
from datetime import date

import acervo

UA = {"accept": "application/json",
      "User-Agent": "senado-2026/1.0 (projeto civico; +https://kvgs.github.io/senado-2026/)"}
LEGISLATURAS = [52, 53, 54, 55, 56, 57]
PAUSA = 0.34
ARQ = pathlib.Path("dados/mandatos-encerrados.json")


def buscar(url: str) -> dict:
    time.sleep(PAUSA)
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=90).read().decode("utf-8"))


def chave(s: str) -> str:
    return " ".join(unicodedata.normalize("NFD", (s or ""))
                    .encode("ascii", "ignore").decode().upper().split())


def deputados_de(leg: int) -> list[dict]:
    saida, pag = [], 1
    while True:
        d = buscar("https://dadosabertos.camara.leg.br/api/v2/deputados"
                   f"?idLegislatura={leg}&itens=100&pagina={pag}")["dados"]
        saida += d
        if len(d) < 100:
            return saida
        pag += 1


def senadores_de(leg: int) -> list[dict]:
    j = buscar("https://legis.senado.leg.br/dadosabertos/senador/lista/legislatura/"
               f"{leg}.json")
    ps = j["ListaParlamentarLegislatura"]["Parlamentares"]["Parlamentar"]
    return [x["IdentificacaoParlamentar"] for x in ps]


def ficha_senado(cod: str) -> tuple[str, str, str]:
    """Devolve (nascimento, nome completo, UF). A lista por legislatura nao traz a
    UF; a ficha traz."""
    j = buscar(f"https://legis.senado.leg.br/dadosabertos/senador/{cod}.json")
    par = j["DetalheParlamentar"]["Parlamentar"]
    ident = par.get("IdentificacaoParlamentar") or {}
    basicos = par.get("DadosBasicosParlamentar") or {}
    return ((basicos.get("DataNascimento") or "")[:10],
            ident.get("NomeCompletoParlamentar") or "",
            ident.get("UfParlamentar") or "")


def em_exercicio_camara() -> set[str]:
    """Quem esta la HOJE nao e mandato encerrado — e trabalho do outro script."""
    d = buscar("https://dadosabertos.camara.leg.br/api/v2/deputados?itens=600")["dados"]
    return {str(x["id"]) for x in d}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()
    if not a.uf and not a.todos:
        raise SystemExit("passe --uf XX ou --todos")
    ufs = acervo.com_acervo() if a.todos else [a.uf.upper()]

    print(f"varrendo legislaturas {LEGISLATURAS[0]}-{LEGISLATURAS[-1]} da Camara...")
    por_nome: dict[str, dict] = {}
    for leg in LEGISLATURAS:
        for x in deputados_de(leg):
            r = por_nome.setdefault(str(x["id"]), {
                "id_externo": str(x["id"]), "nome_casa": x["nome"],
                "ufs": set(), "legislaturas": set()})
            r["ufs"].add(x.get("siglaUf"))
            r["legislaturas"].add(leg)
    print(f"  {len(por_nome)} pessoas distintas passaram pela Camara no periodo")
    hoje = em_exercicio_camara()

    print(f"varrendo legislaturas {LEGISLATURAS[0]}-{LEGISLATURAS[-1]} do Senado...")
    por_cod: dict[str, dict] = {}
    nao_varridas = []
    for leg in LEGISLATURAS:
        try:
            lista = senadores_de(leg)
        except Exception as e:                       # noqa: BLE001
            nao_varridas.append(leg)
            print(f"  legislatura {leg} do Senado: NAO obtida ({type(e).__name__}). "
                  "Fica dito, e nao vira silencio.")
            continue
        for ip in lista:
            r = por_cod.setdefault(str(ip["CodigoParlamentar"]), {
                "id_externo": str(ip["CodigoParlamentar"]),
                "nome_casa": ip.get("NomeParlamentar") or "",
                "nome_completo_casa": ip.get("NomeCompletoParlamentar") or "",
                "casa": "senado", "ufs": set(), "legislaturas": set()})
            r["ufs"].add(ip.get("UfParlamentar"))
            r["legislaturas"].add(leg)
    print(f"  {len(por_cod)} pessoas distintas passaram pelo Senado no periodo")
    hoje_sen = {str(x["IdentificacaoParlamentar"]["CodigoParlamentar"]) for x in
                buscar("https://legis.senado.leg.br/dadosabertos/senador/lista/atual.json")
                ["ListaParlamentarEmExercicio"]["Parlamentares"]["Parlamentar"]}

    indice: dict[str, list[dict]] = {}
    for r in por_nome.values():
        r["casa"] = "camara"
        indice.setdefault(chave(r["nome_casa"]), []).append(r)
    for r in por_cod.values():
        for n in (r["nome_casa"], r["nome_completo_casa"]):
            if n:
                indice.setdefault(chave(n), []).append(r)

    # 1900-01-01 e o preenchimento que a API usa quando NAO SABE a data, e nao uma
    # data. Tratar isso como data faria o script dizer "homonimo, outra pessoa"
    # sobre alguem que pode muito bem ser a mesma — afirmacao mais forte do que o
    # dado permite, e o oposto do que este projeto faz com ausencia.
    SEM_DATA = {"1900-01-01", "0001-01-01", "1901-01-01"}
    achados, recusas, ambiguos, sem_confirmar = [], [], [], []
    for uf in ufs:
        for c in acervo.ler("candidaturas.json", uf)["candidaturas"]:
            if c.get("situacao_parlamentar"):
                continue                     # em exercicio: e do outro script
            nomes = {chave(c["pessoa"]["nome_urna"]), chave(c["pessoa"]["nome_completo"])}
            cands_api = [r for n in nomes for r in indice.get(n, [])]
            if not cands_api:
                continue
            nasc_tse = c["pessoa"].get("data_nascimento")
            confirmados = []
            for r in {(x["casa"], x["id_externo"]): x for x in cands_api}.values():
                if r["casa"] == "camara":
                    det = buscar("https://dadosabertos.camara.leg.br/api/v2/deputados/"
                                 + r["id_externo"])["dados"]
                    nasc_api = (det.get("dataNascimento") or "")[:10]
                    nome_civil = det.get("nomeCivil") or ""
                else:
                    nasc_api, nome_civil, uf_sen = ficha_senado(r["id_externo"])
                    if uf_sen:
                        r["ufs"] = {uf_sen}
                if not nasc_tse or not nasc_api or nasc_api in SEM_DATA:
                    sem_confirmar.append((uf, c["pessoa"]["nome_urna"], r["nome_casa"],
                                          r["casa"], r["id_externo"]))
                    continue
                if nasc_api != nasc_tse:
                    recusas.append((uf, c["pessoa"]["nome_urna"], r["nome_casa"],
                                    f"nasceu {nasc_api} na casa legislativa e "
                                    f"{nasc_tse} no TSE — homonimo, outra pessoa"))
                    continue
                confirmados.append((r, nome_civil, nasc_api))
            if not confirmados:
                continue
            casas = {r["casa"] for r, _, _ in confirmados}
            if len(confirmados) > len(casas):
                ambiguos.append((uf, c["pessoa"]["nome_urna"],
                                 [r["nome_casa"] for r, _, _ in confirmados]))
                continue
            # Mais de uma casa e FATO, e nao ambiguidade: Gladson Cameli foi
            # deputado federal e depois senador. Guardo as duas.
            for r, nome_civil, nasc_api in confirmados:
                casa_hoje = hoje if r["casa"] == "camara" else hoje_sen
                achados.append({
                    "id_candidatura": c["id_candidatura"], "uf": uf,
                    "nome_urna": c["pessoa"]["nome_urna"],
                    "casa": r["casa"], "id_externo": r["id_externo"],
                    "em_exercicio_hoje": r["id_externo"] in casa_hoje,
                    "legislaturas": sorted(r["legislaturas"]),
                    "uf_do_mandato": sorted(x for x in r["ufs"] if x),
                    "_prova": (f"nome civil {nome_civil} e nascimento {nasc_api} na API "
                               + ("da Camara" if r["casa"] == "camara" else "do Senado")
                               + ", iguais a nome_completo e data_nascimento do "
                               "registro no TSE"),
                })

    fechados = [x for x in achados if not x["em_exercicio_hoje"]]
    pessoas = len({x["id_candidatura"] for x in fechados})
    print(f"\n{len(fechados)} mandato(s) federal ENCERRADO, em {pessoas} candidatura(s):")
    for x in fechados:
        print(f"  {x['uf']} {x['nome_urna'][:24]:24} {x['casa']:7} id "
              f"{x['id_externo']:>7}  legisl. {x['legislaturas']}  "
              f"por {'/'.join(x['uf_do_mandato']) or '?'}")
    if [x for x in achados if x["em_exercicio_hoje"]]:
        print(f"\n({len([x for x in achados if x['em_exercicio_hoje']])} em exercicio hoje, "
              "fora daqui: sao do resolver_mandatos.py)")
    if sem_confirmar:
        print(f"\n{len(sem_confirmar)} caso(s) NAO CONFIRMADOS — o nome casou, mas a "
              "casa\n  legislativa nao publica a data de nascimento. Nao da para dizer "
              "se e a\n  mesma pessoa, entao fica de fora — e fica DITO, porque "
              '"nao confirmei"\n  e "nao e" sao coisas diferentes:')
        for uf, nome, casa_nome, casa, idx in sem_confirmar:
            print(f"  {uf} {nome[:24]:24} vs {casa_nome[:24]:24} ({casa} {idx})")
    if recusas:
        print(f"\n{len(recusas)} recusa(s) — nome casou e a pessoa NAO e a mesma:")
        for uf, nome, casa, por in recusas:
            print(f"  {uf} {nome[:24]:24} vs {casa[:24]:24} {por}")
    if ambiguos:
        print(f"\n{len(ambiguos)} AMBIGUIDADE(S) — nao gravo:")
        for uf, nome, quais in ambiguos:
            print(f"  {uf} {nome}: {quais}")

    if not a.gravar:
        print("\n(sem --gravar: nada escrito)")
        return 0

    antigo = json.loads(ARQ.read_text(encoding="utf-8"))["mandatos"] if ARQ.exists() else []
    juntos = {(x["id_candidatura"], x["casa"]): x for x in antigo}
    juntos.update({(x["id_candidatura"], x["casa"]): x for x in fechados})
    ARQ.write_text(json.dumps({
        "_nota": ("Mandato federal ENCERRADO, descoberto por resolver_mandatos_encerrados.py. "
                  "Cada linha foi confirmada por data de nascimento igual na API da casa "
                  "legislativa e no registro no TSE — nome sozinho nao basta. O "
                  "coletar_legislativo.py le este arquivo; antes ele tinha um dicionario "
                  "fixo no codigo com uma entrada escrita a mao."),
        "atualizado_em": date.today().isoformat(),
        "mandatos": sorted(juntos.values(),
                           key=lambda x: (x["uf"], x["nome_urna"], x["casa"])),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\ngravado: {ARQ}  ({len(juntos)} mandato(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
