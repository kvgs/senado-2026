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


# Numeral romano em forma CANONICA. O teste solto "[ivxlcdm]+" casa com nome de
# gente: C, I e D sao todas letras romanas, entao "Cid" virava "CID" — e o mesmo
# valeria para Vivi, Lili, Mimi. A forma canonica so aceita subtracao valida
# (IV, IX, XL, XC, CD, CM), rejeita "cid" e continua aceitando II e XXIII.
ROMANO = r"m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})"


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
        elif i and re.fullmatch(ROMANO, b):           # numeral romano: Joao XXIII
            saida.append(p.upper()); duvida = True
        elif len(b) <= 2 and "." not in b and b == sem_acento(b):
            saida.append(p.upper()); duvida = True    # sigla ou inicial solta
        elif len(b) <= 2 and "." not in b:            # "Ze", "Jo": sigla nao tem acento
            saida.append(b.capitalize()); duvida = True
        elif "'" in b or "’" in b or "`" in b:   # D'Avila, Sant'Anna
            saida.append("'".join(x.capitalize() for x in re.split(r"['`]", p)))
            duvida = True
        elif "-" in b:
            saida.append("-".join(x.capitalize() for x in b.split("-")))
        else:
            saida.append(b.capitalize())
    texto = " ".join(saida)
    for padrao, troca in APOSTROFO:
        novo = re.sub(padrao, troca, texto)
        if novo != texto:
            texto, duvida = novo, True     # restaurado, e marcado para conferencia
    return texto, duvida


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
    # Acrescentados conforme apareceram nos estados novos. Invariantes ficam
    # iguais de proposito: "assistente social" nao flexiona, e forcar um -a ali
    # seria inventar palavra.
    "assistente": "assistente",
    "jornalista": "jornalista",
    "odontologo": "odontóloga",
    "economista": "economista",
    "agricultor": "agricultora",
    "bancario": "bancária",
    "policial": "policial",
    "militar": "militar",
    "tecnico": "técnica",
    "auxiliar": "auxiliar",
    "analista": "analista",
    "psicologo": "psicóloga",
    "sociologo": "socióloga",
    "historiador": "historiadora",
    "escritor": "escritora",
    "produtor": "produtora",
    "diretor": "diretora",
    "gerente": "gerente",
    "corretor": "corretora",
    "enfermeiro": "enfermeira",
    "assessor": "assessora",
    "sindicalista": "sindicalista",
    "dentista": "dentista",
    "veterinario": "veterinária",
    "farmaceutico": "farmacêutica",
    "arquiteto": "arquiteta",
    "contador": "contadora",
    "publicitario": "publicitária",
    "religioso": "religiosa",
    "artista": "artista",
    "atleta": "atleta",
    "motorista": "motorista",
    "bombeiro": "bombeira",
    "delegado": "delegada",
    "juiz": "juíza",
    "promotor": "promotora",
    "procurador": "procuradora",
    "empregado": "empregada",
    "funcionario": "funcionária",
    "operador": "operadora",
    "vendedor": "vendedora",
    "pecuarista": "pecuarista",
    "pedagogo": "pedagoga",
    "cientista": "cientista",
    "eletricista": "eletricista",
    "empreendedor": "empreendedora",
}

# O TSE grava alguns sobrenomes SEM o apostrofo: "MANUELA D AVILA",
# "CAROLINE SANT ANNA". Reproduzir isso na tela mostra o nome de uma pessoa
# grafado errado — e nao e conteudo, e transcricao, da mesma familia do caixa
# alta que ja normalizamos. Restauro os dois padroes documentados, guardo o
# original, e o caso continua marcado para conferencia humana.
APOSTROFO = (
    (r"\bD ([ÁAÃEIOU]\w*)", "d'" + '\\1'),
    (r"\bSant (\w+)", "Sant'" + '\\1'),
)


# Adjetivo que acompanha a ocupacao e concorda com ela. Flexionar so a palavra
# cabeca produzia "Servidora publico civil aposentado" — meio feminino, meio
# masculino, o que na tela fica pior do que nao flexionar nada.
MODIFICADOR = {
    "publico": "pública", "politico": "política", "agropecuario": "agropecuária",
    "aposentado": "aposentada", "civil": "civil", "federal": "federal",
    "municipal": "municipal", "estadual": "estadual", "militar": "militar",
    "autonomo": "autônoma", "rural": "rural", "urbano": "urbana",
    "domestico": "doméstica", "tecnico": "técnica", "administrativo": "administrativa",
}

# Onde a concordancia PARA. Depois de preposicao ou parentese comeca complemento,
# que nao concorda com a pessoa: "professora DE ensino medio" (o ensino e medio,
# nao a professora), "aposentada (EXCETO servidor publico)".
CORTA = {"de", "da", "do", "das", "dos", "em", "no", "na", "e", "ou", "exceto", "para"}


def ocupacao(bruta: str, genero: str) -> tuple[str, bool]:
    """Devolve (ocupacao apresentavel, precisa_de_conferencia).

    Flexiona a palavra cabeca E os adjetivos que concordam com ela, parando na
    primeira preposicao ou parentese — dali em diante e complemento."""
    texto = frase(bruta)
    if not texto or "FEMIN" not in (genero or "").upper():
        return texto, False
    partes = texto.split()
    chave = sem_acento(partes[0]).lower().strip("(),")
    if chave not in FEMININO:
        return texto, True                       # nao sei flexionar: marca
    nova = FEMININO[chave]
    saida = [nova[:1].upper() + nova[1:] if partes[0][:1].isupper() else nova]
    duvida = False
    concordando = True
    for p in partes[1:]:
        limpa = sem_acento(p).lower().strip("(),.")
        if not concordando:
            saida.append(p)
        elif limpa in CORTA or p.startswith("("):
            concordando = False; saida.append(p)
        elif limpa in MODIFICADOR:
            saida.append(p.replace(p.strip("(),."), MODIFICADOR[limpa]))
        elif limpa.endswith(("o", "os")):
            # concorda em masculino e nao esta na tabela: nao chuto, marco.
            saida.append(p); duvida = True
        else:
            saida.append(p)                      # invariavel: "civil", "social"
    return " ".join(saida), duvida


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

    # Registro duplicado da MESMA pessoa: mesmo numero, mesmo partido e mesma data
    # de nascimento. Acontece na base do TSE (Piaui tem um), e sem tratar o
    # segundo sobrescrevia o primeiro em silencio — o cadastro contava 21 e o site
    # mostrava 20.
    def pessoa_chave(l):
        return (l["NR_CANDIDATO"], l["SG_PARTIDO"], l.get("DT_NASCIMENTO"),
                sem_acento(l["NM_CANDIDATO"]).upper())

    por_pessoa: dict[tuple, list[dict]] = {}
    for l in titulares:
        por_pessoa.setdefault(pessoa_chave(l), []).append(l)
    duplicados = {k: v for k, v in por_pessoa.items() if len(v) > 1}

    partidos, coligacoes, duvidas = set(), {}, []
    saida = []
    vistos: set[tuple] = set()
    for l in sorted(titulares, key=lambda x: x["NR_CANDIDATO"]):
        chave = pessoa_chave(l)
        if chave in vistos:
            continue                      # ja entrou; os sequenciais vao juntos
        vistos.add(chave)
        outros = por_pessoa[chave]
        # As duvidas iam so para o terminal. Fechado o terminal, a marca sumia —
        # e o arquivo ficava com o nome normalizado sem dizer que era um palpite.
        # Agora cada uma tambem entra no registro da candidatura.
        meus: list[str] = []
        urna, d1 = capitalizar(l["NM_URNA_CANDIDATO"])
        completo, d2 = capitalizar(l["NM_CANDIDATO"])
        if d1 or d2:
            duvidas.append(f'{l["NR_CANDIDATO"]} {urna} / {completo}')
            meus.append(f'Nome normalizado do registro em caixa alta '
                        f'("{l["NM_URNA_CANDIDATO"]}" / "{l["NM_CANDIDATO"]}"): '
                        f'a regra nao resolve sozinha. Conferir a grafia.')

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
            meus.append(f'Ocupacao "{_ocup}": nao sei flexionar no feminino, '
                        f'ficou como o TSE gravou. Conferir.')
        # O TSE grafa alguns nomes sem apostrofo ("SANT ANNA"). Reproduzir o
        # registro e o certo, mas merece um olhar: foi assim que "Salles" sozinho
        # no cartao virou pergunta na revisao de Sao Paulo.
        if re.search(r"\bSant \w", l["NM_CANDIDATO"], re.I) or \
           re.search(r"\bD [A-Z]", l["NM_CANDIDATO"]):
            duvidas.append(f'{l["NR_CANDIDATO"]} {completo}: o TSE grafou sem apostrofo')
            meus.append(f'O TSE grafou "{l["NM_CANDIDATO"]}" sem apostrofo; '
                        f'restaurado para "{completo}". Conferir contra o registro.')

        sup = [n for _, n in sorted(sup_por_numero.get(l["NR_CANDIDATO"], []))]
        saida.append({
            # O numero de urna entra no id quando duas pessoas DIFERENTES tem o
            # mesmo nome de urna — outro caso, e certo de aparecer em 27 estados.
            "id_candidatura": (
                f'sen-{uf.lower()}-2026-{slug(l["NM_URNA_CANDIDATO"])}'
                if sum(1 for k in por_pessoa
                       if slug(k[3]) and slug(l["NM_URNA_CANDIDATO"]) ==
                       slug(por_pessoa[k][0]["NM_URNA_CANDIDATO"])) == 1
                else f'sen-{uf.lower()}-2026-{slug(l["NM_URNA_CANDIDATO"])}-{l["NR_CANDIDATO"]}'),
            "pessoa": {
                "nome_urna": urna,
                "nome_completo": completo,
                "data_nascimento": data_iso(l.get("DT_NASCIMENTO")),
                "escolaridade": frase(l.get("DS_GRAU_INSTRUCAO")) or None,
                "ocupacao_declarada": _ocup or None,
            },
            # A marca de conferencia mora no dado, e nao so no terminal de quem
            # rodou o script. Some quando alguem confere contra o registro.
            **({"_conferir_transcricao": meus} if meus else {}),
            "id_partido": slug(l["SG_PARTIDO"]),
            "id_coligacao": id_col,
            "cargo": "senador",
            "uf": uf,
            "ano": 2026,
            "numero_urna": l["NR_CANDIDATO"],
            "sequencial_tse": l["SQ_CANDIDATO"],
            # Quando a base traz mais de um registro da mesma pessoa, os outros
            # sequenciais ficam aqui. Descartar sem dizer seria esconder um fato
            # do registro eleitoral.
            **({"_sequenciais_duplicados": [o["SQ_CANDIDATO"] for o in outros[1:]],
                "_nota_duplicidade": (
                    f"A base do TSE traz {len(outros)} registros desta candidatura, com o "
                    "mesmo numero, partido e data de nascimento. Tratados como uma so "
                    "pessoa; os sequenciais de todos ficam registrados.")}
               if len(outros) > 1 else {}),
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


# Os quatro arquivos do acervo, vazios e com o motivo escrito. Eu criei os de
# Pernambuco a mao, e passo feito a mao e passo que o proximo estado esquece.
#
# ARQUIVO AUSENTE E DEFEITO DE INSTALACAO; arquivo presente e vazio, dizendo por
# que, e informacao. E a mesma distincao que o site faz para o leitor entre "nao
# aborda" e "nao localizamos" — vale para os nossos proprios arquivos.
def esqueleto(destino: pathlib.Path, est: dict) -> None:
    onde = acervo.por_extenso(est["uf"])
    vazios = {
        "documentos.json": {
            "_nota": ("Documentos que sustentam posicao: plano registrado no TSE, programa "
                      "partidario, site oficial, base de dados abertos, reportagem, "
                      f"entrevista. Vazio porque a coleta {onde} ainda nao comecou."),
            "documentos": []},
        "posicoes.json": {
            "_nota": ("Posicoes por candidatura e tema, cada uma com fonte, selo e estado de "
                      "cobertura. Vazio NAO significa que as candidaturas nao tem proposta: "
                      "significa que ainda nao procuramos."),
            "posicoes": []},
        "registros_legislativos.json": {
            "_nota": ("Selo azul: proposicoes e votos de quem tem ou teve mandato. Rode "
                      "resolver_mandatos.py e depois coletar_legislativo.py para preencher."),
            "registros": []},
        "pesquisas.json": {
            "_nota": ("Pesquisa de intencao de voto so entra com ficha tecnica completa e "
                      "numero de registro no TSE. Publicar numero sem ficha e pior que nao "
                      "publicar."),
            "_regra": ("Instituto, registro no TSE, periodo de campo, entrevistados, margem "
                       "de erro e nivel de confianca. Faltando um, nao publica."),
            "pesquisas": []},
    }
    for nome, conteudo in vazios.items():
        alvo = destino / nome
        if alvo.exists():
            continue
        alvo.write_text(json.dumps(conteudo, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  criado dados/{destino.name}/{nome}")


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
    # A diferenca so e problema se NAO estiver explicada por registro duplicado.
    _extra = sum(len(c.get("_sequenciais_duplicados") or []) for c in cands)
    _bate = len(cands) + _extra == est["candidaturas_tse"]
    print(f"  TSE diz {est['candidaturas_tse']}; montadas {len(cands)}"
          + (f" (+{_extra} registro(s) duplicado(s) fundido(s))" if _extra else "")
          + ("  OK" if _bate else "  DIVERGE — conferir"))
    print(f"  com suplentes: {sum(1 for c in cands if len(c['suplentes']) == 2)} de {len(cands)} com dois")
    _dup = [c for c in cands if c.get("_sequenciais_duplicados")]
    if _dup:
        print(f"  {len(_dup)} candidatura(s) com REGISTRO DUPLICADO na base do TSE "
              "(mesma pessoa, mais de um registro):")
        for c in _dup:
            print(f"     {c['numero_urna']} {c['pessoa']['nome_urna']} — "
                  f"{1 + len(c['_sequenciais_duplicados'])} registros")
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
    esqueleto(destino, est)

    # ---------------------------------------------------------------------
    # RECADASTRAR NAO PODE DESTRUIR ACERVO EXISTENTE.
    #
    # Este script reescreve candidaturas.json a partir do TSE. Rodado sobre um
    # acervo ja trabalhado, ele trocaria ids e apagaria campo curado a mao — e eu
    # fiz exatamente isso em Sao Paulo, num acervo com 41 posicoes revisadas.
    # Revertido a tempo, mas so porque conferi o diff.
    # ---------------------------------------------------------------------
    anterior = destino / "candidaturas.json"
    if anterior.exists():
        velho = {c["id_candidatura"]: c
                 for c in json.loads(anterior.read_text(encoding="utf-8"))["candidaturas"]}

        # TRAVA 1: id que muda quebra tudo o que aponta para ele. id_candidatura
        # liga posicoes, registros legislativos e classificacoes, e JSON nao tem
        # chave estrangeira que reclame — o estrago seria silencioso.
        novos_ids = {c["id_candidatura"] for c in cands}
        sumiram = sorted(set(velho) - novos_ids)
        if sumiram:
            raise SystemExit(
                f"PAROU: o cadastro novo nao produz {len(sumiram)} id(s) que ja existem "
                f"em dados/{uf.lower()}/candidaturas.json:" + chr(10)
                + chr(10).join("  " + s for s in sumiram[:8])
                + chr(10) + chr(10)
                + "id_candidatura e a chave que liga posicoes, registros e classificacoes."
                + chr(10)
                + "Trocar id exige migrar os arquivos que apontam para ele — outra operacao."
                + chr(10)
                + "Nada foi gravado.")

        # TRAVA 2: tudo o que o cadastro novo NAO produz e preservado. A lista
        # escrita a mao estava incompleta e perdeu oito campos.
        repostos = 0
        for c in cands:
            v = velho.get(c["id_candidatura"])
            if not v:
                continue
            for k, valor in v.items():
                if k not in c or c[k] in (None, [], {}, ""):
                    c[k] = valor
                    repostos += 1
            # pessoa tambem: o TSE nao tem bio nem observacao
            for k, valor in (v.get("pessoa") or {}).items():
                if k not in c["pessoa"] or not c["pessoa"].get(k):
                    c["pessoa"][k] = valor
        if repostos:
            print(f"  preservados do cadastro anterior: {repostos} campo(s) que o TSE "
                  "nao fornece")

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

    # A pagina inicial le daqui. Estado com cadastro mas sem revisao e "em
    # construcao": deixar como "nao comecamos" esconde o que ja existe, e marcar
    # como "publicado" promete o que nao existe.
    est_p = acervo.NACIONAL / "estados.json"
    est_d = json.loads(est_p.read_text(encoding="utf-8"))
    for e in est_d["estados"]:
        if e["uf"] == uf and e["acervo"] == "nao_comecamos":
            e["acervo"] = "em_construcao"
            est_p.write_text(json.dumps(est_d, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  estados.json: {uf} passa a 'em_construcao'")

    print(f"\nescrito: dados/{uf.lower()}/candidaturas.json")
    print(f"referencia.json: +{len(novos)} partido(s), +{len(coligacoes)} coligacao(oes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
