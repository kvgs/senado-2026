# -*- coding: utf-8 -*-
"""Da a cada registro legislativo o link da SUA proposicao.

O PROBLEMA
As posicoes vindas da Camara apontavam para https://dadosabertos.camara.leg.br/api/v2
— a raiz da API. O link existia e nao levava a lugar nenhum util. E os 32
registros legislativos apareciam no site sem link nenhum.

Num projeto cuja regra central e "toda informacao mostra de onde veio, com link",
apontar para a raiz de uma API e pior que nao apontar: parece procedencia sem ser.

A CONFERENCIA QUE IMPORTA
Nao basta achar uma proposicao com o mesmo tipo, numero e ano — a Camara tem
proposicoes com a mesma numeracao em contextos diferentes, e apontar para a
errada seria exatamente o erro que a revisao acabou de encontrar nos dados.
Entao cada resultado tem a ementa comparada com a nossa. Se nao bater o
suficiente, o registro fica SEM link e com a divergencia anotada, para conferir
a mao.

USO
    python resolver_links_legislativos.py --simular
    python resolver_links_legislativos.py --gravar
"""
import argparse
import json
import pathlib
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

RAIZ = pathlib.Path(__file__).resolve().parent
ARQ = RAIZ / "dados" / "registros_legislativos.json"
AGENTE = "senado-sp-2026/1.0 (+https://kvgs.github.io/senado-sp-2026/)"
FICHA = "https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={}"
MATERIA = "https://www25.senado.leg.br/web/atividade/materias/-/materia/{}"
MIN_SEMELHANCA = 0.60


def normaliza(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", s).split()


def semelhanca(a, b):
    """Fracao das palavras significativas da nossa ementa presentes na deles."""
    pa = {p for p in normaliza(a) if len(p) > 3}
    pb = {p for p in normaliza(b) if len(p) > 3}
    if not pa:
        return 0.0
    return len(pa & pb) / len(pa)


def buscar_senado(tipo, numero, ano):
    """Usa /processo, que e o substituto oficial do servico que o proprio Senado
    marcou como descontinuado em 01/02/2026."""
    q = urllib.parse.urlencode({"sigla": tipo, "numero": numero, "ano": ano})
    req = urllib.request.Request(
        f"https://legis.senado.leg.br/dadosabertos/processo?{q}",
        headers={"Accept": "application/json", "User-Agent": AGENTE},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            d = json.loads(r.read().decode("utf-8"))
            return d if isinstance(d, list) else []
    except (urllib.error.URLError, ValueError) as e:
        print(f"    erro ao consultar: {e}")
        return []


def buscar_camara(tipo, numero, ano):
    q = urllib.parse.urlencode({"siglaTipo": tipo, "numero": numero, "ano": ano})
    req = urllib.request.Request(
        f"https://dadosabertos.camara.leg.br/api/v2/proposicoes?{q}",
        headers={"accept": "application/json", "User-Agent": AGENTE},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode("utf-8")).get("dados", [])
    except (urllib.error.URLError, ValueError) as e:
        print(f"    erro ao consultar: {e}")
        return []


def main():
    ap = argparse.ArgumentParser(description="Resolve o link de cada registro legislativo.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--simular", action="store_true", help="mostra o que faria, sem gravar")
    g.add_argument("--gravar", action="store_true", help="grava os links no arquivo")
    a = ap.parse_args()

    dados = json.loads(ARQ.read_text(encoding="utf-8"))
    regs = dados["registros"]

    resolvidos = divergentes = nao_achados = 0

    for r in regs:
        rotulo = f"{r['tipo']} {r['numero']}/{r['ano']}"
        print(f"{rotulo:16} {r['casa']:8}", end="  ")

        if r["casa"] == "senado":
            bruto = r.get("id_externo_senado")
            if not bruto:
                achados = buscar_senado(r["tipo"], r["numero"], r["ano"])
                time.sleep(0.4)
                if not achados:
                    print("nada encontrado na API do Senado — fica sem link")
                    r["_pendencia_link"] = "Materia nao localizada na API do Senado."
                    nao_achados += 1
                    continue
                melhor = max(achados, key=lambda x: semelhanca(r["ementa"], x.get("ementa") or ""))
                s = semelhanca(r["ementa"], melhor.get("ementa") or "")
                if s < MIN_SEMELHANCA:
                    print(f"ementa NAO bate ({s:.0%}) — fica sem link")
                    r["_pendencia_link"] = (
                        f"Materia {melhor.get('codigoMateria')} tem mesmo tipo/numero/ano, mas a "
                        f"ementa coincide apenas {s:.0%}. Conferir a mao.")
                    divergentes += 1
                    continue
                bruto = melhor.get("codigoMateria")
                r["id_externo_senado"] = str(bruto)
                r["url"] = MATERIA.format(bruto)
                r["url_conferida_em"] = date.today().isoformat()
                r["url_base"] = f"API /processo do Senado, ementa confere {s:.0%}"
                r.pop("_pendencia_link", None)
                print(f"ok  materia {bruto}  (ementa {s:.0%})")
                resolvidos += 1
                continue
            codigo = str(bruto).split("-")[0]
            r["url"] = MATERIA.format(codigo)
            r["url_conferida_em"] = date.today().isoformat()
            r["url_base"] = "id da materia ja registrado no acervo"
            print(f"ok  materia {codigo}")
            resolvidos += 1
            continue

        achados = buscar_camara(r["tipo"], r["numero"], r["ano"])
        time.sleep(0.4)                      # cortesia com a API publica

        if not achados:
            print("nada encontrado na API — fica sem link")
            r.pop("url", None)
            r["_pendencia_link"] = "Proposicao nao localizada na API da Camara por tipo/numero/ano."
            nao_achados += 1
            continue

        melhor = max(achados, key=lambda x: semelhanca(r["ementa"], x.get("ementa") or ""))
        s = semelhanca(r["ementa"], melhor.get("ementa") or "")

        if s < MIN_SEMELHANCA:
            print(f"ementa NAO bate ({s:.0%}) — fica sem link")
            print(f"      nossa : {r['ementa'][:90]}")
            print(f"      deles : {(melhor.get('ementa') or '')[:90]}")
            r.pop("url", None)
            r["_pendencia_link"] = (
                f"Encontrada proposicao id {melhor['id']} com mesmo tipo/numero/ano, mas a ementa "
                f"coincide apenas {s:.0%}. Nao vinculada: apontar para a proposicao errada seria "
                "pior que nao apontar. Conferir a mao."
            )
            divergentes += 1
            continue

        r["url"] = FICHA.format(melhor["id"])
        r["id_camara"] = melhor["id"]
        r["url_conferida_em"] = date.today().isoformat()
        r["url_base"] = f"API da Camara, ementa confere {s:.0%}"
        r.pop("_pendencia_link", None)
        print(f"ok  id {melhor['id']}  (ementa {s:.0%})")
        resolvidos += 1

    print()
    print(f"resolvidos: {resolvidos} · ementa divergente: {divergentes} · nao achados: {nao_achados}")

    if a.simular:
        print("\nSimulacao: nada gravado. Use --gravar.")
        return 0

    dados["_regra_link"] = (
        "Cada registro traz o link da sua propria proposicao. Registro cuja ementa nao confere "
        "com a da casa legislativa fica SEM link e com a divergencia anotada: apontar para a "
        "proposicao errada seria pior que nao apontar."
    )
    ARQ.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print("gravado em dados/registros_legislativos.json")
    print("agora rode: python gerar_site.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
