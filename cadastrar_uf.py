# -*- coding: utf-8 -*-
"""Monta dados/<uf>/candidaturas.json da base de candidatos do TSE.

FONTE PRIMARIA, e nao espelho. O cadastro de Sao Paulo veio de um espelho do
Nexo, porque o TSE direto respondia 403 — e foi esse espelho, tipado como
reportagem, que sustentou 15 posicoes reprovadas depois. Agora a base do TSE esta
baixada aqui, e o cadastro sai dela: selo oficial, sem intermediario.

O QUE ESTA BASE TEM E O QUE NAO TEM. Ela nao traz tudo o que o modelo guarda, e
os campos ausentes ficam nulos COM O MOTIVO ESCRITO, em vez de sumirem:

  situacao_registro     vem "#NE" (nao especificado) neste extrato. Registrar
                        "aguardando julgamento" sem ter lido isso em lugar nenhum
                        seria inventar.
  bens_declarados_brl   esta em outro conjunto do TSE (bens de candidato), que
                        ainda nao baixamos.
  mandatos_anteriores   exige a serie historica de candidaturas, outro conjunto.
  contato               so de fonte oficial. Este extrato tem coluna de e-mail,
                        mas ela vem VAZIA nas 12 de PE — entao nao ha o que usar.

CPF E TITULO NAO SAEM DAQUI. A base tem as duas colunas. Nenhuma e lida.

NOME EM CAIXA ALTA. O TSE grava "PAULO RUBEM SANTIAGO". Exibir assim grita, e
capitalizar palavra por palavra produz "Paulo Rubem Santiago Da Silva" — com "Da"
maiusculo, que esta errado em portugues. As particulas ficam minusculas, e todo
nome que a regra nao resolve com seguranca sai marcado para conferencia humana.

USO
    python cadastrar_uf.py --uf PE            # mostra o que faria
    python cadastrar_uf.py --uf PE --gravar   # escreve
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import pathlib
import re
import unicodedata
import zipfile

import acervo

AQUI = pathlib.Path(__file__).resolve().parent
BASE_TSE = AQUI / "fontes" / "consulta-candidatos-2026.zip"

# Particulas que ficam minusculas no meio do nome. "Da", "Do", "Dos" com inicial
# maiuscula e erro de portugues, e aparece no nome de uma pessoa na tela.
PARTICULAS = {"da", "de", "do", "das", "dos", "e", "di", "du", "del", "la", "van", "von"}

# Palavras que o TSE grava abreviadas ou como titulo, e que NAO sao nome proprio
# a capitalizar de forma ingenua.
FIXAS = {"dr": "Dr.", "dra": "Dra.", "pr": "Pr.", "pastor": "Pastor",
         "cel": "Cel.", "sgt": "Sgt.", "prof": "Prof.", "profa": "Profa.",
         "jr": "Jr.", "neto": "Neto", "filho": "Filho", "sobrinho": "Sobrinho"}


def sem_acento(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()


def slug(s: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", sem_acento(s).lower())).strip("-")


def capitalizar(nome: str) -> tuple[str, bool]:
    """Devolve (nome apresentavel, precisa_de_conferencia).

    Marca para conferencia quando a regra nao basta: sigla, nome de uma letra,
    numero romano, apostrofo. Nome de pessoa errado na tela e erro visivel, e
    melhor pedir um olhar do que chutar."""
    partes = nome.strip().split()
    saida, duvida = [], False
    for i, p in enumerate(partes):
        b = p.lower()
        if b.strip(".") in FIXAS:
            saida.append(FIXAS[b.strip(".")])
        elif b in PARTICULAS and i not in (0, len(partes) - 1):
            saida.append(b)
        elif re.fullmatch(r"[ivxlcdm]+", b):          # numeral romano: Joao XXIII
            saida.append(p.upper()); duvida = True
        elif len(b) <= 2 and "." not in b:            # sigla ou inicial solta
            saida.append(p.upper()); duvida = True
        elif "'" in b or "`" in b:                    # D'Avila, Sant'Anna
            saida.append("'".join(x.capitalize() for x in re.split(r"['`]", p)))
            duvida = True
        elif "-" in b:
            saida.append("-".join(x.capitalize() for x in b.split("-")))
        else:
            saida.append(b.capitalize())
    return " ".join(saida), duvida


def frase(s: str) -> str:
    """Caixa de frase, como Sao Paulo guarda: "Ensino medio completo". O TSE grava
    tudo em caixa alta, e caixa de titulo ("Ensino Médio Completo") deixaria o
    mesmo campo com dois formatos no mesmo site."""
    s = (s or "").strip().lower()
    return s[:1].upper() + s[1:] if s else ""


# Ocupacao no feminino. Tabela explicita: regra cega em -o acerta "medico" e
# erra "porta-voz". O que nao esta aqui sai marcado para conferencia.
FEMININO = {
    "advogado": "advogada",
    "aposentado": "aposentada",
    "deputado": "deputada",
    "senador": "senadora",
    "engenheiro": "engenheira",
    "professor": "professora",
    "empresario": "empresária",
    "comerciante": "comerciante",
    "medico": "médica",
    "servidor": "servidora",
    "trabalhador": "trabalhadora",
    "pastor": "pastora",
    "vereador": "vereadora",
    "administrador": "administradora",
    "outros": "outros",
    "estudante": "estudante",
}


def ocupacao(bruta: str, genero: str) -> tuple[str, bool]:
    """Devolve (ocupacao apresentavel, precisa_de_conferencia).

    Flexiona so a PRIMEIRA palavra: no vocabulario do TSE e ela que carrega o
    genero ("professor de ensino medio"). O resto e complemento e nao muda."""
    texto = frase(bruta)
    if not texto or "FEMIN" not in (genero or "").upper():
        return texto, False
    partes = texto.split(" ", 1)
    chave = sem_acento(partes[0]).lower().strip("(),")
    if chave not in FEMININO:
        return texto, True                       # nao sei flexionar: marca
    nova = FEMININO[chave]
    nova = nova[:1].upper() + nova[1:] if partes[0][:1].isupper() else nova
    return (nova + (" " + partes[1] if len(partes) > 1 else "")), False


def linhas_tse(uf: str) -> list[dict]:
    if not BASE_TSE.exists():
        raise SystemExit(f"nao achei {BASE_TSE}. Baixe a base de candidatos do TSE antes.")
    with zipfile.ZipFile(BASE_TSE) as z:
        nome = [n for n in z.namelist() if n.endswith("BRASIL.csv")][0]
        with z.open(nome) as fh:
            return [l for l in csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"),
                                              delimiter=";")
                    if l.get("SG_UF") == uf]


def data_iso(br: str) -> str | None:
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", (br or "").strip())
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def montar(uf: str) -> tuple[list[dict], set, dict, list[str]]:
    linhas = linhas_tse(uf)
    titulares = [l for l in linhas if l["DS_CARGO"].strip().upper() == "SENADOR"]
    if not titulares:
        raise SystemExit(f"nenhuma candidatura a senador em {uf} na base do TSE")

    # Suplente casa pelo NUMERO DE URNA: conferido, 12 de 12 em PE. Coligacao nao
    # serve — nove coligacoes para doze chapas.
    sup_por_numero: dict[str, list[tuple[str, str]]] = {}
    for l in linhas:
        c = l["DS_CARGO"].strip().upper()
        if "SUPLENTE" in c:
            n, _ = capitalizar(l["NM_URNA_CANDIDATO"] or l["NM_CANDIDATO"])
            sup_por_numero.setdefault(l["NR_CANDIDATO"], []).append((c, n))

    partidos, coligacoes, duvidas = set(), {}, []
    saida = []
    for l in sorted(titulares, key=lambda x: x["NR_CANDIDATO"]):
        urna, d1 = capitalizar(l["NM_URNA_CANDIDATO"])
        completo, d2 = capitalizar(l["NM_CANDIDATO"])
        if d1 or d2:
            duvidas.append(f'{l["NR_CANDIDATO"]} {urna} / {completo}')

        partidos.add((l["SG_PARTIDO"], l["NM_PARTIDO"]))

        # "PARTIDO ISOLADO" nao e coligacao: e a ausencia dela.
        nc = (l.get("NM_COLIGACAO") or "").strip()
        id_col = None
        if nc and nc.upper() != "PARTIDO ISOLADO":
            id_col = f'{slug(nc)}-{uf.lower()}'
            coligacoes[id_col] = {
                "id_coligacao": id_col,
                "nome": capitalizar(nc)[0],
                "ano": 2026, "uf": uf, "cargo": "senador",
                "composicao": (l.get("DS_COMPOSICAO_COLIGACAO") or "").strip(),
            }

        _ocup, _d3 = ocupacao(l.get("DS_OCUPACAO"), l.get("DS_GENERO"))
        if _d3:
            duvidas.append(f'{l["NR_CANDIDATO"]} {urna}: nao sei flexionar '
                           f'"{_ocup}" no feminino')
        # O TSE grafa alguns nomes sem apostrofo ("SANT ANNA"). Reproduzir o
        # registro e o certo, mas merece um olhar: foi assim que "Salles" sozinho
        # no cartao virou pergunta na revisao de Sao Paulo.
        if re.search(r"\bSant \w", l["NM_CANDIDATO"], re.I) or \
           re.search(r"\bD [A-Z]", l["NM_CANDIDATO"]):
            duvidas.append(f'{l["NR_CANDIDATO"]} {completo}: o TSE grafou sem apostrofo')

        sup = [n for _, n in sorted(sup_por_numero.get(l["NR_CANDIDATO"], []))]
        saida.append({
            "id_candidatura": f'sen-{uf.lower()}-2026-{slug(l["NM_URNA_CANDIDATO"])}',
            "pessoa": {
                "nome_urna": urna,
                "nome_completo": completo,
                "data_nascimento": data_iso(l.get("DT_NASCIMENTO")),
                "escolaridade": frase(l.get("DS_GRAU_INSTRUCAO")) or None,
                "ocupacao_declarada": _ocup or None,
            },
            "id_partido": slug(l["SG_PARTIDO"]),
            "id_coligacao": id_col,
            "cargo": "senador",
            "uf": uf,
            "ano": 2026,
            "numero_urna": l["NR_CANDIDATO"],
            "sequencial_tse": l["SQ_CANDIDATO"],
            # Ausencias com o motivo escrito, e nao campos omitidos.
            "bens_declarados_brl": None,
            "_bens_ausente": "Esta no conjunto 'bens de candidato' do TSE, ainda nao baixado.",
            "suplentes": sup,
            "situacao_registro": [],
            "_situacao_ausente": ("A base de candidatos traz DS_SITUACAO_CANDIDATURA como "
                                  "'#NE' (nao especificado) neste extrato. Registrar uma "
                                  "situacao sem ter lido seria inventar."),
            "mandatos_anteriores": [],
            "_mandatos_ausente": ("Exige a serie historica de candidaturas do TSE, outro "
                                  "conjunto. Vazio aqui NAO significa primeira eleicao."),
            "contato": {"email": None, "email_fonte": None, "email_tipo": None,
                        "instagram": None, "redes": []},
            "_contato_ausente": ("So entra contato de fonte oficial. A coluna de e-mail deste "
                                 "extrato vem vazia; para quem tem mandato, o contato sai dos "
                                 "dados abertos da casa legislativa."),
            "foto": None,
            "situacao_parlamentar": [],
        })
    return saida, partidos, coligacoes, duvidas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", required=True)
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()
    uf = a.uf.upper()

    est = acervo.estado(uf)                     # valida a UF contra estados.json
    cands, partidos, coligacoes, duvidas = montar(uf)

    ref = acervo.ref()
    ja = {p["sigla"] for p in ref["partidos"]}
    novos = sorted(p for p in partidos if p[0] not in ja)

    print(f"{est['nome']} ({uf}) — {len(cands)} candidaturas ao Senado")
    print(f"  TSE diz {est['candidaturas_tse']}; montadas {len(cands)}"
          + ("  OK" if len(cands) == est["candidaturas_tse"] else "  DIVERGE"))
    print(f"  com suplentes: {sum(1 for c in cands if len(c['suplentes']) == 2)} de {len(cands)} com dois")
    print(f"  coligacoes: {len(coligacoes)} · partidos novos para a referencia: "
          f"{', '.join(s for s, _ in novos) or 'nenhum'}")
    if duvidas:
        print(f"\n  {len(duvidas)} nome(s) que a regra de capitalizacao nao resolve sozinha —")
        print("  conferir contra o registro antes de publicar:")
        for d in duvidas:
            print(f"     {d}")
    print()
    for c in cands:
        print(f"  {c['numero_urna']:>4}  {c['pessoa']['nome_urna'][:26]:28} "
              f"{c['id_partido'].upper():10} {len(c['suplentes'])} supl.")

    if not a.gravar:
        print("\n(sem --gravar: nada foi escrito)")
        return 0

    for sigla, nome in novos:
        ref["partidos"].append({"id_partido": slug(sigla), "sigla": sigla,
                                "nome": capitalizar(nome)[0]})
    ids = {c["id_coligacao"] for c in ref["coligacoes"]}
    for c in coligacoes.values():
        if c["id_coligacao"] not in ids:
            ref["coligacoes"].append(c)
    ref["partidos"].sort(key=lambda p: p["sigla"])
    (acervo.NACIONAL / "referencia.json").write_text(
        json.dumps(ref, ensure_ascii=False, indent=1), encoding="utf-8")

    destino = acervo.NACIONAL / uf.lower()
    destino.mkdir(exist_ok=True)
    (destino / "candidaturas.json").write_text(json.dumps({
        "_nota": ("Pessoa e candidatura no mesmo arquivo. Nenhum CPF e nenhum titulo "
                  "eleitoral aqui: por principio, nao saem da base do TSE para o acervo."),
        "_data_referencia": ref.get("site", {}).get("_extrato_tse", "2026-08-26"),
        "_fonte_registro": ("TSE — Consulta de candidatos 2026, arquivo "
                            "consulta_cand_2026_BRASIL.csv. Fonte primaria, sem espelho. "
                            "Nivel: oficial."),
        "_gerado_por": "cadastrar_uf.py",
        "candidaturas": cands,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\nescrito: dados/{uf.lower()}/candidaturas.json")
    print(f"referencia.json: +{len(novos)} partido(s), +{len(coligacoes)} coligacao(oes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
