# -*- coding: utf-8 -*-
"""Leva o registro legislativo COLETADO para o arquivo que o site publica.

A PONTE QUE FALTAVA. coletar_legislativo.py grava em _coleta_legislativa.json e
diz, no proprio cabecalho, que NAO escreve no arquivo publicavel — a decisao e da
revisao humana. Mas nenhum script fazia o caminho de volta. Resultado: 878
registros de Pernambuco classificados e invisiveis, e uma fila de revisao sobre
material que nao tinha como chegar a tela.

Este script e essa volta, com quatro porteiros.

1. A AMOSTRA DE AUDITORIA MANDA. Nao exijo confirmacao humana item a item: o tema
   de uma ementa literal e arquivamento, nao afirmacao sobre candidatura. Mas
   arquivar 878 itens pela minha leitura so vale se a minha leitura prestar — e
   isso e medido, nao afirmado. A tela de classificacao ja grava 'concordou'
   quando a revisao bate com o que propus. Sem amostra revisada, ou com
   concordancia abaixo do minimo, este script para.

2. EMENTA QUE NAO DIZ DO QUE TRATA NAO PUBLICA. "Altera a Lei no 10.696, de 2 de
   julho de 2003" nao informa nada a quem le. Ou a ementa se explica, ou alguem
   escreve _contexto. Regra da curadoria: voto e defesa de lei precisam vir
   explicados.

3. PERIODO VAI JUNTO DA CONTAGEM, sempre. Mendonca Filho tem registro desde 1995
   e Tulio Gadelha desde 2018. "160" e "208" lado a lado, sem periodo, fazem
   antiguidade parecer produtividade.

4. QUEM NAO TEM REGISTRO GANHA O MOTIVO ESCRITO. Em Pernambuco, 4 das 12
   candidaturas tem mandato federal e 8 nao. Publicar sem dizer isso faria quatro
   pessoas parecerem substanciais e oito parecerem vazias — e a diferenca mede
   mandato, nao candidatura. Ausencia aqui e do TIPO "nao teve mandato federal",
   e nao "nao localizamos".

USO
    python promover_legislativo.py --uf PE
    python promover_legislativo.py --uf PE --gravar
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from datetime import date

import acervo

COLETAS = ("_coleta_legislativa.json", "_coleta_discursos.json")

# Minimos para confiar na classificacao automatica de um estado.
AMOSTRA_MINIMA = 20          # itens revisados por gente
CONCORDANCIA_MINIMA = 0.80   # dos revisados que nao eram editoriais

# Preambulo "Altera a Lei X" — o que importa e o que vem DEPOIS dele.
PREAMBULO = re.compile(
    r"^\s*(altera|modifica|acrescenta|revoga|susta|d[aá] nova reda[cç][aã]o a?o?|inclui)\s+"
    r"(o|a|os|as)?\s*[^,]{0,90}?(lei|decreto-lei|decreto|c[oó]digo|constitui[cç][aã]o|"
    r"estatuto|medida provis[oó]ria)[^,]{0,60}?[,\s]*"
    r"(para|a fim de|com o objetivo de|que)?\s*", re.I)


def explica(ementa: str) -> bool:
    """A ementa diz o que a proposicao FAZ, ou so cita a norma que altera?

    O corte de tamanho vale SO quando havia preambulo para tirar. "Cria o
    Programa Renda Basica Brasileira" e curta e clara; "Altera a Lei no 10.696,
    de 2 de julho de 2003" e do mesmo tamanho e nao diz nada. A diferenca nao e
    o comprimento, e se sobra objeto depois de nomear a norma."""
    texto = (ementa or "").strip()
    resto = PREAMBULO.sub("", texto).strip(" .;")
    if resto == texto.strip(" .;"):
        return len(resto) >= 30          # nao havia preambulo: fala por si
    return len(resto) >= 40              # sobrou algo depois de "Altera a Lei X"?


def confianca(registros: list[dict]) -> tuple[int, int, float, list[str]]:
    """Quantos foram revisados, quantos mediam concordancia, e a taxa."""
    revisados = [r for r in registros
                 if (r.get("_classificacao") or {}).get("por") == "humano"]
    mediveis = [r for r in revisados if "concordou" in (r.get("_classificacao") or {})]
    acertos = sum(1 for r in mediveis if r["_classificacao"]["concordou"])
    taxa = acertos / len(mediveis) if mediveis else 0.0
    discordou = [r["id_registro"] for r in mediveis if not r["_classificacao"]["concordou"]]
    return len(revisados), len(mediveis), taxa, discordou


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", required=True)
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()
    uf = a.uf.upper()
    base = acervo.exige(uf)

    coletados: list[dict] = []
    for nome in COLETAS:
        f = base / nome
        if f.exists():
            coletados += json.loads(f.read_text(encoding="utf-8"))["registros"]
    if not coletados:
        raise SystemExit(f"nao ha coleta legislativa em {uf}. Rode coletar_legislativo.py --uf {uf}")

    cands = {c["id_candidatura"]: c for c in acervo.ler("candidaturas.json", uf)["candidaturas"]}

    # --- PORTEIRO 1: a amostra de auditoria manda -------------------------
    n_rev, n_med, taxa, discordou = confianca(coletados)
    print(f"{uf}: {len(coletados)} registros coletados")
    print(f"  revisados por gente: {n_rev} · com concordancia medida: {n_med} · "
          f"taxa: {taxa:.0%}")
    if n_rev < AMOSTRA_MINIMA or (n_med and taxa < CONCORDANCIA_MINIMA):
        print()
        print(f"PAROU: a classificacao automatica ainda nao foi medida o bastante em {uf}.")
        print(f"  minimo: {AMOSTRA_MINIMA} itens revisados e {CONCORDANCIA_MINIMA:.0%} de concordancia")
        print(f"  agora:  {n_rev} revisados, {taxa:.0%} de concordancia")
        print()
        print(f"  Rode: python classificar.py --uf {uf}")
        print("  Arquivar 878 itens pela minha leitura so vale se a minha leitura prestar,")
        print("  e isso se mede na amostra — nao se afirma.")
        if discordou:
            print(f"  (discordancias ate agora: {len(discordou)})")
        return 1

    # --- PORTEIRO 2: ementa tem de explicar do que trata ------------------
    opacos, prontos = [], []
    for r in coletados:
        cl = r.get("_classificacao") or {}
        if not cl.get("temas"):
            continue                       # sem tema nao entra; nao e erro, e fila
        if explica(r.get("ementa", "")) or (r.get("_contexto") or "").strip():
            prontos.append(r)
        else:
            opacos.append(r)

    print(f"  com tema atribuido: {len(prontos) + len(opacos)}")
    print(f"  ementa que explica (ou com _contexto escrito): {len(prontos)}")
    if opacos:
        print(f"  SEM EXPLICAR, ficam de fora: {len(opacos)}")
        for r in opacos[:6]:
            print(f"      {r['tipo']} {r['numero']}/{r['ano']}: {r.get('ementa','')[:88]}")
        print("      (escreva _contexto nesses itens para que possam entrar)")

    # --- PORTEIRO 3: periodo junto da contagem ----------------------------
    por_cand: dict[str, list[int]] = collections.defaultdict(list)
    for r in prontos:
        for aut in (r.get("autoria") or []):
            if aut["id_candidatura"] in cands:
                por_cand[aut["id_candidatura"]].append(int(r["ano"]))

    totais = {}
    for cid, anos in por_cand.items():
        totais[cid] = {
            "registros": len(anos),
            "periodo_inicio": min(anos),
            "periodo_fim": max(anos),
            # A frase que o site EXIBE junto do numero. Contagem sem periodo faz
            # antiguidade parecer produtividade.
            "_como_exibir": (f"{len(anos)} proposições entre {min(anos)} e {max(anos)}"),
            "_regra": ("Nunca exibir esta contagem comparando candidaturas: casas, "
                       "periodos e regras de iniciativa sao diferentes."),
        }

    # --- PORTEIRO 4: ausencia com o motivo certo --------------------------
    ausencias = []
    for cid, c in cands.items():
        if cid in por_cand:
            continue
        tem_mandato = bool(c.get("situacao_parlamentar"))
        ausencias.append({
            "id_candidatura": cid,
            "motivo": ("nao_localizamos" if tem_mandato else "sem_mandato_federal"),
            "_texto": (
                "Esta candidatura exerce mandato federal, e ainda não localizamos "
                "proposições dela nas bases da Câmara e do Senado."
                if tem_mandato else
                "Esta candidatura não exerce mandato federal, então não há proposições "
                "a mostrar aqui. Ausência de registro legislativo NÃO é ausência de "
                "propostas — é consequência de nunca ter ocupado essa cadeira."),
        })

    print(f"  candidaturas com registro: {len(por_cand)} de {len(cands)}")
    print(f"  sem registro, com motivo escrito: {len(ausencias)}")
    for x in ausencias[:3]:
        print(f"      {x['id_candidatura'].split('-', 3)[-1]}: {x['motivo']}")

    if not a.gravar:
        print("\n(sem --gravar: nada foi escrito)")
        return 0

    destino = base / "registros_legislativos.json"
    atual = json.loads(destino.read_text(encoding="utf-8"))

    # O que ja estava no arquivo carrega conferencia humana (url_conferida_em,
    # _nota, temas escolhidos a mao). Merge preserva; este script so acrescenta.
    existentes = {r["id_registro"]: r for r in atual.get("registros", [])}
    novos = 0
    for r in prontos:
        if r["id_registro"] in existentes:
            continue
        item = {k: v for k, v in r.items() if not k.startswith("_classificacao")}
        item["temas"] = r["_classificacao"]["temas"]
        item["_tema_por"] = r["_classificacao"].get("por", "modelo")
        item["_promovido_em"] = date.today().isoformat()
        existentes[r["id_registro"]] = item
        novos += 1

    atual["registros"] = list(existentes.values())
    atual["totais_por_candidatura"] = totais
    atual["ausencias"] = ausencias
    atual["_confianca_da_classificacao"] = {
        "revisados_por_humano": n_rev,
        "com_concordancia_medida": n_med,
        "taxa_de_concordancia": round(taxa, 3),
        "medido_em": date.today().isoformat(),
        "_nota": ("Taxa de acerto da classificacao automatica, medida na amostra "
                  "sorteada. Nao e estimativa: cada item revisado gravou se a "
                  "revisao bateu com o que o modelo propos."),
    }
    destino.write_text(json.dumps(atual, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\ngravado: {destino}")
    print(f"  {novos} registro(s) novo(s) · {len(existentes)} no total")
    print(f"\nagora rode: python gerar_site.py --uf {uf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
