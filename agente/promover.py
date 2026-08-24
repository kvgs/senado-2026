# -*- coding: utf-8 -*-
"""Traz as respostas registradas no banco para dados/respostas.json.

POR QUE ESTA ETAPA EXISTE
O site e GERADO a partir de arquivos versionados no Git. Se a resposta fosse do
banco direto para a tela, existiria informacao publicada que nao esta no
repositorio, nao passa pelo validador e nao tem historico — e a primeira
pergunta que alguem faria ("de onde saiu isso?") nao teria resposta. A etapa
extra e o preco de conseguir responder essa pergunta sempre.

O QUE ELE NAO FAZ
Nao transforma resposta em "proposta". A resposta e publicada na integra, como
DECLARACAO da candidatura, que e exatamente o que a mensagem enviada prometeu.
Ler o texto e concluir "entao a posicao dela sobre X e Y" e curadoria, e
curadoria e humana.

PRIVACIDADE DO REMETENTE
O endereco completo fica no banco, que e privado. Para o repositorio publico vai
so o dominio — a menos que o endereco seja exatamente o contato oficial que ja
esta registrado no acervo, caso em que ele ja e publico e serve de prova de
procedencia. Assessor que responde de e-mail proprio nao vira dado publicado por
efeito colateral de ter respondido.

USO
    python promover.py --listar
    python promover.py --promover
"""
import argparse
import getpass
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PADRAO_URL = "https://agente-senado-sp-2026.senado-2026.workers.dev"
AGENTE_HTTP = "senado-sp-2026-promover/1.0 (+https://kvgs.github.io/senado-sp-2026/)"
QUEBRA = chr(10)
DESTINO = RAIZ / "dados" / "respostas.json"


def chamar(url, token, caminho, corpo=None):
    req = urllib.request.Request(
        url.rstrip("/") + caminho,
        data=json.dumps(corpo).encode("utf-8") if corpo is not None else None,
        headers={"x-token": token, "content-type": "application/json",
                 "User-Agent": AGENTE_HTTP},
        method="POST" if corpo is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", "replace")
        if e.code == 401:
            raise SystemExit(QUEBRA.join([
                "Token recusado (401). Confira se e o mesmo valor gravado com:",
                "  npx wrangler secret put TOKEN_ADMIN",
            ]))
        raise SystemExit(f"Erro {e.code} ao falar com o backend: {detalhe[:200]}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Nao consegui alcancar o backend: {e.reason}")


def carrega_acervo():
    d = json.loads((RAIZ / "dados" / "candidaturas.json").read_text(encoding="utf-8"))
    lst = d["candidaturas"] if isinstance(d, dict) else d
    return {c["id_candidatura"]: c for c in lst}


def dominio(endereco):
    return endereco.split("@")[-1].strip().lower() if "@" in endereco else ""


def publicavel(resposta, cands, perguntas_por_id):
    """Monta a versao que pode ir para o repositorio publico."""
    c = cands.get(resposta["id_candidatura"], {})
    oficial = ((c.get("contato") or {}).get("email") or "").strip().lower()
    de = resposta["remetente"].strip()
    bate = bool(oficial) and de.lower() == oficial

    ids = json.loads(resposta["perguntas_ids"]) if resposta.get("perguntas_ids") else []
    perguntas = [
        {"pergunta": perguntas_por_id[i]["pergunta"],
         "recebida_do_eleitor_em": perguntas_por_id[i]["criada_em"][:10]}
        for i in ids if i in perguntas_por_id
    ]

    return {
        "id_resposta": resposta["id"],
        "id_candidatura": resposta["id_candidatura"],
        "id_tema": resposta.get("id_tema"),
        "nivel_fonte": "declaracao_candidato",
        "canal": resposta["canal"],
        "recebida_em": resposta["recebida_em"],
        "registrada_em": resposta["registrada_em"][:10],
        # Endereco completo so quando ja e publico por ser o contato oficial.
        "remetente": de if bate else None,
        "remetente_dominio": dominio(de),
        "confere_com_contato_oficial": bate,
        "texto": resposta["texto"],
        "perguntas_que_responde": perguntas,
        "revisado_por_humano": False,
    }


def main():
    ap = argparse.ArgumentParser(description="Traz respostas do banco para dados/respostas.json")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--listar", action="store_true", help="mostra o que ha para promover")
    g.add_argument("--promover", action="store_true", help="grava e marca como promovido")
    a = ap.parse_args()

    url = os.environ.get("AGENTE_URL", PADRAO_URL)
    token = os.environ.get("AGENTE_TOKEN") or getpass.getpass("Token de moderacao: ")

    novas = chamar(url, token, "/respostas?pendentes=1")["respostas"]
    if not novas:
        print("Nenhuma resposta nova para promover.")
        return 0

    fila = chamar(url, token, "/fila")
    perguntas_por_id = {p["id"]: p for p in fila["perguntas"]}
    cands = carrega_acervo()
    temas = {t["id"]: t["nome"] for t in fila["catalogo"]["temas"]}

    prontas = [publicavel(r, cands, perguntas_por_id) for r in novas]

    print(f"{len(prontas)} resposta(s) para promover:{QUEBRA}")
    for r in prontas:
        nome = cands.get(r["id_candidatura"], {}).get("pessoa", {}).get("nome_urna", r["id_candidatura"])
        print(f"  {nome} — recebida em {r['recebida_em']} por {r['canal']}")
        print(f"    de: {r['remetente'] or '(dominio ' + r['remetente_dominio'] + ')'}"
              f"  confere com contato oficial: {'SIM' if r['confere_com_contato_oficial'] else 'nao'}")
        print(f"    tema: {temas.get(r['id_tema'], 'nao classificado')}")
        print(f"    responde {len(r['perguntas_que_responde'])} pergunta(s) da fila")
        print(f"    texto: {len(r['texto'])} caracteres, publicado na integra")
        if not r["confere_com_contato_oficial"]:
            print("    ATENCAO: o endereco nao bate com o contato oficial registrado.")
            print("    Confira antes de publicar — o site vai exibir essa ressalva ao leitor.")
        print()

    if a.listar:
        print("Nada gravado. Use --promover para gravar.")
        return 0

    if DESTINO.exists():
        atual = json.loads(DESTINO.read_text(encoding="utf-8"))
    else:
        atual = {
            "_regra_publicacao": (
                "Resposta de candidatura e publicada NA INTEGRA, como declaracao (selo roxo), "
                "e nunca convertida automaticamente em proposta. Interpretar o que ela significa "
                "e curadoria humana."
            ),
            "_regra_silencio": (
                "Silencio NAO vira posicao. Se perguntamos e nao houve resposta, o acervo registra "
                "que a pergunta foi feita e ate quando nao houve retorno — afirmacao sobre a nossa "
                "pergunta, nunca sobre a candidatura."
            ),
            "_regra_remetente": (
                "O endereco completo so e publicado quando coincide com o contato oficial ja "
                "registrado no acervo, porque ai ja era publico. Nos demais casos publica-se apenas "
                "o dominio: quem responde de e-mail proprio nao vira dado publicado por ter "
                "respondido."
            ),
            "respostas": [],
        }

    ja = {x["id_resposta"] for x in atual["respostas"]}
    novas_ok = [r for r in prontas if r["id_resposta"] not in ja]
    atual["respostas"].extend(novas_ok)
    atual["respostas"].sort(key=lambda x: x["recebida_em"], reverse=True)
    DESTINO.write_text(json.dumps(atual, ensure_ascii=False, indent=1), encoding="utf-8")

    r = chamar(url, token, "/promovidas", {"ids": [x["id_resposta"] for x in prontas]})
    if r.get("erro"):
        print("Gravado no arquivo, mas nao consegui marcar no banco: " + r["erro"])
        print("Elas vao reaparecer na proxima execucao — confira antes de gravar de novo.")
        return 1

    print(f"{len(novas_ok)} resposta(s) gravadas em dados/respostas.json")
    print(QUEBRA.join([
        "",
        "Falta publicar. Na raiz do projeto:",
        "  python validar.py",
        "  python gerar_site.py",
        '  git add -A && git commit -m "publica resposta recebida" && git push',
    ]))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
