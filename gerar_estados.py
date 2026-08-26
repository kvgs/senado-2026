# -*- coding: utf-8 -*-
"""Monta dados/estados.json — a tabela das 27 unidades da federacao.

POR QUE ISTO VEM PRIMEIRO. O site tem 43 pontos onde "Sao Paulo" esta escrito a
mao: titulo, rotulos, os prompts do LLM no worker, e os e-mails que saem para os
gabinetes. Enquanto a UF for texto no codigo, cada estado novo e uma chance de
mandar para um gabinete do Ceara uma mensagem dizendo "escrevo como eleitor de
Sao Paulo". Erro que sai de casa.

Entao a UF passa a ser DADO. Este arquivo e a fonte.

O que cada campo serve:

  candidaturas    contagem do TSE, para a lista de estados dizer o tamanho sem
                  prometer acervo que nao existe.
  assembleia      nome da casa legislativa estadual. O site precisa dela para
                  dizer "ha registro legislativo, mas fora do nosso alcance" —
                  a frase que hoje esta chumbada como ALESP por causa do Andre
                  do Prado.
  acervo          'publicado', 'em_construcao' ou 'nao_comecamos'. A lista de
                  estados mostra isso: prometer 27 estados prontos quando um
                  esta pronto e o oposto da regra de que ausencia e informacao.

VAGAS. Em 2026 todo estado elege DOIS senadores — e a renovacao de dois tercos
(54 das 81 cadeiras). Nao e por estado, e uniforme, entao fica fora da tabela e
mora no texto nacional.
"""
import csv
import io
import json
import pathlib
import zipfile
from collections import Counter

RAIZ = pathlib.Path(r"c:\Users\BOC277 - Usuario\Documents\politica")

# Nome da casa legislativa de cada estado, escrito como a propria casa se chama.
# Nao da para derivar de sigla: o DF tem Camara Legislativa, e nao Assembleia.
ASSEMBLEIA = {
    "AC": "Assembleia Legislativa do Estado do Acre",
    "AL": "Assembleia Legislativa do Estado de Alagoas",
    "AP": "Assembleia Legislativa do Estado do Amapá",
    "AM": "Assembleia Legislativa do Estado do Amazonas",
    "BA": "Assembleia Legislativa do Estado da Bahia",
    "CE": "Assembleia Legislativa do Estado do Ceará",
    "DF": "Câmara Legislativa do Distrito Federal",
    "ES": "Assembleia Legislativa do Estado do Espírito Santo",
    "GO": "Assembleia Legislativa do Estado de Goiás",
    "MA": "Assembleia Legislativa do Estado do Maranhão",
    "MT": "Assembleia Legislativa do Estado de Mato Grosso",
    "MS": "Assembleia Legislativa do Estado de Mato Grosso do Sul",
    "MG": "Assembleia Legislativa do Estado de Minas Gerais",
    "PA": "Assembleia Legislativa do Estado do Pará",
    "PB": "Assembleia Legislativa do Estado da Paraíba",
    "PR": "Assembleia Legislativa do Estado do Paraná",
    "PE": "Assembleia Legislativa do Estado de Pernambuco",
    "PI": "Assembleia Legislativa do Estado do Piauí",
    "RJ": "Assembleia Legislativa do Estado do Rio de Janeiro",
    "RN": "Assembleia Legislativa do Estado do Rio Grande do Norte",
    "RS": "Assembleia Legislativa do Estado do Rio Grande do Sul",
    "RO": "Assembleia Legislativa do Estado de Rondônia",
    "RR": "Assembleia Legislativa do Estado de Roraima",
    "SC": "Assembleia Legislativa do Estado de Santa Catarina",
    "SP": "Assembleia Legislativa do Estado de São Paulo",
    "SE": "Assembleia Legislativa do Estado de Sergipe",
    "TO": "Assembleia Legislativa do Estado do Tocantins",
}

NOME = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal",
    "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco",
    "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima",
    "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe",
    "TO": "Tocantins",
}

# Como o nome entra numa frase: "eleitor(a) DE São Paulo", "DO Acre", "DA Bahia".
# Sem isto o texto sai errado em metade dos estados, e texto errado sobre a UF
# e justamente o que sai numa mensagem para gabinete.
PREPOSICAO = {
    "AC": "do", "AL": "de", "AP": "do", "AM": "do", "BA": "da", "CE": "do",
    "DF": "do", "ES": "do", "GO": "de", "MA": "do", "MT": "de", "MS": "de",
    "MG": "de", "PA": "do", "PB": "da", "PR": "do", "PE": "de", "PI": "do",
    "RJ": "do", "RN": "do", "RS": "do", "RO": "de", "RR": "de", "SC": "de",
    "SP": "de", "SE": "de", "TO": "do",
}

REGIAO = {
    "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MT", "MS"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
}
REGIAO_DE = {uf: r for r, ufs in REGIAO.items() for uf in ufs}


def contar_candidaturas() -> Counter:
    c = Counter()
    with zipfile.ZipFile(RAIZ / "fontes" / "consulta-candidatos-2026.zip") as f:
        nome = [n for n in f.namelist() if n.endswith("BRASIL.csv")][0]
        with f.open(nome) as fh:
            for lin in csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"), delimiter=";"):
                if "SENADOR" in (lin.get("DS_CARGO") or "").upper():
                    c[lin.get("SG_UF")] += 1
    return c


def main():
    cont = contar_candidaturas()
    faltam = sorted(set(NOME) - set(cont))
    if faltam:
        raise SystemExit(f"UF sem candidatura no arquivo do TSE: {faltam} — confira a fonte")

    estados = []
    for uf in sorted(NOME):
        estados.append({
            "uf": uf,
            "nome": NOME[uf],
            "preposicao": PREPOSICAO[uf],
            "regiao": REGIAO_DE[uf],
            "candidaturas_tse": cont[uf],
            "assembleia": ASSEMBLEIA[uf],
            # SP e o unico com acervo. Dizer o contrario na lista de estados
            # seria prometer o que nao existe.
            "acervo": "publicado" if uf == "SP" else "nao_comecamos",
        })

    saida = RAIZ / "dados" / "estados.json"
    saida.write_text(json.dumps({
        "_nota": ("As 27 unidades da federacao. A UF deixa de ser texto escrito a mao no "
                  "codigo e passa a ser dado: eram 43 pontos com 'Sao Paulo' chumbado, "
                  "incluindo os prompts do LLM e os e-mails que saem para gabinetes. "
                  "'preposicao' existe porque 'eleitor de Sao Paulo' e 'eleitor do Acre' "
                  "nao seguem a mesma regra, e concordancia errada numa mensagem enviada "
                  "a um gabinete e erro que sai de casa."),
        "_vagas_2026": ("Em 2026 cada estado elege DOIS senadores: e a renovacao de dois "
                        "tercos do Senado, 54 das 81 cadeiras. E uniforme, entao nao entra "
                        "por estado."),
        "_contagem": "candidaturas_tse vem de consulta_cand_2026_BRASIL.csv, cargo SENADOR.",
        "estados": estados,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"dados/estados.json: {len(estados)} unidades, "
          f"{sum(e['candidaturas_tse'] for e in estados)} candidaturas")
    for r in REGIAO:
        ufs = [e for e in estados if e["regiao"] == r]
        print(f"  {r:14} {len(ufs)} UF · {sum(e['candidaturas_tse'] for e in ufs)} candidaturas")


if __name__ == "__main__":
    main()
