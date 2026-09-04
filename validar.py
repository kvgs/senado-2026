#!/usr/bin/env python3
"""
Validador do modelo de dados — Comparador de Candidaturas 2026.

Transforma em código as regras que estavam só em prosa nos documentos do
projeto. A intenção é que uma regra violada apareça aqui, e não numa tela
publicada.

Uso:  python validar.py
Saída: relatório no stdout; exit code 1 se houver ERRO.
"""

import json
import sys
from pathlib import Path

import argparse as _argparse

import acervo

# --uf para validar o acervo de um estado sem editar referencia.json. Validar o
# estado errado nao da erro: da "tudo certo" sobre outra coisa.
_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--uf", default=None)
_UF = (_ap.parse_known_args()[0].uf or acervo.uf_padrao()).upper()

DADOS = acervo.exige(_UF)
NACIONAL = acervo.NACIONAL

NIVEIS_FONTE = {
    "oficial", "verificada", "secundaria",
    "declaracao_candidato", "registro_legislativo",
}
ESTADOS = {"A", "B", "C", "D"}
# "ausencia" ENTRA AQUI porque o acervo a usa e o modelo a previu: estado C e D
# sao registros de ausencia, e ausencia nao e promessa nem resultado entregue.
# O validador nao sabia disso e reprovava os 40 registros de ausencia do acervo —
# 96 erros no Acre, 24 no Amapa — sem ninguem ver, porque ele roda em um estado
# por vez e o padrao e Sao Paulo. Regra que reprova a pratica correta e regra que
# se aprende a ignorar.
NATUREZAS = {"promessa", "resultado_entregue", "ausencia"}
# SO O D. C e D sao os dois estados de ausencia, mas de tipos opostos, e a
# primeira versao desta regra tratou os dois como iguais — reprovando 58 linhas
# de Sao Paulo que estavam certas.
#
#   C  "li este documento e ele NAO trata do tema". TEM fonte: o documento lido,
#      com nivel_fonte e data_referencia. A ausencia foi constatada DENTRO de uma
#      fonte, e apontar qual e o que a sustenta.
#   D  "nao localizei fonte nenhuma". NAO tem fonte, por definicao, e o que a
#      sustenta e dizer quando se procurou e onde.
ESTADOS_SEM_FONTE = {"D"}

erros: list[str] = []
avisos: list[str] = []


def carregar(nome):
    caminho = (NACIONAL if nome in acervo.DE_TODOS else DADOS) / nome
    if not caminho.exists():
        erros.append(f"[arquivo] {nome} não encontrado em {DADOS}")
        return None
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        erros.append(f"[json] {nome} inválido: {e}")
        return None


CONHECIMENTO = Path(__file__).parent / "conhecimento" / "regras.json"


def carregar_conhecimento():
    """Ausente e ERRO, nao aviso: sem a base, o validador deixa de cobrar as
    regras que custaram 51 posicoes para serem aprendidas, e ninguem percebe."""
    if not CONHECIMENTO.exists():
        erros.append("[kb] conhecimento/regras.json nao encontrado — as regras de fonte "
                     "nao podem ser cobradas sem ele")
        return None
    try:
        return json.loads(CONHECIMENTO.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        erros.append(f"[kb] conhecimento/regras.json invalido: {e}")
        return None


def cobrar_regras_de_fonte(kb, posicoes, documentos):
    if not kb:
        return
    tipos = kb["tipos_de_fonte"]
    docs_por_id = {d["id_documento"]: d for d in documentos}

    for pos in posicoes:
        pid = pos["id_posicao"]
        # Posicao ja reprovada na revisao esta fora da publicacao e fica no acervo
        # como memoria do erro. O validador bloqueia o que E PUBLICAVEL; relembrar
        # erro ja registrado transformaria o validador em ruido permanente.
        if (pos.get("revisao") or {}).get("resultado") in ("remover", "corrigir"):
            continue
        doc = docs_por_id.get(pos.get("id_documento"))
        if not doc:
            continue
        tipo = doc.get("tipo")
        estado = pos.get("estado_cobertura")

        # R-ESCOPO-01 — documento de outro estado nao sustenta nada.
        if doc.get("aplicavel_a_sp") is False:
            erros.append(f"[R-ESCOPO-01] {pid}: usa '{doc['id_documento']}', marcado como "
                         "nao aplicavel a SP")

        regra = tipos.get(tipo)
        if not regra:
            avisos.append(f"[kb] {pid}: tipo de fonte '{tipo}' nao esta na base de "
                          "conhecimento — sem regra, nada pode ser cobrado dele")
            continue

        # R-FONTE-01 e R-FONTE-02 — o que cada tipo de fonte pode sustentar.
        permitidos = regra.get("estados_permitidos")
        if permitidos is not None and estado in ("A", "B") and estado not in permitidos:
            id_regra = "R-FONTE-01" if not permitidos else "R-FONTE-02"
            erros.append(f"[{id_regra}] {pid}: estado {estado} com fonte de tipo "
                         f"'{tipo}' ({regra['nome']}) — {regra['porque'][:110]}")

        # R-ESCOPO-03 — programa de uma candidatura nao fala pelas outras.
        if doc.get("assinatura") == "candidatura":
            dono = doc.get("assinado_por", "outra candidatura")
            erros.append(
                f"[R-ESCOPO-03] {pid}: usa documento assinado por {dono}. Programa de uma "
                "candidatura fala por ela e por mais ninguem — sob outro candidato, poe na "
                "boca dele o que outra pessoa disse."
            )

        # R-ESCOPO-02 — documento de outro cargo exige escopo dito ao leitor.
        if doc.get("cargo_registrado") and doc["cargo_registrado"] != "senador":
            if not (pos.get("escopo") or "").strip():
                erros.append(
                    f"[R-ESCOPO-02] {pid}: usa documento registrado para o cargo de "
                    f"{doc['cargo_registrado']} sem escopo declarado. Quem clica encontra "
                    "o plano de outra candidatura e nao tem como saber por que ele aparece aqui."
                )

        # R-FONTE-05 — autoria legislativa em prosa, com link generico, nao se sustenta.
        if pos.get("nivel_fonte") == "registro_legislativo":
            url = (doc.get("url") or "").rstrip("/")
            if url.endswith(("/api/v2", "/dadosabertos", "/repositorioDados")):
                erros.append(
                    f"[R-FONTE-05] {pid}: registro legislativo apontando para endereco "
                    f"generico ({url}). Autoria de proposicao vive em "
                    "registros_legislativos, uma ficha por proposicao — texto que "
                    "empacota varias nao tem um link possivel."
                )

        # R-REDACAO-01 — parafrase de fonte oficial sem ancora precisa de olho humano.
        if (pos.get("nivel_fonte") == "oficial"
                and not (pos.get("citacao_literal") or "").strip()
                and not pos.get("revisado_por_humano")):
            avisos.append(f"[curadoria] {pid}: fonte oficial sem citacao literal — "
                          "parafrase sem ancora, conferir palavra a palavra")


def main():
    ref = carregar("referencia.json")
    cands = carregar("candidaturas.json")
    docs = carregar("documentos.json")
    posic = carregar("posicoes.json")
    regs = carregar("registros_legislativos.json")
    pesq = carregar("pesquisas.json")

    if erros:
        relatar()
        return

    ids_tema = {t["id_tema"] for t in ref["temas"]}
    ids_partido = {p["id_partido"] for p in ref["partidos"]}
    ids_colig = {c["id_coligacao"] for c in ref["coligacoes"]}
    ids_cand = {c["id_candidatura"] for c in cands["candidaturas"]}
    ids_doc = {d["id_documento"] for d in docs["documentos"]}

    # ---------- candidaturas ----------
    for c in cands["candidaturas"]:
        cid = c["id_candidatura"]
        if c["id_partido"] not in ids_partido:
            erros.append(f"[fk] {cid}: id_partido '{c['id_partido']}' inexistente")
        if c.get("id_coligacao") and c["id_coligacao"] not in ids_colig:
            erros.append(f"[fk] {cid}: id_coligacao '{c['id_coligacao']}' inexistente")
        if not c.get("sequencial_tse"):
            avisos.append(f"[chave] {cid}: sem sequencial_tse — chave natural do registro oficial")

        # R7/R10: situação de registro é histórico datado
        for s in c.get("situacao_registro", []):
            if not s.get("observado_em"):
                erros.append(f"[R10] {cid}: situacao_registro sem observado_em")

        # R11: CPF nunca em Silver
        if "cpf" in json.dumps(c).lower():
            erros.append(f"[R11] {cid}: aparece 'cpf' — CPF não sai da camada Bronze")

    # ---------- posições ----------
    vistos = set()
    for p in posic["posicoes"]:
        pid = p.get("id_posicao", "<sem id>")
        if pid in vistos:
            erros.append(f"[pk] id_posicao duplicado: {pid}")
        vistos.add(pid)

        if p["id_tema"] not in ids_tema:
            erros.append(f"[fk] {pid}: id_tema '{p['id_tema']}' inexistente")
        sem_fonte = p.get("estado_cobertura") in ESTADOS_SEM_FONTE
        # REGISTRO DE AUSENCIA NAO TEM FONTE, e exigir nivel_fonte dele seria
        # exigir que se nomeie a origem de uma coisa que nao foi encontrada.
        if sem_fonte:
            # AVISO, E NAO ERRO. A pratica do acervo e nivel_fonte nulo no estado
            # D, e sao 40 registros assim. Mas ha um, o p054 de Sao Paulo, que
            # nomeia a base de candidaturas como fonte da busca — e ele foi
            # conferido e aprovado pela curadoria. Transformar isso em erro
            # bloquearia a publicacao por causa de uma decisao humana ja tomada.
            # O validador aponta a divergencia; quem decide continua sendo gente.
            if p.get("nivel_fonte") is not None:
                avisos.append(f"[R3] {pid}: estado D com nivel_fonte "
                              f"'{p.get('nivel_fonte')}'. No resto do acervo o "
                              "estado D vai com nivel_fonte nulo, porque ausencia "
                              "de fonte nao tem fonte. Se aqui a intencao e "
                              "apontar ONDE se procurou, isso ja vive em "
                              "escopo_da_busca.")
        elif p.get("nivel_fonte") not in NIVEIS_FONTE:
            erros.append(f"[R3] {pid}: nivel_fonte '{p.get('nivel_fonte')}' inválido")
        if p.get("estado_cobertura") not in ESTADOS:
            erros.append(f"[R2] {pid}: estado_cobertura '{p.get('estado_cobertura')}' inválido")
        if p.get("natureza") and p["natureza"] not in NATUREZAS:
            erros.append(f"[R5] {pid}: natureza '{p['natureza']}' inválida")
        # A DATA DA AUSENCIA E A DA BUSCA. data_referencia responde "de quando e
        # esta declaracao"; num registro de ausencia nao ha declaracao, e a
        # pergunta certa e "quando foi que procuramos" — busca_realizada_em.
        if sem_fonte:
            if not p.get("busca_realizada_em"):
                erros.append(f"[R10] {pid}: registro de ausencia sem "
                             "busca_realizada_em — sem a data, 'nao localizamos' "
                             "nao diz de quando")
            if not p.get("escopo_da_busca"):
                erros.append(f"[R10] {pid}: registro de ausencia sem "
                             "escopo_da_busca — afirmar que nao achamos exige "
                             "dizer onde procuramos")
        elif not p.get("data_referencia"):
            erros.append(f"[R10] {pid}: sem data_referencia")
        if p.get("id_documento") and p["id_documento"] not in ids_doc:
            erros.append(f"[fk] {pid}: id_documento '{p['id_documento']}' inexistente")

        tipo = p.get("atribuido_a_tipo")
        alvo = p.get("atribuido_a_id")

        # R1: proposta pertence a candidatura OU a partido
        if tipo == "candidatura":
            if alvo not in ids_cand:
                erros.append(f"[R1] {pid}: atribuido_a_id '{alvo}' não é candidatura conhecida")
        elif tipo == "partido":
            if alvo not in ids_partido:
                erros.append(f"[R1] {pid}: atribuido_a_id '{alvo}' não é partido conhecido")
            if not p.get("id_candidatura_contexto"):
                erros.append(f"[R1] {pid}: proposta de partido exige id_candidatura_contexto")
            elif p["id_candidatura_contexto"] not in ids_cand:
                erros.append(f"[fk] {pid}: id_candidatura_contexto inexistente")
        else:
            erros.append(f"[R1] {pid}: atribuido_a_tipo '{tipo}' inválido")

        # Estado B tem que ser atribuído a partido, e vice-versa
        if p.get("estado_cobertura") == "B" and tipo != "partido":
            erros.append(f"[R1] {pid}: estado B exige atribuido_a_tipo='partido'")
        if tipo == "partido" and p.get("estado_cobertura") != "B":
            avisos.append(f"[R1] {pid}: atribuído a partido mas estado != B — conferir")

        # ---- A REGRA QUE MAIS IMPORTA ----
        # R2: estado D é afirmação sobre a NOSSA busca, não sobre o candidato.
        # Sem data e escopo registrados, vira acusação de silêncio insustentável.
        if p.get("estado_cobertura") == "D":
            if not p.get("busca_realizada_em"):
                erros.append(f"[R2/D] {pid}: estado D sem busca_realizada_em")
            if not p.get("escopo_da_busca"):
                erros.append(f"[R2/D] {pid}: estado D sem escopo_da_busca")

        # Curadoria incremental: nada publicável sem revisão humana
        if not p.get("revisado_por_humano"):
            avisos.append(f"[curadoria] {pid}: ainda não revisado por humano — não publicar")

    # ---------- registros legislativos ----------
    for r in regs["registros"]:
        rid = r["id_registro"]
        for t in r.get("temas", []):
            if t not in ids_tema:
                erros.append(f"[fk] {rid}: tema '{t}' inexistente")
        if not r.get("autoria"):
            erros.append(f"[R9] {rid}: sem autoria")
        for a in r.get("autoria", []):
            if a["id_candidatura"] not in ids_cand:
                erros.append(f"[fk] {rid}: autoria aponta candidatura inexistente")
            # Assinatura de apoio não é iniciativa. PEC no Senado exige 27
            # assinaturas: sem ordem e total, "autor" mistura as duas coisas.
            tot = a.get("total_autores")
            if tot is not None and tot > 1 and a.get("ordem_autoria") is None:
                erros.append(
                    f"[autoria] {rid}: total_autores={tot} sem ordem_autoria. "
                    "Não dá para distinguir iniciativa de assinatura de apoio."
                )
            if r.get("casa") == "senado" and r.get("tipo") == "PEC" and tot is None:
                avisos.append(
                    f"[autoria] {rid}: PEC do Senado sem total_autores — PEC lá exige "
                    "27 assinaturas, então 'autor' sem contexto infla o registro."
                )

    # ---------- votações nominais ----------
    # Um voto sem a pergunta votada e sem a proposição é ruído: não dá para
    # traduzir em posição. Aqui isso é erro, não estilo.
    for v in regs.get("votacoes_nominais", []):
        vid = v.get("id_votacao", "<sem id>")
        if not v.get("pergunta"):
            erros.append(f"[voto] {vid}: sem 'pergunta' — voto sem a pergunta votada não é interpretável")
        obj = v.get("proposicao_objeto") or {}
        if not obj.get("rotulo") or not obj.get("ementa"):
            erros.append(f"[voto] {vid}: sem proposicao_objeto completa (rotulo + ementa)")
        if not v.get("data"):
            erros.append(f"[R10] {vid}: votação sem data")
        for t in v.get("temas", []):
            if t not in ids_tema:
                erros.append(f"[fk] {vid}: tema '{t}' inexistente")
        registros_voto = list(v.get("votos", []))
        registros_voto += (v.get("voto_adicional") or {}).get("votos", [])
        if not registros_voto:
            erros.append(f"[voto] {vid}: nenhum voto registrado")
        for r in registros_voto:
            if r.get("id_candidatura") not in ids_cand:
                erros.append(f"[fk] {vid}: voto aponta candidatura inexistente '{r.get('id_candidatura')}'")
            if not r.get("voto"):
                erros.append(f"[voto] {vid}: registro sem valor de voto")

    # A limitação de cobertura tem que estar declarada junto do dado.
    if regs.get("votacoes_nominais") and not regs.get("_limitacao_votos"):
        erros.append(
            "[voto] há votações nominais mas falta _limitacao_votos. A base de "
            "votações tem lacuna temporal e a maioria das votações é simbólica — "
            "publicar sem declarar isso induz a ler ausência de voto como ausência de atuação."
        )

    # R9 + contexto obrigatório: quem tem contagem precisa de situacao_parlamentar
    sit_parl = {
        c["id_candidatura"]
        for c in cands["candidaturas"]
        if c.get("situacao_parlamentar")
    }
    for t in regs.get("totais_por_candidatura", []):
        if t.get("substantivas_pl_pec_plp_pdl") is not None:
            if t["id_candidatura"] not in sit_parl:
                erros.append(
                    f"[contexto] {t['id_candidatura']}: tem contagem de proposições "
                    "sem situacao_parlamentar. Contagem sem contexto de licença é "
                    "correta no número e enganosa no sentido."
                )

    # ---------- regras da base de conhecimento ----------
    cobrar_regras_de_fonte(
        carregar_conhecimento(),
        posic["posicoes"],
        docs["documentos"],
    )

    # ---------- pesquisas ----------
    for q in pesq["pesquisas"]:
        if not q.get("registro_tse"):
            erros.append(f"[R8] pesquisa {q.get('id_pesquisa')}: sem registro_tse")
        for campo in ("campo_inicio", "campo_fim", "entrevistados", "margem_erro_pp"):
            if q.get(campo) in (None, ""):
                erros.append(f"[R8] pesquisa {q.get('id_pesquisa')}: sem {campo}")
        for r in q.get("resultados", []):
            if r["id_candidatura"] not in ids_cand:
                erros.append(f"[fk] pesquisa: resultado aponta candidatura inexistente")
            # R8: ausência do questionário não é zero
            if r.get("constava_no_questionario") is False and r.get("percentual") is not None:
                erros.append(
                    f"[R8] {r['id_candidatura']}: constava_no_questionario=false "
                    "mas tem percentual. Ausência do questionário não é 0%."
                )

    # ---------- regra de neutralidade ----------
    # Proibido agregado que permita montar contador de completude por candidatura.
    contagem = {}
    for p in posic["posicoes"]:
        alvo = p.get("id_candidatura_contexto") or p.get("atribuido_a_id")
        if alvo in ids_cand and p.get("estado_cobertura") in ("A", "B"):
            contagem[alvo] = contagem.get(alvo, 0) + 1
    if contagem:
        avisos.append(
            "[neutralidade] O validador consegue derivar contagem de propostas por "
            "candidatura. Isso é esperado em Silver — mas a camada Gold NÃO deve "
            "expor esse agregado: seria ranking implícito, e mediria verba de "
            "campanha e cobertura de imprensa, não qualidade de candidatura."
        )

    relatar(len(posic["posicoes"]), len(cands["candidaturas"]), len(regs["registros"]))


def relatar(n_pos=0, n_cand=0, n_reg=0):
    print("=" * 68)
    print("VALIDAÇÃO DO MODELO DE DADOS — Comparador de Candidaturas 2026")
    print("=" * 68)
    if n_cand:
        print(f"candidaturas: {n_cand} · posições: {n_pos} · registros legislativos: {n_reg}")
        print("-" * 68)

    if erros:
        print(f"\n❌ {len(erros)} ERRO(S) — bloqueiam publicação:\n")
        for e in erros:
            print(f"   {e}")
    else:
        print("\n✅ Nenhum erro de integridade.")

    if avisos:
        curadoria = [a for a in avisos if a.startswith("[curadoria]")]
        outros = [a for a in avisos if not a.startswith("[curadoria]")]
        if outros:
            print(f"\n⚠️  {len(outros)} aviso(s):\n")
            for a in outros:
                print(f"   {a}")
        if curadoria:
            # O ESTADO ENTRA NA FRASE, e nao e detalhe. Este validador roda em UM
            # estado (--uf, ou o padrao de referencia.json), e a frase sem a
            # sigla foi lida como se fosse o acervo inteiro: "122 aguardando
            # revisao" era so Sao Paulo, quando o acervo tinha 1.216. Numero sem
            # escopo engana quem confia nele — inclusive quem o escreveu.
            print(f"\n📋 {len(curadoria)} posição(ões) de {_UF} aguardando "
                  "revisão humana (curadoria incremental — nada disso é "
                  "publicável ainda).")
            print("   Este validador olha um estado por vez. Para o acervo "
                  "inteiro, rode com --uf de cada um.")

    print()
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
