# -*- coding: utf-8 -*-
"""Coleta pronunciamentos em plenario — a candidatura falando, no registro oficial.

POR QUE ISTO VEIO ANTES DA IMPRENSA. O pedido era coletar jornais. Testei o
Google Noticias com recorte tematico e o retorno foi este:

    busca "Simone Tebet educacao"  ->  "Marina defende chapa com Tebet"
    busca "Derrite seguranca"      ->  "Flavio lanca plano de seguranca"
    busca "Ricardo Salles 2026"    ->  "passar a boiada" (2020, do ministerio)

Nome na manchete nao e a pessoa falando. E exatamente o erro que tirou 49 das
122 posicoes na revisao — inclusive uma atribuida ao Andre do Prado a partir de
materia sobre o Geraldo Rufino. O coletor de imprensa existe (coletar_imprensa.py)
e aplica trava para isso, mas a precisao dele e baixa por natureza.

O discurso em plenario nao tem esse problema:

  - A atribuicao esta dentro do proprio texto: "O SR. RICARDO SALLES (NOVO - SP)".
  - E a pessoa falando, em primeira pessoa. Nao e alguem resumindo o que ela disse.
  - Vem com INDEXACAO TEMATICA DA PROPRIA CASA (keywords na Camara, Indexacao no
    Senado). O tema deixa de ser palpite meu por palavra-chave e passa a ser
    vocabulario controlado de quem registrou a sessao.
  - Nao tem paywall, nao tem robots.txt, nao tem direito autoral: e registro
    publico.
  - Resolve justamente as quatro candidaturas que aparecem vazias no site.

O QUE ELE NAO FAZ. Nao escreve no acervo. Discurso e 🟣 declaracao do candidato
registrada em 🔵 registro oficial: prova que a pessoa DISSE, nunca que o que ela
disse e verdade. E a transcricao vem "sem revisao do orador", o que fica gravado
em cada registro.

Fora ficam pronunciamentos cerimoniais — homenagem, pesar, despedida, saudacao.
Nao dizem o que a candidatura defende, e entupiriam a revisao.

Uso:
    python coletar_discursos.py
    python coletar_discursos.py --resumo
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import date

from coletar_legislativo import buscar, sem_acento, sugerir_temas

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
SAIDA = DADOS / "_coleta_discursos.json"
HOJE = date.today().isoformat()

# Pronunciamento cerimonial. Nao diz o que a candidatura defende.
CERIMONIAL = [
    "homenage", "pesar", "falecimento", "despedida", "saudacao", "congratula",
    "aniversario", "posse de", "boas-vindas", "agradecimento a", "voto de aplauso",
    "efemeride", "comemora",
]

# Quanto da transcricao guardar. O texto inteiro seria um discurso de 20 minutos
# na tela; o comeco e onde o orador enuncia o assunto. Quem revisa abre o link.
TRECHO = 700


def cerimonial(*textos: str) -> bool:
    a = sem_acento(" ".join(t or "" for t in textos))
    return any(p in a for p in CERIMONIAL)


def coletar_camara(id_dep: str, id_cand: str, desde: str) -> list[dict]:
    itens, pagina = [], 1
    while True:
        j = buscar("https://dadosabertos.camara.leg.br/api/v2/deputados/"
                   f"{id_dep}/discursos?dataInicio={desde}&dataFim={HOJE}"
                   f"&itens=100&pagina={pagina}&ordem=DESC&ordenarPor=dataHoraInicio")
        d = j.get("dados") or []
        itens.extend(d)
        if len(d) < 100:
            break
        pagina += 1

    saida = []
    for x in itens:
        sumario = (x.get("sumario") or "").strip()
        kw = (x.get("keywords") or "").strip()
        transc = (x.get("transcricao") or "").strip()
        if cerimonial(sumario, kw):
            continue
        if not (sumario or transc):
            continue
        # O tema sai da indexacao DA CASA quando ela existe. Ementa e prosa livre;
        # keyword da Camara e vocabulario controlado, e erra muito menos.
        temas, conf = sugerir_temas(kw or sumario)
        if kw and conf in ("fraca", "nenhuma"):
            t2, c2 = sugerir_temas(kw + " " + sumario)
            if c2 in ("boa", "ambigua"):
                temas, conf = t2, c2
        inicio = (x.get("dataHoraInicio") or "")
        quando = inicio[:10]
        # A HORA entra no id. Sem ela, tres falas do mesmo deputado no mesmo dia
        # e do mesmo tipo viram o mesmo id — e a tela de classificacao decidiria
        # uma achando que decidiu as tres. Eram 7 ids colidindo, 18 registros.
        hora = inicio[11:16].replace(":", "")
        saida.append({
            "id_registro": f"disc-cam-{id_dep}-{quando}-{hora}-{(x.get('tipoDiscurso') or '')[:3].lower()}",
            "casa": "camara",
            "id_candidatura": id_cand,
            "data": quando,
            "tipo_sessao": x.get("tipoDiscurso") or "",
            "sumario_oficial": sumario,
            "indexacao_oficial": kw,
            "trecho_transcricao": transc[:TRECHO],
            "transcricao_truncada": len(transc) > TRECHO,
            "url": x.get("urlTexto") or "",
            "temas": temas,
            "_confianca_tema": conf,
            "_ressalva": "Transcricao sem revisao do orador (Diario da Camara).",
            "id_documento": "doc-camara-api",
        })
    return saida


def coletar_senado(cod: str, id_cand: str, ini: str, fim: str) -> list[dict]:
    j = buscar("https://legis.senado.leg.br/dadosabertos/senador/"
               f"{cod}/discursos.json?dataInicio={ini}&dataFim={fim}")
    p = (((j.get("DiscursosParlamentar") or {}).get("Parlamentar") or {})
         .get("Pronunciamentos") or {}).get("Pronunciamento") or []
    if isinstance(p, dict):
        p = [p]
    saida = []
    for x in p:
        resumo = (x.get("TextoResumo") or "").strip()
        idx = (x.get("Indexacao") or "").strip()
        if cerimonial(resumo, idx):
            continue
        if not (resumo or idx):
            continue
        temas, conf = sugerir_temas(idx or resumo)
        cod_p = x.get("CodigoPronunciamento")
        saida.append({
            "id_registro": f"disc-sf-{cod_p}",
            "casa": "senado",
            "id_candidatura": id_cand,
            "data": x.get("DataPronunciamento") or "",
            "tipo_sessao": ((x.get("TipoUsoPalavra") or {}) or {}).get("Descricao") or "",
            "sumario_oficial": resumo,
            "indexacao_oficial": idx,
            "trecho_transcricao": "",
            "transcricao_truncada": False,
            "url": x.get("UrlTexto") or "",
            "url_texto_integral": x.get("UrlTextoBinario") or "",
            "temas": temas,
            "_confianca_tema": conf,
            "_ressalva": "Resumo e indexacao sao da taquigrafia do Senado; o texto integral esta no link.",
            "id_documento": "doc-senado-api",
        })
    return saida


def main() -> int:
    so_resumo = "--resumo" in sys.argv
    cands = json.loads((DADOS / "candidaturas.json").read_text(encoding="utf-8"))["candidaturas"]

    tudo: list[dict] = []
    for c in cands:
        pl = (c.get("situacao_parlamentar") or [None])[0]
        if not (pl and pl.get("casa") == "camara"):
            continue
        # A legislatura atual comecou em 01/02/2023. Discurso de mandato anterior
        # e outro contexto e nao entra sem dizer de onde vem.
        r = coletar_camara(str(pl["id_externo"]), c["id_candidatura"], "2023-02-01")
        print(f">> {c['id_candidatura']}: {len(r)} pronunciamentos nao cerimoniais", flush=True)
        tudo.extend(r)

    r = coletar_senado("5527", "sen-sp-2026-tebet", "20150201", "20221231")
    print(f">> sen-sp-2026-tebet: {len(r)} pronunciamentos nao cerimoniais (mandato 2015-2022)", flush=True)
    tudo.extend(r)

    conf: dict[str, int] = {}
    for x in tudo:
        conf[x["_confianca_tema"]] = conf.get(x["_confianca_tema"], 0) + 1
    print("\n" + "=" * 60)
    print(f"pronunciamentos coletados: {len(tudo)}")
    print("tema sugerido, por confianca:")
    for k in ("boa", "fraca", "ambigua", "nenhuma"):
        if conf.get(k):
            print(f"   {k:9} {conf[k]:4}")
    print("\nNada entra no site sem revisao: discurso prova que a pessoa DISSE,")
    print("nunca que o que ela disse e verdade.")

    if so_resumo:
        print("\n(--resumo: nada foi escrito)")
        return 0
    SAIDA.write_text(json.dumps({
        "_nota": ("Pronunciamentos em plenario, AGUARDANDO REVISAO. Selo 🟣 declaracao "
                  "do candidato dentro de 🔵 registro oficial. Nao e lido pelo gerar_site.py."),
        "_coletado_em": HOJE,
        "registros": sorted(tudo, key=lambda x: (x["id_candidatura"], x["data"]), reverse=True),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nescrito: {SAIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
