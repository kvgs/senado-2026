# -*- coding: utf-8 -*-
"""Procura materia de jornal sobre cada candidatura, por tema.

O QUE ELE ENTREGA: uma LISTA DE LEITURA, e nao acervo. A diferenca importa.
Folha e Estadao tem paywall e o corpo da materia nao chega ate aqui; o que chega
e manchete, veiculo, data e link. Quem le a materia e extrai a posicao e a
revisao humana. O script poupa a garimpagem, nao a leitura.

POR QUE AS TRAVAS SAO DURAS. Rodei a busca sem trava nenhuma e o retorno foi:

    busca "Simone Tebet educacao"   ->  "Marina defende chapa com Tebet"
    busca "Derrite seguranca"       ->  "Ao lado de Moro e Derrite, Flavio lanca plano"
    busca "Ricardo Salles 2026"     ->  "passar a boiada" (2020, do ministerio)

Os tres erros sao de tipos diferentes e todos ja aconteceram neste acervo:
pessoa errada (uma posicao do Andre do Prado saiu de materia sobre o Geraldo
Rufino), assunto errado, e epoca errada. Foram 49 remocoes de 122. Entao:

  1. VERBO DE FALA. O nome precisa ser seguido de "defende", "diz", "propoe" e
     afins em ate 30 caracteres. "Tebet defende fim da escala 6x1" passa;
     "Ao lado de Moro e Derrite, Flavio lanca" nao, porque depois de "Derrite"
     vem ", Flavio lanca". Isso e o que separa quem falou de quem foi citado.

  2. NENHUM OUTRO CANDIDATO ANTES. Se outra das 15 candidaturas aparece antes no
     titulo, a materia provavelmente e sobre ela.

  3. JANELA DE TEMPO. Fora de 2026 nao entra como proposta de campanha. Sai
     marcado como contexto anterior, e nunca se mistura com o resto.

  4. TETO POR CANDIDATURA E TEMA. Sem teto, quem tem mais imprensa ganha mais
     acervo — e cobertura de imprensa mede fama e verba de campanha, nao
     qualidade de candidatura. O projeto proibe medir isso.

ESCOLHER VEICULO E ATO EDITORIAL. A lista abaixo e uma escolha, e nao um dado.
Esta explicita para poder ser discutida e mudada.

Uso:
    python coletar_imprensa.py
    python coletar_imprensa.py --resumo
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime

from coletar_legislativo import sem_acento

RAIZ = pathlib.Path(__file__).resolve().parent
import argparse as _argparse

import acervo

# Qual estado esta ferramenta trabalha. --uf existe para nao ser preciso editar
# referencia.json e lembrar de voltar: esquecer de voltar escreveria no acervo
# errado achando que era o certo.
_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--uf", default=None)
_UF = (_ap.parse_known_args()[0].uf or acervo.uf_padrao()).upper()

DADOS = acervo.exige(_UF)          # dados/<uf>/ — acervo daquele estado
NACIONAL = acervo.NACIONAL         # dados/ — referencia, estados, mapa
SAIDA = DADOS / "_coleta_imprensa.json"
HOJE = date.today().isoformat()
UA = "Mozilla/5.0 (compativel; senado-2026/1.0; projeto civico)"

# Escolha editorial, sujeita a revisao. Criterio: redacao com ficha tecnica
# publica, correcao de erro sinalizada e cobertura de politica nacional.
VEICULOS = {
    "nexo jornal": "Nexo", "nexo": "Nexo",
    "folha de s.paulo": "Folha de S.Paulo", "folha": "Folha de S.Paulo",
    "estadao": "Estadão", "o estado de s. paulo": "Estadão",
    "g1": "G1", "bbc news brasil": "BBC News Brasil",
    "poder360": "Poder360", "agencia publica": "Agência Pública",
    "jota info": "JOTA", "jota": "JOTA",
    "congresso em foco": "Congresso em Foco",
    "agencia camara": "Agência Câmara", "agencia senado": "Agência Senado",
    "senado federal": "Agência Senado", "camara dos deputados": "Agência Câmara",
    "uol": "UOL", "valor economico": "Valor Econômico",
}

# Verbo que indica que a PESSOA falou, e nao que foi citada por outro.
FALA = (r"(defende|diz|afirma|prop[oõ]e|promete|critica|quer|anuncia|declara|"
        r"apresenta|cobra|nega|admite|rebate|explica|sugere|lan[çc]a|"
        r"defendeu|disse|afirmou|prop[oô]s|prometeu|criticou|anunciou)")

# Manchete sobre a DISPUTA, e nao sobre o que a candidatura defende. "Lanca
# pre-candidatura" e "rebate fulano" sao corrida de cavalo: dizem quem esta
# brigando com quem, e nada sobre o que a pessoa faria no mandato.
PROCESSO = (r"(pre-?candidat|lanca candidatura|registra candidatura|sera candidat|"
            r"nao sera candidat|chapa|vice de |disputa com|rebate|ingrato|"
            r"filia|federacao|convencao|urna|pesquisa|intencao de voto|"
            r"lidera|empat|ponto[s]? percentua)")

TETO_POR_TEMA = 4  # sem teto, o acervo passa a medir cobertura de imprensa

TERMOS = {
    "t1": "segurança pública", "t2": "educação", "t3": "saúde",
    "t4": "economia emprego", "t5": "transporte infraestrutura",
    "t6": "meio ambiente clima", "t7": "habitação moradia",
    "t8": "tecnologia internet", "t9": "cultura direitos humanos",
    "t10": "Congresso projeto de lei",
}


def buscar_rss(consulta: str) -> list[dict]:
    u = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(consulta) +
         "&hl=pt-BR&gl=BR&ceid=BR:pt-419")
    req = urllib.request.Request(u, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        s = r.read().decode("utf-8", "replace")
    saida = []
    for bloco in re.findall(r"<item>(.*?)</item>", s, re.S):
        def campo(tag):
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", bloco, re.S)
            return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""
        saida.append({"titulo": campo("title"), "url": campo("link"),
                      "veiculo": campo("source"), "data": campo("pubDate")})
    return saida


def normaliza_data(s: str) -> str:
    for f in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(s, f).date().isoformat()
        except ValueError:
            continue
    return ""


def quem_fala(titulo: str, nomes_alvo: list[str], outros: list[str]) -> tuple[bool, str]:
    """Decide se o titulo mostra a PESSOA falando. Devolve (aceita, motivo)."""
    t = sem_acento(titulo)
    pos = min((t.find(sem_acento(n)) for n in nomes_alvo if sem_acento(n) in t), default=-1)
    if pos < 0:
        return False, "o nome nao aparece no titulo"
    for o in outros:
        p = t.find(sem_acento(o))
        if 0 <= p < pos:
            return False, f'"{o}" aparece antes no titulo — a materia deve ser sobre essa pessoa'
    # A janela comeca DEPOIS do nome e e curta. Com janela larga vazou
    # "Ramuth nega disputa com Andre do Prado para vice de Tarcisio e afirma":
    # o "afirma" era do Ramuth, 30 caracteres adiante.
    fim_nome = pos + max(len(sem_acento(n)) for n in nomes_alvo if sem_acento(n) in t)
    depois = t[fim_nome:fim_nome + 28]
    if not re.search(r"^[^,;:]{0,12}" + FALA, depois):
        return False, "nenhum verbo de fala logo apos o nome — pode ser mencao, e nao declaracao"
    if re.search(PROCESSO, t):
        return False, "manchete de processo eleitoral (candidatura, chapa, disputa), e nao de proposta"
    return True, ""


def main() -> int:
    so_resumo = "--resumo" in sys.argv
    cands = json.loads((DADOS / "candidaturas.json").read_text(encoding="utf-8"))["candidaturas"]
    ref = json.loads((NACIONAL / "referencia.json").read_text(encoding="utf-8"))
    nome_tema = {t["id_tema"] if "id_tema" in t else t.get("id"): t.get("nome") for t in ref["temas"]}

    todos_nomes = {}
    for c in cands:
        p = c["pessoa"]
        n = [p["nome_urna"]]
        comp = p.get("nome_completo") or ""
        if comp:
            n.append(comp)
        # Sobrenome sozinho so quando e distintivo. "Salles" e; "Silva" nao.
        todos_nomes[c["id_candidatura"]] = n

    aceitos, recusados = [], []
    for c in cands:
        cid = c["id_candidatura"]
        alvo = todos_nomes[cid]
        outros = [n for k, v in todos_nomes.items() if k != cid for n in v]
        for tid, termo in TERMOS.items():
            consulta = f'"{alvo[0]}" {termo}'
            try:
                itens = buscar_rss(consulta)
            except Exception as e:
                print(f"   ! falha em {cid}/{tid}: {e}")
                continue
            guardados = 0
            for it in itens:
                if guardados >= TETO_POR_TEMA:
                    break
                veic = VEICULOS.get(sem_acento(it["veiculo"]))
                if not veic:
                    continue
                ok, motivo = quem_fala(it["titulo"], alvo, outros)
                d = normaliza_data(it["data"])
                reg = {"id_candidatura": cid, "tema": tid, "tema_nome": nome_tema.get(tid, tid),
                       "titulo": it["titulo"], "veiculo": veic, "data": d, "url": it["url"],
                       "consulta": consulta,
                       "epoca": "campanha 2026" if d[:4] == "2026" else "anterior a 2026"}
                if not ok:
                    reg["motivo_recusa"] = motivo
                    recusados.append(reg)
                    continue
                aceitos.append(reg)
                guardados += 1
            time.sleep(0.7)
        print(f">> {cid}: {sum(1 for a in aceitos if a['id_candidatura']==cid)} materias aceitas", flush=True)

    de_campanha = [a for a in aceitos if a["epoca"] == "campanha 2026"]
    print("\n" + "=" * 62)
    print(f"aceitas: {len(aceitos)}  (sendo {len(de_campanha)} de 2026)")
    print(f"recusadas pelas travas: {len(recusados)}")
    mot: dict[str, int] = {}
    for r in recusados:
        chave = r["motivo_recusa"].split("—")[0].strip()[:52]
        mot[chave] = mot.get(chave, 0) + 1
    for k, v in sorted(mot.items(), key=lambda x: -x[1]):
        print(f"   {v:4}  {k}")
    print("\nIsto e lista de leitura, e nao acervo: o corpo da materia esta atras de")
    print("paywall e a posicao so entra depois que alguem ler a materia inteira.")

    if so_resumo:
        print("\n(--resumo: nada foi escrito)")
        return 0
    SAIDA.write_text(json.dumps({
        "_nota": ("Lista de leitura, AGUARDANDO REVISAO. Manchete nao e posicao: "
                  "a posicao so nasce depois que alguem ler a materia e extrair a "
                  "citacao literal. Nao e lido pelo gerar_site.py."),
        "_coletado_em": HOJE,
        "_veiculos": sorted(set(VEICULOS.values())),
        "_teto_por_tema": TETO_POR_TEMA,
        "aceitas": aceitos,
        "recusadas": recusados,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nescrito: {SAIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
