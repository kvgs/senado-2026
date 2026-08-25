# -*- coding: utf-8 -*-
"""Gera a versao legivel da base de conhecimento, a partir do mesmo JSON.

Uma fonte, duas saidas — a mesma razao pela qual o site e gerado: documentacao
escrita a mao ao lado de regra executavel divergem, e quando divergem e a
documentacao que mente, porque ninguem roda documentacao.

    python gerar_conhecimento.py
"""
import json
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent
FONTE = RAIZ / "conhecimento" / "regras.json"
SAIDA = RAIZ / "conhecimento" / "REGRAS.md"

kb = json.loads(FONTE.read_text(encoding="utf-8"))
L = []

L.append("# Base de conhecimento da curadoria")
L.append("")
L.append("> **Arquivo gerado.** Não edite aqui — edite `conhecimento/regras.json` e rode")
L.append("> `python gerar_conhecimento.py`. As regras marcadas como mecânicas são cobradas")
L.append("> por `validar.py`, que recusa o arquivo em vez de avisar.")
L.append("")
L.append(kb["_o_que_e_isto"])
L.append("")
L.append(f"*{kb['_inspiracao']}*")
L.append("")

L.append("## O que cada tipo de fonte pode sustentar")
L.append("")
L.append("A pergunta não é se a fonte é boa. É se ela é do **tipo** que sustenta")
L.append("aquela **espécie** de afirmação. Um cadastro de candidaturas registra com")
L.append("precisão o partido de alguém, e simplesmente não contém o que essa pessoa")
L.append("propõe.")
L.append("")

for chave, f in kb["tipos_de_fonte"].items():
    L.append(f"### `{chave}` — {f['nome']}")
    L.append("")
    L.append(f["o_que_e"])
    L.append("")
    L.append(f"**Sustenta:** {', '.join(f['sustenta'])}")
    L.append("")
    L.append(f"**Não sustenta:** {', '.join(f['nao_sustenta'])}")
    L.append("")
    est = f.get("estados_permitidos")
    L.append("**Estados de cobertura permitidos:** "
             + (", ".join(est) if est else "nenhum — não sustenta proposta"))
    L.append("")
    L.append(f"**Por quê:** {f['porque']}")
    L.append("")
    if f.get("cuidado"):
        L.append(f"**Cuidado:** {f['cuidado']}")
        L.append("")
    if f.get("exige"):
        L.append(f"**Exige:** {', '.join(f['exige'])}")
        L.append("")

L.append("## Regras")
L.append("")
# Agrupar por ONDE, e nao por "mecanica ou humana": o que importa para quem le e
# se existe algo impedindo a violacao, e onde. Regra sem cobranca aparece
# separada, com o nome disso.
cobradas = [r for r in kb["regras"] if r.get("onde") not in ("AINDA NAO COBRADA", "revisao humana")]
humanas = [r for r in kb["regras"] if r.get("onde") == "revisao humana"]
descobertas = [r for r in kb["regras"] if r.get("onde") == "AINDA NAO COBRADA"]

L.append(f"{len(cobradas)} regras têm código que as impede, {len(humanas)} dependem de "
         f"julgamento na revisão, e {len(descobertas)} ainda não têm cobrança nenhuma.")
L.append("Cada uma existe porque foi violada uma vez — o campo *por quê* guarda o caso real.")
L.append("")

for titulo, grupo, nota in (
    ("Impedidas por código", cobradas, None),
    ("Dependem de julgamento humano", humanas,
     "Não dá para cobrar em código sem produzir falso erro, e validador que grita errado "
     "é validador desligado. Estas vivem na tela de revisão."),
    ("Sem cobrança ainda", descobertas,
     "Estão aqui para não serem esquecidas. Regra sem cobrança é lembrete, e lembrete "
     "é o que falhou antes."),
):
    if not grupo:
        continue
    L.append(f"### {titulo}")
    L.append("")
    if nota:
        L.append(f"*{nota}*")
        L.append("")
    for r in grupo:
        L.append(f"**{r['id']} — {r['titulo']}**")
        L.append("")
        L.append(f"{r['regra']}")
        L.append("")
        L.append(f"*Por quê:* {r['porque']}")
        L.append("")
        L.append(f"*Onde é cobrada:* `{r.get('onde', 'não declarado')}`")
        L.append("")

SAIDA.write_text("\n".join(L) + "\n", encoding="utf-8")
# Recorte da base para o backend do agente. Vai embutido no worker pela mesma
# razao que os hashes do acervo vao: se a pesquisa usasse uma copia propria das
# regras, ela divergiria do validador — e a divergencia apareceria como fonte
# aceita na pesquisa e recusada na hora de gravar.
CAMPOS = ("nome", "o_que_e", "sustenta", "nao_sustenta", "cuidado")
recorte = {
    "_gerado_de": "conhecimento/regras.json",
    "tipos_de_fonte": {
        k: {c: v[c] for c in CAMPOS if v.get(c)}
        for k, v in kb["tipos_de_fonte"].items()
    },
}
(RAIZ / "agente" / "regras.json").write_text(
    json.dumps(recorte, ensure_ascii=False, indent=1), encoding="utf-8")

n_tipos = len(kb["tipos_de_fonte"])
print(f"conhecimento/REGRAS.md gerado: {n_tipos} tipos de fonte · "
      f"{len(cobradas)} impedidas por codigo · {len(humanas)} humanas · "
      f"{len(descobertas)} sem cobranca")
