# -*- coding: utf-8 -*-
"""Coleta o material publicado nos sites que a candidatura declarou ao TSE.

O QUE ISTO E, NO MODELO DO SITE. Site de candidatura e selo ROXO — declaracao do
candidato. Prova que a pessoa disse aquilo, nunca que aquilo e verdade. E a
atribuicao aqui e a mais limpa que existe: dominio dela, primeira pessoa, sem
intermediario. Nao e o problema que derrubou 15 posicoes tipadas como reportagem.

O MODO DE FALHAR E OUTRO: PARAFRASE. Foi assim que "controle estatal dos precos"
virou "congelamento de precos" numa revisao — outra politica, mesma frase
aproximada. Por isso esta coleta guarda TRECHO LITERAL com o endereco exato de
onde saiu, e nao resumo. Resumir e trabalho de depois, e passa pela revisao.

ESTA ETAPA NAO AFIRMA NADA. Ela baixa, guarda o texto e registra o que
encontrou. Transformar isso em posicao atribuida a uma candidatura e outra
operacao, e nenhuma posicao entra no site sem alguem ter aberto a fonte.

CORTESIA COM SERVIDOR DE TERCEIRO
  - robots.txt consultado e OBEDECIDO, inclusive o crawl-delay
  - User-Agent identifica o projeto e da o endereco para reclamacao
  - uma requisicao por vez, com pausa entre elas
  - no maximo PAGINAS_POR_SITE paginas por dominio

AUSENCIA E INFORMACAO, tambem aqui. Site que responde 404, que esta "em breve",
que exige JavaScript ou que proibe robo NAO vira silencio: vira registro com o
motivo, porque "nao achamos proposta" e "a candidatura nao publicou proposta"
sao coisas diferentes.

USO
    python coletar_sites.py --uf PE            # mostra o que faria
    python coletar_sites.py --uf PE --gravar
    python coletar_sites.py --todos --gravar
    python coletar_sites.py --todos --gravar --limite 5   # piloto
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import date

import acervo

AGENTE = ("senado-2026/1.0 (+https://kvgs.github.io/senado-2026/; "
          "coleta de material de campanha declarado ao TSE)")

PAUSA = 2.0             # segundos entre requisicoes ao mesmo dominio
PAUSA_ENTRE_SITES = 1.0
PAGINAS_POR_SITE = 4
LIMITE_BYTES = 3_000_000
TEMPO = 25

# Palavras que indicam pagina de proposta. Procuradas no texto do link e no
# endereco. "Proposta" e "plano" sao as diretas; "bandeira" e "compromisso"
# aparecem no vocabulario de campanha com o mesmo papel.
SINAIS = ("proposta", "propostas", "plano", "programa", "bandeira", "bandeiras",
          "compromisso", "compromissos", "prioridade", "prioridades", "projeto",
          "por que", "porque", "ideias", "diretrizes", "carta", "manifesto",
          # Achados no piloto: o site do Jorge Viana chama a secao de propostas de
          # "O Que Penso", e a lista original nao pegava. Vocabulario de campanha
          # nao usa a palavra "proposta" com tanta frequencia quanto eu supus.
          "penso", "atuacao", "atuação", "defendo", "defende", "luta", "lutas",
          "causa", "causas", "pauta", "pautas", "quem sou", "trabalho",
          "meu trabalho", "nossas", "objetivo", "objetivos", "meta", "metas",
          "por um", "por uma", "mandato", "gestao", "gestão")

# Paginas que nunca tem proposta e so gastam requisicao.
IGNORAR = ("/politica-de-privacidade", "/privacidade", "/termos", "/cookies",
           "/login", "/doe", "/doacao", "/contato", "/imprensa", "/agenda",
           ".pdf", ".jpg", ".png", ".mp4", ".zip", "/feed", "/wp-json", "/wp-admin")

SEM_JS = re.compile(r"(habilite o javascript|enable javascript|requires javascript"
                    r"|precisa de javascript)", re.I)
EM_BREVE = re.compile(r"(em breve|coming soon|em constru[cç][aã]o|site em manuten[cç][aã]o)", re.I)


def buscar(url: str, tempo: int = TEMPO) -> tuple[int, str, bytes, str]:
    """Devolve (status, tipo, corpo, url_final). Excecao vira status 0."""
    req = urllib.request.Request(url, headers={
        "User-Agent": AGENTE,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=tempo) as r:
        return (r.status, r.headers.get("Content-Type", ""),
                r.read(LIMITE_BYTES), r.geturl())


def normalizar(u: str) -> str:
    """O TSE grava a maioria das URLs em caixa alta. Host nao tem caixa; caminho
    tem. Entao o host desce para minusculas e o caminho fica como veio — e as
    variantes sao tentadas em ordem, em vez de eu adivinhar qual esta certa."""
    u = u.strip()
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    p = urllib.parse.urlsplit(u)
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(),
                                    p.path, p.query, p.fragment))


def variantes(u: str) -> list[str]:
    """Enderecos a tentar, em ordem. Caminho em caixa alta 404 em servidor
    sensivel a caixa; o mesmo caminho em minusculas costuma existir."""
    base = normalizar(u)
    p = urllib.parse.urlsplit(base)
    fora = [base]
    if p.path and p.path != "/" and p.path != p.path.lower():
        fora.append(urllib.parse.urlunsplit((p.scheme, p.netloc, p.path.lower(),
                                             p.query, p.fragment)))
    if p.path not in ("", "/"):
        fora.append(urllib.parse.urlunsplit((p.scheme, p.netloc, "/", "", "")))
    # COM E SEM "www." sao hosts diferentes no DNS, e a candidatura declarou um
    # so. Cinco enderecos que resolvem no DNS falharam na coleta, e nenhum era
    # tentado na outra forma.
    outro = (p.netloc[4:] if p.netloc.startswith("www.") else "www." + p.netloc)
    fora.append(urllib.parse.urlunsplit((p.scheme, outro, p.path or "/", "", "")))
    fora.append(urllib.parse.urlunsplit((p.scheme, outro, "/", "", "")))
    if base.startswith("https://"):
        fora.append("http://" + base[len("https://"):])
        fora.append(urllib.parse.urlunsplit(("http", outro, "/", "", "")))
    return list(dict.fromkeys(fora))


def robo(base: str) -> tuple[urllib.robotparser.RobotFileParser | None, str]:
    p = urllib.parse.urlsplit(base)
    alvo = f"{p.scheme}://{p.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        st, _, corpo, _ = buscar(alvo, tempo=12)
        if st != 200:
            return None, f"robots.txt respondeu {st}: nada proibido explicitamente"
        rp.parse(corpo.decode("utf-8", "replace").splitlines())
        return rp, "robots.txt lido"
    except Exception as e:                       # noqa: BLE001 — rede falha de muitos jeitos
        return None, f"robots.txt nao obtido ({type(e).__name__}): nada proibido explicitamente"


def texto(corpo: bytes, tipo: str) -> str:
    cs = "utf-8"
    m = re.search(r"charset=([\w-]+)", tipo, re.I)
    if m:
        cs = m.group(1)
    s = corpo.decode(cs, "replace")
    if not m and re.search(r'charset=["\']?iso-8859-1', s[:2000], re.I):
        s = corpo.decode("latin-1", "replace")
    s = re.sub(r"<(script|style|noscript|svg)\b.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</(p|div|li|h[1-6]|tr)>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    # Erro de PHP vazando para dentro da pagina. O site de um senador imprime
    # "Warning: Use of undefined constant..." no meio do conteudo, e isso entraria
    # na coleta como se fosse texto da candidatura.
    s = re.sub(r"^\s*(Warning|Notice|Deprecated|Fatal error)\s*:.*$", "", s, flags=re.M)
    s = re.sub(r"[ \t\xa0]+", " ", s)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", s).strip()


def titulo(corpo: bytes, tipo: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", corpo.decode("utf-8", "replace"),
                  re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip() if m else ""


def links(corpo: bytes, tipo: str, base: str) -> list[tuple[str, str]]:
    """(url_absoluta, texto_do_link) das paginas internas que parecem proposta."""
    s = corpo.decode("utf-8", "replace")
    fora, host = [], urllib.parse.urlsplit(base).netloc
    # O padrao antigo era href="([^"'#]+)", que DESCARTA todo endereco contendo
    # "#" — e nao so a ancora pura. Site de campanha em pagina unica escreve
    # href="/#propostas", e o link chamado "Propostas" era justamente o que se
    # perdia. Agora casa o endereco inteiro e o fragmento e cortado depois.
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', s, re.S | re.I):
        href, rotulo = m.group(1).strip(), re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()
        if href.lower().startswith(("mailto:", "tel:", "javascript:")):
            continue
        u = urllib.parse.urljoin(base, href)
        if urllib.parse.urlsplit(u).netloc != host:
            continue
        b = u.lower()
        if any(x in b for x in IGNORAR):
            continue
        alvo = (rotulo + " " + urllib.parse.unquote(b))
        alvo = alvo.lower()
        if any(sig in alvo for sig in SINAIS):
            fora.append((u.split("#")[0], rotulo[:80]))
    vistos, unicos = set(), []
    for u, r in fora:
        if u not in vistos:
            vistos.add(u); unicos.append((u, r))
    return unicos


def diagnostico(t: str) -> str | None:
    """Motivo para o texto nao servir. Vira registro, nao silencio."""
    if len(t) < 400:
        if SEM_JS.search(t):
            return "pagina exige JavaScript: o conteudo nao vem no HTML"
        if EM_BREVE.search(t):
            return "pagina anuncia que esta em construcao ou em breve"
        return f"pagina devolveu pouco texto ({len(t)} caracteres)"
    return None


def coletar_um(c: dict, uf: str) -> dict:
    url = (c.get("contato") or {}).get("site")
    reg = {
        "id_candidatura": c["id_candidatura"],
        "uf": uf,
        "nome_urna": c["pessoa"]["nome_urna"],
        "url_declarada": url,
        "coletado_em": date.today().isoformat(),
        "_fonte": "Site declarado pela candidatura ao TSE (base de redes sociais 2026)",
        "_selo": "declaracao_do_candidato",
        "_nota_selo": ("Selo roxo: prova que a candidatura publicou isto, nunca que o "
                       "conteudo e verdadeiro."),
        "paginas": [],
    }

    inicial = None
    tentativas = []
    for v in variantes(url):
        try:
            st, tipo, corpo, final = buscar(v)
            tentativas.append(f"{v} -> {st}")
            if st == 200 and "html" in tipo.lower():
                inicial = (v, tipo, corpo, final)
                break
        except urllib.error.HTTPError as e:
            tentativas.append(f"{v} -> {e.code}")
        except Exception as e:                   # noqa: BLE001
            tentativas.append(f"{v} -> {type(e).__name__}")
        time.sleep(PAUSA)

    if inicial is None:
        reg["_indisponivel"] = ("Site declarado nao respondeu com pagina HTML. Tentativas: "
                                + "; ".join(tentativas))
        return reg

    v, tipo, corpo, final = inicial
    rp, nota_robo = robo(final)
    reg["robots"] = nota_robo
    atraso = None
    if rp is not None:
        try:
            atraso = rp.crawl_delay(AGENTE) or rp.crawl_delay("*")
        except Exception:                        # noqa: BLE001
            atraso = None
        if not rp.can_fetch(AGENTE, final):
            reg["_indisponivel"] = ("robots.txt do site proibe a coleta desta pagina. "
                                    "Nada foi guardado.")
            return reg
    pausa = max(PAUSA, float(atraso or 0))

    def guarda(u_, tipo_, corpo_, rotulo):
        t = texto(corpo_, tipo_)
        p = {
            "url": u_,
            "rotulo_do_link": rotulo,
            "titulo": titulo(corpo_, tipo_),
            "bytes": len(corpo_),
            "sha256_16": hashlib.sha256(corpo_).hexdigest()[:16],
            "caracteres_de_texto": len(t),
            # TRECHO LITERAL. Resumo vem depois e passa por revisao.
            "texto": t[:40000],
        }
        d = diagnostico(t)
        if d:
            p["_sem_conteudo_util"] = d
        return p

    reg["url_final"] = final
    reg["paginas"].append(guarda(final, tipo, corpo, "pagina inicial"))

    candidatos = links(corpo, tipo, final)
    reg["links_de_proposta_encontrados"] = [{"url": u, "rotulo": r} for u, r in candidatos]
    for u_, rot in candidatos[:PAGINAS_POR_SITE - 1]:
        if rp is not None and not rp.can_fetch(AGENTE, u_):
            continue
        time.sleep(pausa)
        try:
            st, tp, cp, fin = buscar(u_)
            if st == 200 and "html" in tp.lower():
                reg["paginas"].append(guarda(fin, tp, cp, rot))
        except Exception:                        # noqa: BLE001
            continue

    # MENU NAO E CONTEUDO. O texto literal fica inteiro, porque a citacao depende
    # dele; mas a linha que aparece em mais de uma pagina do mesmo site e
    # navegacao, e contar isso como material da candidatura inflaria a medida.
    # No piloto, uma pagina de 7 mil caracteres era quase toda menu.
    if len(reg["paginas"]) > 1:
        conta: collections.Counter = collections.Counter()
        for p in reg["paginas"]:
            for linha in {x.strip() for x in p["texto"].split("\n") if x.strip()}:
                conta[linha] += 1
        repetidas = {l for l, n in conta.items() if n == len(reg["paginas"]) and len(l) < 120}
        for p in reg["paginas"]:
            proprio = "\n".join(x for x in p["texto"].split("\n")
                                if x.strip() and x.strip() not in repetidas)
            p["caracteres_proprios"] = len(proprio)
    else:
        for p in reg["paginas"]:
            p["caracteres_proprios"] = p["caracteres_de_texto"]

    uteis = [p for p in reg["paginas"] if not p.get("_sem_conteudo_util")]
    if not uteis:
        reg["_sem_material"] = ("O site respondeu, e nenhuma pagina trouxe texto aproveitavel. "
                                "Isto e um fato sobre o site, nao sobre a candidatura.")
    return reg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--gravar", action="store_true")
    ap.add_argument("--limite", type=int, default=0, help="para piloto")
    a = ap.parse_args()
    if not a.uf and not a.todos:
        raise SystemExit("passe --uf XX ou --todos")

    ufs = acervo.com_acervo() if a.todos else [a.uf.upper()]
    alvos = []
    for uf in ufs:
        for c in acervo.ler("candidaturas.json", uf)["candidaturas"]:
            if (c.get("contato") or {}).get("site"):
                alvos.append((uf, c))
    if a.limite:
        alvos = alvos[:a.limite]

    print(f"{len(alvos)} site(s) a coletar, {PAUSA}s entre requisicoes, "
          f"ate {PAGINAS_POR_SITE} paginas por site.")
    if not a.gravar:
        for uf, c in alvos:
            print(f"  {uf} {c['pessoa']['nome_urna'][:24]:24} {c['contato']['site'][:56]}")
        print("\n(sem --gravar: nada foi baixado nem escrito)")
        return

    por_uf: dict[str, list] = collections.defaultdict(list)
    resumo: collections.Counter = collections.Counter()
    for i, (uf, c) in enumerate(alvos, 1):
        print(f"[{i}/{len(alvos)}] {uf} {c['pessoa']['nome_urna'][:22]:22}", end="  ", flush=True)
        reg = coletar_um(c, uf)
        por_uf[uf].append(reg)
        if reg.get("_indisponivel"):
            print("indisponivel"); resumo["indisponivel"] += 1
        elif reg.get("_sem_material"):
            print("respondeu, sem texto util"); resumo["sem texto util"] += 1
        else:
            n = len([p for p in reg["paginas"] if not p.get("_sem_conteudo_util")])
            ch = sum(p["caracteres_de_texto"] for p in reg["paginas"])
            print(f"{n} pagina(s), {ch/1000:.0f}k caracteres")
            resumo["com material"] += 1
        time.sleep(PAUSA_ENTRE_SITES)

    for uf, regs in por_uf.items():
        f = acervo.de(uf) / "_coleta_sites.json"
        antigo = json.loads(f.read_text(encoding="utf-8"))["registros"] if f.exists() else []
        novos = {r["id_candidatura"]: r for r in antigo}
        novos.update({r["id_candidatura"]: r for r in regs})
        f.write_text(json.dumps({"registros": list(novos.values())},
                                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"gravado: {f}  ({len(novos)} registro(s))")

    print()
    for k, v in resumo.most_common():
        print(f"  {v:4}  {k}")


if __name__ == "__main__":
    main()
