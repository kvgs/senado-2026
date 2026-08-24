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

BASE = pathlib.Path(__file__).parent
HERE = BASE
OUT = BASE / "index.html"

ref = json.loads((BASE/"dados"/"referencia.json").read_text(encoding="utf-8"))
cands = json.loads((BASE/"dados"/"candidaturas.json").read_text(encoding="utf-8"))["candidaturas"]
pos = json.loads((BASE/"dados"/"posicoes.json").read_text(encoding="utf-8"))["posicoes"]
docs = {d["id_documento"]: d for d in json.loads((BASE/"dados"/"documentos.json").read_text(encoding="utf-8"))["documentos"]}
pesq = json.loads((BASE/"dados"/"pesquisas.json").read_text(encoding="utf-8"))
regs = json.loads((BASE/"dados"/"registros_legislativos.json").read_text(encoding="utf-8"))

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
    fem = p["nome_urna"] in ("Simone Tebet","Marina Silva","Soninha Francine",
                             "Dra Eliana Ferreira","Maíra de Souza")
    frases = []
    frases.append(f'Declarou ao TSE a ocupação de {p["ocupacao_declarada"].lower()}.')

    parl = (c.get("situacao_parlamentar") or [{}])[0]
    if parl.get("casa") == "camara":
        t = f'Exerce mandato de deputad{"a" if fem else "o"} federal por São Paulo'
        if parl.get("desde"):
            t += f', em exercício desde {parl["desde"][8:10]}/{parl["desde"][5:7]}/{parl["desde"][:4]}'
        if parl.get("motivo_afastamento_anterior"):
            t += f' — antes disso, {parl["motivo_afastamento_anterior"][0].lower() + parl["motivo_afastamento_anterior"][1:]}'
        frases.append(t + '.')
    elif parl.get("casa") == "alesp":
        t = 'Exerce mandato de deputado estadual em São Paulo'
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
        "situacao": c["situacao_registro"][0]["situacao"],
        "situacao_em": c["situacao_registro"][0]["observado_em"],
        "sequencial": c.get("sequencial_tse"),
        "suplentes": c.get("suplentes", []),
        "foto": None,   # encaixe: preenchido quando o dataset de fotos do TSE for baixado
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

votos = []
for v in regs.get("votacoes_nominais", []):
    for x in v.get("votos", []) + (v.get("voto_adicional") or {}).get("votos", []):
        if x["id_candidatura"] in cand_por_id:
            votos.append({"cand": x["id_candidatura"], "voto": x["voto"],
                          "pergunta": v["pergunta"], "data": v["data"],
                          "proposicao": v["proposicao_objeto"]["rotulo"],
                          "temas": v.get("temas", []), "cuidado": v.get("_cuidado","")})

# Respostas recebidas dos gabinetes. Arquivo pode nao existir ainda — nenhuma
# resposta e um estado legitimo, nao um erro de configuracao.
_rp = HERE/"dados"/"respostas.json"
respostas = json.loads(_rp.read_text(encoding="utf-8"))["respostas"] if _rp.exists() else []

q = pesq["pesquisas"][0]
pesquisa = {"instituto": q["instituto"], "registro": q["registro_tse"],
            "ini": q["campo_inicio"], "fim": q["campo_fim"], "n": q["entrevistados"],
            "erro": q["margem_erro_pp"], "conf": q["nivel_confianca"],
            "resultados": {r["id_candidatura"]: r for r in q["resultados"]},
            "outros": q.get("outros", [])}

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
(ag/"catalogo.json").write_text(json.dumps({
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
OUT.write_text(tpl.replace("/*__DADOS__*/", json.dumps(dados, ensure_ascii=False)), encoding="utf-8")
print(f"gerado: {OUT.name}  ({OUT.stat().st_size/1024:.0f} KB)")
print(f"  temas {len(temas)} · candidaturas {len(ordem)} · publicadas {len(pos_publicaveis)}"
      f" · revisadas {dados['totais']['revisadas']} · reprovadas e retiradas {pos_reprovadas}")
print(f"  fotos: 0 de {len(ordem)} (dataset do TSE bloqueado — encaixe pronto)")
