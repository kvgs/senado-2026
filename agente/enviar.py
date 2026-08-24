# -*- coding: utf-8 -*-
"""Envia as perguntas da fila para os gabinetes, pelo seu proprio e-mail.

POR QUE NAO NO WORKER
O Cloudflare Worker nao abre SMTP com facilidade, e todo servico de envio por
HTTP exige dominio proprio verificado — o e-mail sairia de um dominio novo, com
cara de robo, e nao do seu endereco. Rodando aqui, sai da sua conta de verdade:
aparece na sua caixa de Enviados, e a resposta do gabinete cai na sua caixa de
entrada. Para uma conversa que voce quer que aconteca, isso importa.

O QUE ELE NAO FAZ
Nao decide nada. Voce escolhe a candidatura e ve a mensagem antes de sair.
Nao existe modo "enviar tudo sem olhar", de proposito: o dia em que uma pergunta
ofensiva escorregar para a caixa de um gabinete assinada por voce, o projeto
inteiro perde credibilidade, e isso nao se recupera com pedido de desculpas.

USO
    python enviar.py --listar
    python enviar.py --simular sen-sp-2026-marina
    python enviar.py --enviar  sen-sp-2026-marina

CREDENCIAIS (por variavel de ambiente, nunca em arquivo versionado)
    AGENTE_URL     https://agente-senado-sp-2026.senado-2026.workers.dev
    AGENTE_TOKEN   o mesmo TOKEN_ADMIN gravado na Cloudflare
    GMAIL_USUARIO  seu endereco
    GMAIL_SENHA    SENHA DE APP do Gmail, nao a senha da conta
                   (myaccount.google.com/apppasswords — exige 2 etapas ligada)
O que faltar, ele pergunta na hora, sem ecoar na tela.
"""
import argparse
import getpass
import json
import os
import smtplib
import ssl
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from email.message import EmailMessage

PADRAO_URL = "https://agente-senado-sp-2026.senado-2026.workers.dev"

# A Cloudflare bloqueia o User-Agent padrao do Python ("Python-urllib/3.x") com
# erro 1010 antes de a requisicao chegar no worker. Um identificador proprio
# passa — e diz de verdade quem esta chamando, que e o que um User-Agent serve
# para fazer.
AGENTE_HTTP = "senado-sp-2026-enviar/1.0 (+https://kvgs.github.io/senado-sp-2026/)"

QUEBRA = chr(10)   # escape de nova linha nao sobrevive a todo caminho de edicao


# --------------------------------------------------------------- credenciais

def pega(nome, rotulo, secreto=False):
    v = os.environ.get(nome)
    if v:
        return v.strip()
    v = getpass.getpass(f"{rotulo}: ") if secreto else input(f"{rotulo}: ")
    return v.strip()


# ------------------------------------------------------------- fala com a API

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
        if "1010" in detalhe:
            raise SystemExit(QUEBRA.join([
                "A Cloudflare bloqueou a chamada antes de chegar no worker (erro 1010).",
                "Isso acontece quando o User-Agent parece robo. O script ja manda um",
                "identificador proprio; se voltou a acontecer, veja em Security -> Bots,",
                "no painel da Cloudflare, se o Bot Fight Mode foi ligado.",
            ]))
        raise SystemExit(f"Erro {e.code} ao falar com o backend: {detalhe[:200]}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Nao consegui alcancar o backend: {e.reason}")


# ------------------------------------------------------------------ mensagem

def montar(cand, temas_por_id, perguntas):
    """Monta UMA mensagem representando todas as perguntas selecionadas.

    A agregacao e o ponto do desenho: um eleitor e ignoravel, quinze nao sao.
    """
    por_tema = defaultdict(list)
    for p in perguntas:
        por_tema[p.get("id_tema") or ""].append(p)

    n = len(perguntas)
    corpo = [
        f"Prezada assessoria de {cand['nome']},",
        "",
        "Escrevo em nome do projeto Senado por Sao Paulo 2026",
        "(https://kvgs.github.io/senado-sp-2026/), um site independente e sem fins",
        "lucrativos que reune as propostas das candidaturas ao Senado por Sao Paulo,",
        "sempre com a fonte oficial de cada informacao.",
        "",
        "Procuramos nas fontes publicas disponiveis e nao localizamos posicao",
        "registrada sobre os pontos abaixo. "
        + ("Um eleitor nos perguntou o seguinte:" if n == 1
           else f"{n} eleitores nos perguntaram sobre estes pontos:"),
        "",
    ]
    for tid, itens in por_tema.items():
        corpo.append(temas_por_id.get(tid, "Sem tema identificado").upper())
        for p in itens:
            corpo.append(f"  - {p['pergunta']}")
        corpo.append("")

    corpo += [
        "Qualquer resposta sera publicada na integra, identificada como declaracao",
        "da candidatura e com a data em que foi recebida. Se a candidatura preferir",
        "nao responder, registraremos apenas que a pergunta foi feita, sem",
        "interpretar o silencio.",
        "",
        "Se preferirem indicar um documento publico que ja trate do assunto, tambem",
        "serve — e e a forma que preferimos, porque podemos citar a fonte original.",
        "",
        "Agradeco a atencao.",
        "",
    ]
    assunto = ("Pergunta de eleitores sobre a candidatura ao Senado por SP"
               + (f" ({n} perguntas)" if n > 1 else ""))
    return assunto, "\n".join(corpo)


# -------------------------------------------------------------------- envio

def enviar_email(usuario, senha, para, assunto, texto):
    msg = EmailMessage()
    msg["From"] = usuario
    msg["To"] = para
    msg["Reply-To"] = usuario          # a resposta tem de voltar para voce
    msg["Subject"] = assunto
    msg.set_content(texto)

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx, timeout=45) as s:
        s.login(usuario, senha)
        s.send_message(msg)


# --------------------------------------------------------------------- fluxo

def carregar(url, token):
    d = chamar(url, token, "/fila")
    if d.get("erro"):
        raise SystemExit("Backend recusou: " + d["erro"])
    cat = d["catalogo"]
    cands = {c["id"]: c for c in cat["candidaturas"]}
    temas = {t["id"]: t["nome"] for t in cat["temas"]}
    pend = [p for p in d["perguntas"] if p["estado"] == "pendente"]
    return cands, temas, pend


def listar(cands, temas, pend):
    if not pend:
        print("Fila vazia. Nada pendente.")
        return
    por_cand = defaultdict(list)
    for p in pend:
        por_cand[p["id_candidatura"]].append(p)

    print(f"{len(pend)} pergunta(s) pendente(s)\n")
    for cid in sorted(por_cand, key=lambda k: -len(por_cand[k])):
        c = cands.get(cid, {"nome": cid, "partido": "", "email": None})
        marca = "  " if c.get("email") else "  [SEM CONTATO OFICIAL] "
        print(f"{len(por_cand[cid]):>3} pergunta(s) · {c['nome']} ({c.get('partido','')}){marca}")
        print(f"      id: {cid}")
        for p in por_cand[cid]:
            print(f"      - [{temas.get(p.get('id_tema') or '', 'sem tema')}] {p['pergunta']}")
        print()


def preparar(cands, temas, pend, cid):
    c = cands.get(cid)
    if not c:
        raise SystemExit(f"Candidatura desconhecida: {cid}")
    itens = [p for p in pend if p["id_candidatura"] == cid]
    if not itens:
        raise SystemExit(f"Nenhuma pergunta pendente para {c['nome']}.")
    if not c.get("email"):
        raise SystemExit(
            f"{c['nome']} nao tem e-mail oficial registrado.\n"
            "So temos contato das candidaturas com mandato. As demais dependem do\n"
            "dataset 'Redes sociais de candidatos' do TSE, ainda pendente de download.\n"
            "Contato so entra aqui vindo de fonte oficial: mandar eleitor escrever\n"
            "para a pessoa errada seria pior que nao mandar."
        )
    assunto, texto = montar(c, temas, itens)
    return c, itens, assunto, texto


def mostrar(c, itens, assunto, texto):
    print("=" * 70)
    print(f"Para:    {c['email']}")
    print(f"Fonte do contato: {c.get('email_fonte') or 'nao registrada'}")
    print(f"Assunto: {assunto}")
    print(f"Perguntas: {len(itens)}")
    print("=" * 70)
    print(texto)
    print("=" * 70)


def main():
    ap = argparse.ArgumentParser(description="Envia perguntas da fila aos gabinetes.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--listar", action="store_true", help="mostra a fila pendente")
    g.add_argument("--simular", metavar="ID", help="monta a mensagem e NAO envia")
    g.add_argument("--enviar", metavar="ID", help="monta, confirma e envia")
    g.add_argument("--autoteste", action="store_true",
                   help="testa a montagem da mensagem sem rede e sem credenciais")
    a = ap.parse_args()

    if a.autoteste:
        return autoteste()

    url = os.environ.get("AGENTE_URL", PADRAO_URL)
    token = pega("AGENTE_TOKEN", "Token de moderacao", secreto=True)
    cands, temas, pend = carregar(url, token)

    if a.listar:
        return listar(cands, temas, pend)

    cid = a.simular or a.enviar
    c, itens, assunto, texto = preparar(cands, temas, pend, cid)
    mostrar(c, itens, assunto, texto)

    if a.simular:
        print("\nSimulacao: nada foi enviado.")
        return

    if input(f"\nEnviar para {c['email']}? digite ENVIAR para confirmar: ").strip() != "ENVIAR":
        print("Cancelado. Nada saiu.")
        return

    usuario = pega("GMAIL_USUARIO", "Seu endereco Gmail")
    senha = pega("GMAIL_SENHA", "Senha de APP do Gmail", secreto=True)

    try:
        enviar_email(usuario, senha, c["email"], assunto, texto)
    except smtplib.SMTPAuthenticationError:
        raise SystemExit(
            "Gmail recusou o login. Quase sempre e porque a senha usada foi a da\n"
            "conta, e nao uma SENHA DE APP. Crie uma em myaccount.google.com/apppasswords\n"
            "(precisa da verificacao em duas etapas ligada)."
        )
    print(f"Enviado para {c['email']}.")

    r = chamar(url, token, "/decidir",
               {"ids": [p["id"] for p in itens], "estado": "enviada",
                "nota": f"enviada por e-mail para {c['email']}"})
    if r.get("erro"):
        print("ATENCAO: o e-mail saiu, mas nao consegui marcar na fila: " + r["erro"])
        print("Marque na pagina /admin para nao perguntar duas vezes.")
    else:
        print(f"{r.get('atualizadas', 0)} pergunta(s) marcada(s) como enviada(s).")


def autoteste():
    """Prova a montagem da mensagem sem rede, sem credenciais e sem enviar nada."""
    cands = {"x": {"id": "x", "nome": "Fulana de Tal", "partido": "PXX",
                   "email": "gabinete@exemplo.leg.br", "email_fonte": "Camara (dados abertos)"}}
    temas = {"t5": "Infraestrutura e Mobilidade Urbana", "t7": "Habitacao"}
    pend = [
        {"id": "1", "id_candidatura": "x", "id_tema": "t5", "estado": "pendente",
         "pergunta": "Ha posicao sobre a duplicacao da Rodovia dos Tamoios?"},
        {"id": "2", "id_candidatura": "x", "id_tema": "t5", "estado": "pendente",
         "pergunta": "E sobre transporte hidroviario de passageiros?"},
        {"id": "3", "id_candidatura": "x", "id_tema": "t7", "estado": "pendente",
         "pergunta": "Qual a posicao sobre locacao social?"},
    ]
    print(">>> listar\n")
    listar(cands, temas, pend)
    print(">>> mensagem montada\n")
    c, itens, assunto, texto = preparar(cands, temas, pend, "x")
    mostrar(c, itens, assunto, texto)

    # O corpo e quebrado em linhas fixas, entao a checagem tem de olhar o texto
    # com os espacos normalizados — senao uma frase que existe parece ausente.
    liso = " ".join(texto.split())

    faltas = []
    if "3 eleitores" not in liso: faltas.append("nao agregou a contagem de eleitores")
    if "Rodovia dos Tamoios" not in liso: faltas.append("perdeu uma pergunta")
    if "INFRAESTRUTURA E MOBILIDADE URBANA" not in liso: faltas.append("nao agrupou por tema")
    if "sem interpretar o silencio" not in liso: faltas.append("perdeu a clausula do silencio")
    if "(3 perguntas)" not in assunto: faltas.append("assunto sem a contagem")

    print("\n>>> sem contato oficial deve recusar")
    semmail = {"y": {"id": "y", "nome": "Beltrano", "partido": "PYY", "email": None}}
    try:
        preparar(semmail, temas, [{"id": "9", "id_candidatura": "y", "id_tema": None,
                                   "estado": "pendente", "pergunta": "Qualquer coisa aqui."}], "y")
        faltas.append("aceitou candidatura sem e-mail")
    except SystemExit:
        print("    OK  recusou, como deve")

    print("\n" + ("FALHAS: " + "; ".join(faltas) if faltas else "autoteste: tudo certo"))
    return 1 if faltas else 0


if __name__ == "__main__":
    sys.exit(main() or 0)
