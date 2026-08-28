import urllib.parse
# -*- coding: utf-8 -*-
"""Gera o site de comparacao a partir de dados/*.json.

A pagina e GERADA, nunca escrita a mao: assim nao pode divergir do modelo.
Regras respeitadas (secao 4 do contexto):
  - toda posicao exibida carrega fonte com link, selo e data
  - proposta de partido aparece rotulada como do partido, nunca do candidato
  - os 4 estados de cobertura sao distinguidos; C nunca vira D
  - NAO existe contador de completude por candidato nem ordenacao por volume
  - pesquisa NAO aparece por candidato, so em secao propria com ficha tecnica
  - ordem dos candidatos: numero de urna
  - bio gerada mecanicamente do registro, sem adjetivo
"""
import hashlib, json, pathlib

import argparse as _argparse

import acervo

# --uf escolhe o estado a gerar. Sem isso, gerar Pernambuco exigiria editar
# referencia.json, e esquecer de voltar geraria SP com o rotulo de PE.
_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--uf", default=None)
_UF = (_ap.parse_known_args()[0].uf or acervo.uf_padrao()).upper()

BASE = pathlib.Path(__file__).parent
DADOS_UF = acervo.exige(_UF)
HERE = BASE
# A pagina do estado mora em <uf>/index.html. A raiz e a escolha do estado,
# gerada por gerar_inicio.py. OUT e resolvido depois de ler qual UF e esta.
OUT = None   # definido abaixo, quando site.uf for conhecido

# Nome do estado para o texto corrido das bios. acervo.por_extenso ja traz a
# preposicao certa ("por Sao Paulo", "pelo Acre", "pela Bahia") — montar isso
# com um "por " fixo daria "por o Acre".
UF_POR_EXTENSO = acervo.por_extenso(_UF)
UF_NOME_EXTENSO = acervo.estado(_UF)["nome"]

ref = json.loads((BASE/"dados"/"referencia.json").read_text(encoding="utf-8"))
cands = json.loads((DADOS_UF/"candidaturas.json").read_text(encoding="utf-8"))["candidaturas"]
pos = json.loads((DADOS_UF/"posicoes.json").read_text(encoding="utf-8"))["posicoes"]
docs = {d["id_documento"]: d for d in json.loads((DADOS_UF/"documentos.json").read_text(encoding="utf-8"))["documentos"]}
pesq = json.loads((DADOS_UF/"pesquisas.json").read_text(encoding="utf-8"))
regs = json.loads((DADOS_UF/"registros_legislativos.json").read_text(encoding="utf-8"))

partidos = {p["id_partido"]: p for p in ref["partidos"]}
coligs = {c["id_coligacao"]: c for c in ref["coligacoes"]}
temas = ref["temas"]
selos = {s["id"]: s for s in ref["niveis_fonte"]}

CARGO_NOME = {
    "deputado_federal": "deputado federal", "deputado_estadual": "deputado estadual",
    "senador": "senador", "vereador": "vereador", "prefeito": "prefeito",
    "vice_governador": "vice-governador", "presidente": "presidente",
    "suplente_senador": "suplente de senador",
}

def bio(c):
    """Resumo biografico mecanico, so do registro. Sem adjetivo, sem juizo."""
    p = c["pessoa"]
    # O genero vem do registro do TSE. Era uma lista de nomes de mulheres de Sao
    # Paulo escrita a mao, entao toda deputada dos outros 26 estados virava
    # "deputado". A lista fica so como reserva para cadastro antigo sem o campo.
    fem = ((p.get("genero") or "").upper().startswith("FEMIN")
           or p["nome_urna"] in ("Simone Tebet", "Marina Silva", "Soninha Francine",
                                 "Dra Eliana Ferreira", "Maíra de Souza"))
    frases = []
    frases.append(f'Declarou ao TSE a ocupação de {p["ocupacao_declarada"].lower()}.')

    parl = (c.get("situacao_parlamentar") or [{}])[0]
    if parl.get("casa") == "camara":
        # "por Sao Paulo" estava escrito a mao: 31 bios dos outros estados
        # afirmavam que a pessoa era deputada por Sao Paulo. Afirmacao falsa
        # sobre gente real, gerada por um literal.
        t = (f'Exerce mandato de deputad{"a" if fem else "o"} federal '
             f'{UF_POR_EXTENSO}')
        if parl.get("desde"):
            t += f', em exercício desde {parl["desde"][8:10]}/{parl["desde"][5:7]}/{parl["desde"][:4]}'
        if parl.get("motivo_afastamento_anterior"):
            t += f' — antes disso, {parl["motivo_afastamento_anterior"][0].lower() + parl["motivo_afastamento_anterior"][1:]}'
        frases.append(t + '.')
    elif parl.get("casa") == "senado":
        # A casa "senado" nao era tratada: 32 senadores em exercicio nao tinham
        # linha de mandato. Os que pareciam ter so declararam "senador" como
        # OCUPACAO ao TSE, que e autodeclaracao — outro fato, e mais fraco.
        t = f'Exerce mandato de senador{"a" if fem else ""} {UF_POR_EXTENSO}'
        if parl.get("desde"):
            t += f', em exercício desde {parl["desde"][8:10]}/{parl["desde"][5:7]}/{parl["desde"][:4]}'
        frases.append(t + '.')
    elif parl.get("casa") == "alesp":
        t = (f'Exerce mandato de deputad{"a" if fem else "o"} estadual '
             f'em {UF_NOME_EXTENSO}')
        if parl.get("cargo_na_casa"): t += f' e ocupa o cargo de {parl["cargo_na_casa"]}'
        frases.append(t + '.')

    for ce in c.get("cargos_executivos_anteriores", [])[:1]:
        frases.append(f'Foi {ce["cargo"]} ({ce["ente"]}).')
    for cr in c.get("cargos_representacao", [])[:1]:
        frases.append(f'É {cr["cargo"]}.')

    ma = c.get("mandatos_anteriores", [])
    eleitos = [m for m in ma if m.get("resultado","").startswith("eleit")]
    if eleitos:
        cargos = []
        for m in eleitos:
            nome = CARGO_NOME.get(m["cargo"], m["cargo"])
            uf = m.get("uf") or m.get("municipio") or ""
            cargos.append(f'{nome}{" por " + uf if uf else ""} em {m["ano"]}')
        frases.append(f'Já foi eleit{"a" if fem else "o"} ' + "; ".join(cargos[:3]) + '.')
    elif ma:
        frases.append(f'Disputou {len(ma)} eleiç{"ões" if len(ma)>1 else "ão"} anterior'
                      f'{"es" if len(ma)>1 else ""} sem ser eleit{"a" if fem else "o"}.')
    else:
        frases.append(f'Primeira candidatura registrada nos dados abertos do TSE.')

    nota = c.get("_nota")
    if nota and "Primeira disputa" not in nota and "Primeira candidatura" not in nota:
        pass
    return " ".join(frases)

cand_por_id = {}
for c in cands:
    colig = coligs.get(c.get("id_coligacao") or "", {})
    iniciais = "".join(w[0] for w in c["pessoa"]["nome_urna"].split()[:2] if w[0].isalpha()).upper()
    cand_por_id[c["id_candidatura"]] = {
        "nome": c["pessoa"]["nome_urna"],
        "completo": c["pessoa"]["nome_completo"],
        "partido": partidos[c["id_partido"]]["sigla"],
        "partido_nome": partidos[c["id_partido"]]["nome"],
        "coligacao": colig.get("nome",""),
        "coligacao_comp": colig.get("composicao",""),
        "numero": c["numero_urna"],
        "iniciais": iniciais,
        "bio": bio(c),
        # A situacao do registro pode nao existir: a base de candidatos do TSE traz
        # "#NE" em alguns extratos. Ausencia vira None e o site DIZ que nao sabe,
        # em vez de a pagina quebrar ou, pior, mostrar campo vazio sem explicar.
        "situacao": (c["situacao_registro"] or [{}])[0].get("situacao"),
        "situacao_em": (c["situacao_registro"] or [{}])[0].get("observado_em"),
        "situacao_ausente": c.get("_situacao_ausente") if not c["situacao_registro"] else None,
        "sequencial": c.get("sequencial_tse"),
        "suplentes": c.get("suplentes", []),
        # Foto de registro de candidatura. O credito e do TSE; o caminho tecnico
        # de obtencao fica em candidaturas.json, nao no site.
        "foto": (c.get("foto") or {}).get("arquivo"),
        "foto_credito": (c.get("foto") or {}).get("credito"),
        # --- Fase 6: ficha completa para a pagina de perfil ---
        "nascimento": c["pessoa"].get("data_nascimento"),
        "escolaridade": c["pessoa"].get("escolaridade"),
        "bens": c.get("bens_declarados_brl"),
        "coligacao_comp": colig.get("composicao", ""),
        "parlamentar": (c.get("situacao_parlamentar") or [None])[0],
        "mandatos": c.get("mandatos_anteriores", []),
        "cargos_exec": c.get("cargos_executivos_anteriores", []),
        "cargos_repr": c.get("cargos_representacao", []),
        "areas_declaradas": c.get("areas_atuacao_declaradas", []),
        "base_eleitoral": c.get("base_eleitoral_declarada", []),
        "obs_registro": (c.get("_pendencias") or []) + (
            [c["_nota"]] if c.get("_nota") else []),
        "concorrentes": c.get("candidaturas_concorrentes_2026", []),
        "contato": c.get("contato") or {},
    }

# Situacao do programa do PARTIDO de cada candidatura. Serve para o site dizer
# a verdade certa quando nao ha proposta — sao tres casos diferentes, e a frase
# generica "o partido nao registrou programa" seria FALSA para a UP, que
# registrou um programa assinado pela candidatura da Samara Martins.
_docs_por_partido = {}
for _r in pos:
    _d = docs.get(_r.get("id_documento")) or {}
    if _d.get("tipo") in ("plano_tse", "programa_partidario"):
        _dono = _r.get("atribuido_a_id")
        if _dono in partidos:
            _docs_por_partido.setdefault(_dono, {})[_d["id_documento"]] = _d

for _cid, _c in cand_por_id.items():
    _pid = next((c["id_partido"] for c in cands if c["id_candidatura"] == _cid), None)
    _ds = list((_docs_por_partido.get(_pid) or {}).values())
    _de_outra = [d for d in _ds if d.get("assinatura") == "candidatura"]
    if not _ds:
        _c["programa_partido"] = {"tipo": "nenhum"}
    elif _de_outra and len(_de_outra) == len(_ds):
        _c["programa_partido"] = {
            "tipo": "de_outra_candidatura",
            "assinado_por": _de_outra[0].get("assinado_por", ""),
            "titulo": _de_outra[0].get("titulo", ""),
            "url": _de_outra[0].get("url", ""),
        }
    else:
        _c["programa_partido"] = {"tipo": "do_partido"}

ordem = sorted(cand_por_id, key=lambda k: int(cand_por_id[k]["numero"]))

# Posicao reprovada na revisao humana NAO vai para o site. Continua em
# posicoes.json, com a nota de quem reprovou: o arquivo guarda a memoria do erro,
# que e o que impede repeti-lo. O que sai daqui e a publicacao, nao o registro.
REPROVADAS = {"remover", "corrigir"}
pos_publicaveis = [r for r in pos
                   if (r.get("revisao") or {}).get("resultado") not in REPROVADAS]
pos_reprovadas = len(pos) - len(pos_publicaveis)

grade = {t["id_tema"]: {cid: [] for cid in ordem} for t in temas}
for r in pos_publicaveis:
    alvo = r.get("id_candidatura_contexto") or r.get("atribuido_a_id")
    if alvo not in grade[r["id_tema"]]: continue
    doc = docs.get(r.get("id_documento"), {})
    grade[r["id_tema"]][alvo].append({
        "estado": r["estado_cobertura"], "selo": r.get("nivel_fonte"),
        "texto": r.get("texto") or "", "citacao": r.get("citacao_literal") or "",
        "escopo": r.get("escopo") or "",
        "de_partido": r.get("atribuido_a_tipo") == "partido",
        "partido": partidos.get(r.get("atribuido_a_id"), {}).get("sigla",""),
        "fonte": doc.get("titulo","fonte não registrada"),
        # Link proprio da posicao vence o do documento: quando a fonte e uma API,
        # o endereco util e o da proposicao especifica, nao a raiz do servico.
        "url": r.get("url_especifica") or doc.get("url",""),
        "data": r.get("data_referencia"),
        "busca_em": r.get("busca_realizada_em",""),
        "busca_escopo": r.get("escopo_da_busca",""),
        "ressalva": (r.get("conferido_por_ia") or {}).get("ressalva",""),
        "revisado": bool(r.get("revisado_por_humano")),
        # contexto embutido: o agente precisa saber de quem e de que tema e a linha,
        # e derivar isso no navegador seria uma segunda fonte de verdade
        "cid": alvo, "tid": r["id_tema"],
    })
# citacao literal primeiro — regra mecanica declarada, sem juizo editorial
for t in grade:
    for cid in grade[t]:
        grade[t][cid].sort(key=lambda i: (0 if i["citacao"] else 1))

# ---------------------------------------------------------------------------
# POR QUE ESTA CELULA ESTA VAZIA — por candidatura, e nao uma frase so.
#
# O texto antigo era "Este cruzamento ainda nao foi trabalhado", igual para todo
# mundo. Mas os motivos sao diferentes e a diferenca importa: quem nao declarou
# site ao TSE, quem declarou um endereco que nao existe, e quem tem site que
# lemos inteiro e nao fala do tema nao estao na mesma situacao. Sem isso, 16
# candidaturas com proposta fazem as outras 299 parecerem sem ideias — e o que
# a tela estaria medindo e quem tem site, nao quem tem proposta.
#
# Tudo aqui e afirmacao sobre A NOSSA BUSCA, e sai so do que foi registrado.
_coleta_sites = {}
_f = DADOS_UF / "_coleta_sites.json"
if _f.exists():
    _coleta_sites = {r["id_candidatura"]: r
                     for r in json.loads(_f.read_text(encoding="utf-8"))["registros"]}

for _c in cands:
    _cid = _c["id_candidatura"]
    _ct = _c.get("contato") or {}
    _site = _ct.get("site")
    _col = _coleta_sites.get(_cid)
    if not _site:
        _b = {"estado": "sem_site",
              "texto": ("Esta candidatura não declarou site próprio no registro no TSE. "
                        "Procuramos onde a lei manda declarar; a ausência é do registro, "
                        "não da candidatura.")}
    elif _col is None:
        _b = {"estado": "nao_coletado", "url": _site,
              "texto": ("Esta candidatura declarou um site ao TSE, e ainda não o "
                        "coletamos. A lacuna é nossa.")}
    elif _col.get("_indisponivel"):
        _b = {"estado": "site_fora_do_ar", "url": _site, "quando": _col.get("coletado_em"),
              "texto": ("O site que esta candidatura declarou ao TSE não respondeu quando "
                        "tentamos ler, em " + str(_col.get("coletado_em")) + ".")}
    elif _col.get("_sem_material"):
        _b = {"estado": "site_sem_conteudo", "url": _col.get("url_final") or _site,
              "quando": _col.get("coletado_em"),
              "texto": ("O site que esta candidatura declarou ao TSE respondeu, e não "
                        "trouxe texto que pudéssemos ler (em " + str(_col.get("coletado_em")) + ").")}
    else:
        _b = {"estado": "site_lido", "url": _col.get("url_final") or _site,
              "quando": _col.get("coletado_em"),
              "paginas": len(_col.get("paginas") or []),
              "texto": ("Lemos " + str(len(_col.get("paginas") or [])) + " página(s) do site "
                        "que esta candidatura declarou ao TSE, em " + str(_col.get("coletado_em")) +
                        ", e não encontramos nada dela sobre este tema.")}
    cand_por_id[_cid]["busca"] = _b

leg = {t["id_tema"]: {} for t in temas}
for rg in regs["registros"]:
    for a in rg.get("autoria", []):
        if a["id_candidatura"] not in cand_por_id: continue
        for t in rg.get("temas", []):
            leg[t].setdefault(a["id_candidatura"], []).append({
                "rotulo": f'{rg["tipo"]} {rg["numero"]}/{rg["ano"]}',
                "casa": rg["casa"], "ementa": rg["ementa"],
                # link da propria proposicao, conferido pela ementa contra a casa
                # legislativa. Registro sem link e registro cuja ementa nao bateu.
                "url": rg.get("url", ""),
                "ordem_autoria": a.get("ordem_autoria"), "total_autores": a.get("total_autores"),
            })

# Cada voto carrega A PERGUNTA QUE FOI VOTADA, e nao a do registro. Antes as duas
# listas eram achatadas e a pergunta principal era carimbada nas duas: na tela
# apareciam "Nao" e "Sim" para a mesma pergunta, o que le como contradicao — e
# publicava um voto sob uma pergunta que nao foi aquela.
votos = []
for v in regs.get("votacoes_nominais", []):
    adicional = v.get("voto_adicional") or {}
    # A ressalva do registro descreve A PERGUNTA PRINCIPAL. Copiar para o voto
    # adicional grudava nele um texto sobre outra pergunta — o mesmo erro de
    # atribuicao, uma camada abaixo.
    # VOTO SEM ASSUNTO NAO PUBLICA.
    #
    # "Aprovacao do Projeto de Lei no 6.139/2023, ressalvado o destaque" era o que
    # o visitante lia. Dois candidatos votaram "Nao" — em que? A pergunta e o
    # texto regimental da sessao, e nao diz do que trata a proposicao. Publicar
    # voto assim informa que a pessoa votou, e nao no que ela votou, que e a
    # unica parte util.
    if not (v.get("assunto") or "").strip():
        raise SystemExit(
            f"PAROU: votacao sem 'assunto' em dados/{_UF.lower()}/registros_legislativos.json"
            + chr(10) + f"  pergunta: {v.get('pergunta')}"
            + chr(10) + "Escreva em 'assunto' do que trata a proposicao, em linguagem simples."
            + chr(10) + "Voto sem isso diz que a pessoa votou, e nao no que ela votou.")

    grupos = [(v.get("pergunta"), v.get("votos", []), v.get("_cuidado", ""),
               v.get("assunto", ""))]
    if adicional.get("votos"):
        grupos.append((adicional.get("pergunta") or v.get("pergunta"),
                       adicional["votos"],
                       adicional.get("_cuidado", ""),
                       adicional.get("assunto") or v.get("assunto", "")))
    for pergunta, lista, cuidado, assunto in grupos:
        for x in lista:
            if x["id_candidatura"] not in cand_por_id:
                continue
            votos.append({"cand": x["id_candidatura"], "voto": x["voto"],
                          "pergunta": pergunta, "data": v["data"],
                          # Do que trata a proposicao, em linguagem de quem le.
                          "assunto": assunto,
                          # Quantas vezes a mesma pergunta foi votada na sessao com
                          # esse mesmo voto. Sem isso, "votou Nao duas vezes" some.
                          "ocorrencias": x.get("ocorrencias"),
                          "proposicao": v["proposicao_objeto"]["rotulo"],
                          "temas": v.get("temas", []), "cuidado": cuidado})

# Respostas recebidas dos gabinetes. Arquivo pode nao existir ainda — nenhuma
# resposta e um estado legitimo, nao um erro de configuracao.
_rp = DADOS_UF/"respostas.json"
respostas = json.loads(_rp.read_text(encoding="utf-8"))["respostas"] if _rp.exists() else []

# Base de conhecimento da curadoria, publicada na aba "Como e feito". Vem do
# mesmo arquivo que o validador cobra: pagina de metodologia escrita a mao
# envelhece em silencio e passa a descrever um processo que nao existe mais.
_kb = HERE/"conhecimento"/"regras.json"
conhecimento = json.loads(_kb.read_text(encoding="utf-8")) if _kb.exists() else None

# Estado sem pesquisa levantada e caso normal, e nao defeito: a regra do projeto
# e que pesquisa so entra com ficha tecnica completa e registro no TSE. Sem
# nenhuma, a aba nao aparece — melhor aba ausente que aba vazia, que o leitor le
# como "ninguem pesquisou este estado".
q = (pesq["pesquisas"] or [None])[0]
pesquisa = None if not q else {
    "instituto": q["instituto"], "registro": q["registro_tse"],
    "ini": q["campo_inicio"], "fim": q["campo_fim"], "n": q["entrevistados"],
    "erro": q["margem_erro_pp"], "conf": q["nivel_confianca"],
    "resultados": {r["id_candidatura"]: r for r in q["resultados"]},
    "outros": q.get("outros", [])}
if pesquisa is None:
    print(f"  sem pesquisa registrada em {_UF}: a aba Pesquisa nao entra nesta pagina")

# Endpoint do backend do agente. Arquivo ausente = recurso desligado e o site
# se comporta exatamente como antes. Nada de chave nem segredo aqui: so a URL.
_ep = HERE/"agente-endpoint.txt"
agente_url = _ep.read_text(encoding="utf-8").strip() if _ep.exists() else ""

dados = {
    "atualizado": "24 de agosto de 2026",
    "agente_url": agente_url,
    "temas": [{"id": t["id_tema"], "nome": t["nome"]} for t in temas],
    "ordem": ordem, "candidatos": cand_por_id, "grade": grade, "leg": leg,
    "votos": votos, "pesquisa": pesquisa, "respostas": respostas,
    "conhecimento": conhecimento,
    "selos": {k: {"nome": v["nome"], "def": v["definicao"], "eixo": v["eixo"]}
              for k, v in selos.items()},
    "totais": {
        "posicoes": len(pos_publicaveis),
        "revisadas": sum(1 for r in pos_publicaveis if r.get("revisado_por_humano")),
        "reprovadas": pos_reprovadas,
        "levantadas": len(pos),
    },
}

# Hashes do acervo. O backend so aceita redigir a partir de texto cujo hash esta
# aqui: e a prova de que a linha veio do acervo, e nao de um navegador adulterado.
# Gerado junto com o site pela mesma razao que o site e gerado — nao pode divergir.
# So o que e publicavel entra: se uma posicao foi reprovada na revisao e saiu do
# site, o backend tambem nao deve aceitar redigir a partir dela. Deixar o hash
# para tras manteria o texto errado alcancavel por um cliente adulterado.
chaves = sorted({
    hashlib.sha256(((r.get("texto") or "") + chr(0) + (r.get("citacao_literal") or ""))
                   .encode("utf-8")).hexdigest()[:16]
    for r in pos_publicaveis
})
ag = HERE/"agente"
ag.mkdir(exist_ok=True)
(ag/"acervo-hashes.json").write_text(
    json.dumps({"gerado_de": "dados/posicoes.json", "n": len(chaves), "chaves": chaves},
               ensure_ascii=False, indent=1), encoding="utf-8")

# Catalogo para o backend: quem sao as candidaturas e os temas validos, e qual
# o contato OFICIAL de cada uma. O worker recusa pergunta dirigida a id que nao
# esteja aqui, e a pagina de moderacao usa o e-mail para montar a mensagem.
# Contato so de fonte oficial — nunca raspado de rede social, nunca achado em
# busca: mandar eleitor escrever para a pessoa errada seria pior que nao mandar.
# A UF viaja no catalogo porque o worker precisa dela para montar prompt e nao
# pode adivinhar: os textos que ele gera dizem de que estado se trata.
_sitecfg = ref.get("site") or {}
# A UF vem de _UF (--uf, ou o padrao de referencia.json), e nao de site.uf direto:
# senao --uf pe leria o acervo de PE e rotularia a pagina como SP.
_est = acervo.estado(_UF)

# Agora que a UF e conhecida, o destino e a profundidade dos assets seguem dela.
OUT = BASE / _est["uf"].lower() / "index.html"
OUT.parent.mkdir(parents=True, exist_ok=True)
# "../" porque a pagina desceu um nivel; as fontes e as fotos ficam na raiz,
# compartilhadas pelos 27 estados em vez de copiadas 27 vezes.
PREFIXO = "../"

(ag/"catalogo.json").write_text(json.dumps({
    "uf": _est["uf"],
    "uf_nome": _est["nome"],
    # "por Sao Paulo", "pelo Acre", "pela Bahia" — a preposicao vem do dado
    # porque concordancia errada em texto que sai de casa parece descuido.
    "uf_por": {"de": "por", "do": "pelo", "da": "pela"}[_est["preposicao"]] + " " + _est["nome"],
    "uf_assembleia": _est["assembleia"],
    "site_url": _sitecfg.get("url", ""),
    "temas": [{"id": t["id_tema"], "nome": t["nome"]} for t in temas],
    "candidaturas": [{
        "id": cid,
        "nome": cand_por_id[cid]["nome"],
        "partido": cand_por_id[cid]["partido"],
        "numero": cand_por_id[cid]["numero"],
        "email": (cand_por_id[cid].get("contato") or {}).get("email"),
        "email_fonte": (cand_por_id[cid].get("contato") or {}).get("email_fonte"),
        "email_tipo": (cand_por_id[cid].get("contato") or {}).get("email_tipo"),
        # Instagram entra como ATALHO manual, nunca como envio automatico: a API
        # so permite responder quem escreveu nas ultimas 24h, e automatizar conta
        # pessoal por fora viola os termos e derruba a conta.
        "instagram": (cand_por_id[cid].get("contato") or {}).get("instagram"),
        "instagram_fonte": (cand_por_id[cid].get("contato") or {}).get("instagram_fonte"),
    } for cid in ordem],
}, ensure_ascii=False, indent=1), encoding="utf-8")

tpl = (HERE/"_template_site.html").read_text(encoding="utf-8")
# A UF vai para o JS do site: o e-mail que o eleitor abre pronto e o texto de
# mensagem citam o estado, e sao textos que saem da maquina dele para um gabinete.
# A foto tambem e caminho relativo, e mora nos dados. Sem o prefixo, o <img>
# aponta para fora e o site mostra as iniciais — que o leitor le como
# "candidatura sem foto", uma afirmacao diferente e falsa.
for _c in dados["candidatos"].values():
    if _c.get("foto"):
        _c["foto"] = PREFIXO + _c["foto"]

dados["uf"] = {
    "sigla": _est["uf"], "nome": _est["nome"],
    "preposicao": _est["preposicao"],     # "de" São Paulo, "do" Acre, "da" Bahia
    "por": {"de": "por", "do": "pelo", "da": "pela"}[_est["preposicao"]] + " " + _est["nome"],
    "assembleia": _est["assembleia"],
}
dados["site_url"] = _sitecfg.get("url", "")

# O endereco de contato vem dos dados, e o texto visivel sai do MESMO campo do
# href: assim os dois nao podem divergir. urlencode so no assunto, que e a parte
# que precisa dele.
_email = ((ref.get("contato") or {}).get("email") or "").strip()
if not _email:
    raise SystemExit("dados/referencia.json nao tem contato.email — o site ficaria sem contato")
# O assunto trazia "SP" fixo, e as 27 paginas mandavam e-mail dizendo Sao Paulo.
# Quem escreve do Acre nomeando Sao Paulo no assunto obriga quem le a adivinhar
# de onde veio \u2014 e o assunto existe justamente para nao precisar adivinhar.
_assunto = urllib.parse.quote(f"Senado {_UF} 2026 \u2014 feedback")
# Marcadores de UF no HTML estatico (titulo, cabecalho, explicador). Cada um
# tem de aparecer, senao o site sai dizendo o estado errado ou nenhum.
for _m, _v in (("{{UF_NOME}}", dados["uf"]["nome"]), ("{{UF_POR}}", dados["uf"]["por"]),
               # Estava escrito "15" no template, do tempo em que so havia Sao
               # Paulo. Com 27 estados, 26 paginas anunciavam o numero de outro
               # estado logo abaixo do titulo.
               ("{{N_CANDIDATURAS}}", str(len(dados["candidatos"])))):
    if _m not in tpl:
        raise SystemExit(f"_template_site.html perdeu o marcador {_m}")
    tpl = tpl.replace(_m, _v)

if "{{RAIZ}}" not in tpl:
    raise SystemExit("_template_site.html perdeu o marcador {{RAIZ}} das fontes")
tpl = tpl.replace("{{RAIZ}}", PREFIXO)

tpl = tpl.replace("{{MAILTO}}", f"mailto:{_email}?subject={_assunto}").replace("{{EMAIL}}", _email)

# Sem o link de volta, quem entra num estado so sai pelo botao do navegador — e
# quem chega por link direto nunca ve o mapa. E um <a> solto no template: some
# numa refatoracao sem quebrar nada, do mesmo jeito que o "15" ficou para tras.
if f'class="voltar-mapa" href="{PREFIXO}"' not in tpl:
    raise SystemExit("_template_site.html perdeu o link de volta para a pagina inicial"
                     + chr(10) + f'  esperado: <a class="voltar-mapa" href="{PREFIXO}">')

OUT.write_text(tpl.replace("/*__DADOS__*/", json.dumps(dados, ensure_ascii=False)), encoding="utf-8")
print(f"gerado: {OUT.name}  ({OUT.stat().st_size/1024:.0f} KB)")
print(f"  temas {len(temas)} · candidaturas {len(ordem)} · publicadas {len(pos_publicaveis)}"
      f" · revisadas {dados['totais']['revisadas']} · reprovadas e retiradas {pos_reprovadas}")
com_foto = sum(1 for cid in ordem if cand_por_id[cid].get("foto"))
print(f"  fotos: {com_foto} de {len(ordem)} (credito TSE — registro de candidatura)")
