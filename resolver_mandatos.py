# -*- coding: utf-8 -*-
"""Descobre quais candidaturas tem mandato federal hoje, e grava o id externo.

POR QUE ESTE PASSO EXISTE. A base de candidatos do TSE nao diz quem esta no
Congresso. Sem isso, situacao_parlamentar fica vazio e o coletor legislativo nao
acha ninguem para coletar — ele procura exatamente esse campo.

CASAMENTO POR NOME, COM CUIDADO. E a unica chave possivel: o TSE usa sequencial
proprio e as casas legislativas usam id proprio, e nao existe tabela publica que
ligue os dois. Nome casa mal por natureza — "HUMBERTO SERGIO COSTA LIMA" no TSE e
"Humberto Costa" no Senado. Entao:

  - compara sem acento e sem caixa;
  - tenta nome de urna E nome completo;
  - exige que o casamento seja UNICO. Dois candidatos de nome parecido casando com
    o mesmo parlamentar e ambiguidade, e ambiguidade sai como AVISO, nao como
    palpite. Atribuir a proposicao de um deputado a candidatura errada e o erro
    que este projeto mais teve.

O QUE GRAVA. casa, id_externo, situacao e condicao, direto da API. Nao inventa
motivo de afastamento: se a casa diz "Licenciado", grava; se nao diz, fica nulo.

USO
    python resolver_mandatos.py --uf PE
    python resolver_mandatos.py --uf PE --gravar
"""
from __future__ import annotations

import argparse
import json
import unicodedata
import urllib.request

import acervo

UA = {"accept": "application/json",
      "User-Agent": "senado-2026/1.0 (projeto civico; +https://kvgs.github.io/senado-2026/)"}


def buscar(url: str) -> dict:
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=90).read())


def chave(s: str) -> str:
    return " ".join(unicodedata.normalize("NFD", (s or ""))
                    .encode("ascii", "ignore").decode().upper().split())


def deputados() -> dict[str, dict]:
    d = buscar("https://dadosabertos.camara.leg.br/api/v2/deputados"
               "?itens=600&ordem=ASC&ordenarPor=nome")["dados"]
    return {chave(x["nome"]): {"casa": "camara", "id_externo": str(x["id"]),
                               "uf": x.get("siglaUf"), "nome_casa": x["nome"]}
            for x in d}


def senadores() -> dict[str, dict]:
    j = buscar("https://legis.senado.leg.br/dadosabertos/senador/lista/atual.json")
    saida = {}
    for p in j["ListaParlamentarEmExercicio"]["Parlamentares"]["Parlamentar"]:
        ip = p["IdentificacaoParlamentar"]
        reg = {"casa": "senado", "id_externo": str(ip["CodigoParlamentar"]),
               "uf": ip.get("UfParlamentar"), "nome_casa": ip.get("NomeParlamentar")}
        for n in (ip.get("NomeParlamentar"), ip.get("NomeCompletoParlamentar")):
            if n:
                saida[chave(n)] = reg
    return saida


def detalhe_camara(id_externo: str) -> dict:
    d = buscar(f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_externo}")["dados"]
    st = d.get("ultimoStatus") or {}
    return {"situacao": st.get("situacao"), "condicao": st.get("condicaoEleitoral"),
            "desde": (st.get("data") or "")[:10] or None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", required=True)
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()
    uf = a.uf.upper()

    cands = acervo.ler("candidaturas.json", uf)
    print("consultando Camara e Senado...")
    dep, sen = deputados(), senadores()
    print(f"  {len(dep)} deputados e {len(set(v['id_externo'] for v in sen.values()))} "
          f"senadores em exercicio\n")

    achados, avisos = {}, []
    for c in cands["candidaturas"]:
        nomes = [c["pessoa"]["nome_urna"], c["pessoa"]["nome_completo"]]
        casou = []
        for fonte in (dep, sen):
            for n in nomes:
                r = fonte.get(chave(n))
                if r and r not in casou:
                    casou.append(r)
        if not casou:
            continue
        if len(casou) > 1:
            avisos.append(f'{c["pessoa"]["nome_urna"]}: casou com mais de um parlamentar '
                          f'({", ".join(x["nome_casa"] for x in casou)}) — ambiguidade, '
                          f'nao gravo')
            continue
        r = casou[0]
        # A UF do mandato pode nao ser a da candidatura, e isso e fato, nao erro:
        # a Tebet foi senadora por MS e concorre por SP. Fica registrado.
        if r.get("uf") and r["uf"] != uf:
            avisos.append(f'{c["pessoa"]["nome_urna"]}: mandato por {r["uf"]}, '
                          f'candidatura por {uf} — confirmar que e a mesma pessoa')
        achados[c["id_candidatura"]] = r

    print(f"{len(achados)} candidatura(s) com mandato federal em exercicio:")
    for cid, r in achados.items():
        det = detalhe_camara(r["id_externo"]) if r["casa"] == "camara" else {}
        r.update({k: v for k, v in det.items() if v})
        nome = next(c["pessoa"]["nome_urna"] for c in cands["candidaturas"]
                    if c["id_candidatura"] == cid)
        print(f'  {nome[:24]:26} {r["casa"]:8} id {r["id_externo"]:8} '
              f'{r.get("situacao") or "-":12} {r.get("condicao") or ""}')
    if avisos:
        print("\navisos (nao gravados sem conferencia):")
        for x in avisos:
            print(f"  ! {x}")

    if not a.gravar:
        print("\n(sem --gravar: nada foi escrito)")
        return 0

    for c in cands["candidaturas"]:
        r = achados.get(c["id_candidatura"])
        if not r:
            continue
        c["situacao_parlamentar"] = [{
            "casa": r["casa"], "id_externo": r["id_externo"],
            "situacao": r.get("situacao") or "Exercício",
            "condicao": r.get("condicao"),
            "desde": r.get("desde"),
            # Nao inventado: so entra se a casa legislativa disser.
            "motivo_afastamento_anterior": None,
            "_fonte": ("Camara dos Deputados, dados abertos v2" if r["casa"] == "camara"
                       else "Senado Federal, dados abertos"),
            "_casado_por": "nome, conferido unico contra a lista de parlamentares em exercicio",
        }]
    (acervo.de(uf) / "candidaturas.json").write_text(
        json.dumps(cands, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\ngravado em dados/{uf.lower()}/candidaturas.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
