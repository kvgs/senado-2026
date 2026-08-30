# -*- coding: utf-8 -*-
"""Grava em dados/<uf>/candidaturas.json o site e as redes que a candidatura
declarou AO TSE, da base "rede social de candidato".

POR QUE ESTA FONTE SERVE. A regra do projeto e que contato so entra de fonte
oficial — contato errado manda o eleitor escrever para um estranho. Estas URLs
foram declaradas pela propria candidatura no registro, e publicadas pelo TSE:
oficiais na origem e autodeclaradas no conteudo. As duas coisas ficam escritas
no campo de fonte, porque sao diferentes.

O CAMPO E TEXTO LIVRE, E ESTA SUJO. Nas 1.232 URLs das candidaturas ao Senado
apareceram um telefone, handles digitados como texto ("INSTAGRAM: @FULANO"),
uma URL malformada ("https://.www.") e enderecos que nao sao URL nenhuma. Nada
disso e descartado em silencio: vai para _conferir_contato, porque publicar um
telefone no lugar de um site e pior do que nao publicar nada.

RECUSAR NAO ERA SUFICIENTE, E RECUSAR DEMAIS TAMBEM ERA ERRO. Duas coisas
apareceram quando esta parte foi medida:

  1. 49 links iam para o ar sem abrir nada. A linha "FACEBOOK: HTTPS://WWW.
     FACEBOOK.COM/RUICOSTAOFICIAL" contem "facebook.com", entao era classificada
     como rede e publicada inteira como href — com o rotulo dentro. O navegador
     tentava abrir "https://FACEBOOK: HTTPS://...". Atingia Jaques Wagner (10
     links), Favaro (9), Rui Costa, Pedro Taques e Veneziano (6 cada), entre
     outros. O conserto foi por ordem: texto com espaco e frase, nao endereco, e
     passa a ser examinado antes de casar com nome de dominio.
  2. 27 candidaturas apareciam como "nao declarou nenhuma rede social nem site".
     Tinham declarado. A recuperacao (ver recuperar()) le a frase e tira dela o
     endereco, quando da para fazer isso sem escolher nada por conta propria.

O TSE CORTA DS_URL EM 80 CARACTERES: 1.899 enderecos da base tem exatamente 80,
contra ~140 em cada comprimento vizinho. Quando o corte cai no rastreio
(?igsh=, ?utm_source=) nao faz falta; quando cai no caminho, o endereco aponta
para um perfil que nao existe. As duas situacoes sao tratadas de forma diferente.

teste-redes.py trava cada uma dessas decisoes, com as linhas reais da base.

PAGINA DE PARTIDO NAO E SITE DA CANDIDATURA. Treze candidaturas do PCO declaram
a mesma URL. Isso e material do partido, que no modelo deste site e o estado B —
outro fato, e nao pode virar "site oficial da candidatura". Vai para
site_do_partido, com quantas candidaturas a compartilham.

O TSE NAO DIVULGA E-MAIL. A coluna DS_EMAIL traz a string "NAO DIVULGAVEL" em
todas as linhas (conferido nas candidaturas a senador de 8 estados). Ausencia da
fonte, nao da nossa busca — e o motivo fica escrito no dado.

CAIXA ALTA. O TSE grava a maioria das URLs em caixa alta, e algumas em caixa
original. Caminho de URL e sensivel a caixa, entao o valor NAO e normalizado:
fica como foi declarado. Normalizar o que ja se perdeu seria inventar.

USO
    python cadastrar_redes.py --uf PE            # mostra o que faria
    python cadastrar_redes.py --uf PE --gravar   # escreve
    python cadastrar_redes.py --todos --gravar   # todos os estados com acervo
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import re
import zipfile
from datetime import date

import acervo

BASE = acervo.RAIZ / "fontes" / "redes-sociais-candidatos-2026.zip"

FONTE = "TSE — Redes sociais de candidatos 2026 (autodeclarado no registro)"

# Sai impresso no bloco de canais de cada candidatura.
MOTIVO_EMAIL = "O TSE não divulga e-mail de candidato: a coluna DS_EMAIL traz \"NÃO DIVULGÁVEL\" em todas as linhas. Ausência da fonte, não da nossa busca."

# Dominios que sao rede social, agregador de links ou hospedagem de midia. Nao
# sao "site da candidatura", que e onde mora programa e proposta.
REDES = (
    "instagram.com", "facebook.com", "fb.com", "youtube.", "youtu.be", "tiktok.com",
    "twitter.com", "x.com", "linkedin.com", "kwai.com", "kwai.app", "threads.com",
    "threads.net", "wa.me", "whatsapp.com", "t.me", "telegram.", "linktr.ee",
    "bio.link", "lnk.bio", "beacons.", "campsite.bio", "spotify.com", "soundcloud.com",
    "flickr.com", "twibbonize.com", "pinterest.", "snapchat.com", "rumble.com",
    # Encontradas ao revisar os 89 que iam ser publicados como "site oficial":
    "bsky.app", "sticker.ly", "cos.tv", "kwai-video.com", "vm.tiktok.com",
    "chat.whatsapp.com", "discord.gg", "twitch.tv", "medium.com", "substack.com",
    "gettr.com", "suamusica.com.br", "gab.com", "parler.com", "vk.com",
)

# Terminacoes de dominio aceitas. Lista explicita, e nao "qualquer coisa depois
# do ponto": a base trouxe "HIPERION.OLIVEIRA" e "MILTONCARDOSO.OFICIAL", que
# nao sao enderecos, e passariam por um teste de ".algo".
TLD = (
    ".com.br", ".org.br", ".net.br", ".gov.br", ".adv.br", ".blog.br", ".eco.br",
    ".com", ".org", ".net", ".info", ".me", ".co", ".io", ".app", ".dev", ".online",
    ".site", ".br", ".rio", ".tv", ".xyz", ".club", ".page", ".link", ".bio",
)

# Rotulo que a pessoa digitou antes do endereco: "SITE: https://...". O endereco
# depois do rotulo e valido, e jogar a linha toda fora perderia um site real.
ROTULO = re.compile(r"^\s*(site|website|p[aá]gina|home\s?page|blog)\s*:\s*", re.I)

REDE_NOME = {
    "instagram": "instagram", "facebook": "facebook", "youtube": "youtube",
    "youtu.be": "youtube", "tiktok": "tiktok", "x.com": "x", "twitter": "x",
    "kwai": "kwai", "threads": "threads", "linkedin": "linkedin",
}


def limpa(u: str) -> str:
    return (u or "").strip()


def chave(u: str) -> str:
    """Forma comparavel: sem esquema, sem www, sem barra final, em minusculas.
    Serve so para DETECTAR repeticao — nunca para gravar."""
    return re.sub(r"^https?://", "", u.lower()).removeprefix("www.").rstrip("/")


def sem_rotulo(u: str) -> str:
    """Tira "SITE: " da frente. Dois senadores declararam assim, e o endereco
    depois do rotulo e legitimo."""
    return ROTULO.sub("", limpa(u)).strip()


def especie(u: str) -> str:
    """Classifica a URL declarada. O campo e texto livre e recebe de tudo:
    telefone, e-mail, handle digitado a mao, rotulo, placeholder de modelo."""
    b = sem_rotulo(u).lower()
    if not b:
        return "vazio"
    if re.fullmatch(r"\+?[\d\s()\-.]{8,}", b):
        return "telefone"
    # E-mail vira "site oficial" e manda o eleitor escrever para um endereco que
    # nunca foi anunciado como canal. Quatro apareceram nas 1.232.
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", b):
        return "email_no_campo_de_url"
    if re.fullmatch(r"[a-z\s]+:\s*@?[\w.\-]+", b):
        return "handle_como_texto"
    # Comeca com @: e handle, nunca endereco. "@MAIRADESOUZA.UP" passava pelo
    # teste de dominio porque ".UP" parece TLD — e teria virado "site oficial".
    if b.startswith("@"):
        return "handle_como_texto"
    if re.search(r"https?://\.", b) or b.count("://") > 1:
        return "malformada"
    # TEXTO LIVRE ANTES DE REDE. Estava depois, e por isso "X/TWITTER:
    # X.COM/JAQUESWAGNER KWAI: KWAI.COM/@... YOUTUBE: YOUTU" virava "rede" — a
    # linha inteira contem "x.com" — e ia para o site como UM link, que nao abre
    # nada. Endereco nao tem espaco no meio; se tem, e frase, e frase vai para a
    # recuperacao, que sabe achar os enderecos dentro dela.
    corpo = re.sub(r"^https?://", "", b)
    if len(corpo.split()) > 1:
        return "texto_livre"
    if any(d in b for d in REDES):
        return "rede"
    dominio = corpo.split("/")[0].rstrip(".")
    if not any(dominio.endswith(t) for t in TLD):
        return "dominio_improvavel"
    # Placeholder de modelo que o partido nao preencheu.
    if re.search(r"nome-de-urna|seu-nome|nomecandidato|exemplo", b):
        return "placeholder_do_partido"
    return "site"


# ---------------------------------------------------------------- recuperacao
# 27 candidaturas apareciam no site como "nao declarou nenhuma rede social nem
# site no registro no TSE". Elas declararam: escreveram "INSTAGRAM: @FULANO" num
# campo que espera URL, e o classificador recusou. A frase publicada era falsa
# sobre 27 pessoas reais.
#
# O QUE ENTRA: so o que tem PLATAFORMA NOMEADA e HANDLE SEM ESPACO. "INSTAGRAM:
# @ALCIDESFERNANDES" tem os dois. "FACEBOOK: ALCIDES FERNANDES" tem um nome com
# espaco, que nao e handle — fica de fora. "@REGISETHUR" sozinho nao diz a rede,
# e a base do TSE nao tem coluna de plataforma para desempatar — fica de fora.
#
# O QUE NUNCA ENTRA: e-mail, telefone e endereco de rua. A pessoa errou o campo,
# e republicar o dado pessoal dela por causa do erro seria decisao nossa, nao
# dela.
PERFIL = {
    "instagram": "https://www.instagram.com/{h}",
    "facebook": "https://www.facebook.com/{h}",
    "threads": "https://www.threads.net/@{h}",
    "tiktok": "https://www.tiktok.com/@{h}",
    "x": "https://x.com/{h}",
    "youtube": "https://www.youtube.com/@{h}",
    "linkedin": "https://www.linkedin.com/in/{h}",
    "kwai": "https://www.kwai.com/@{h}",
}
# Como as pessoas digitaram de verdade, erros de grafia inclusive.
APELIDO_REDE = {
    "instagram": "instagram", "instagran": "instagram", "insta": "instagram",
    "facebook": "facebook", "face": "facebook", "fb": "facebook",
    "threads": "threads",
    "tiktok": "tiktok", "tik tok": "tiktok",
    "x": "x", "twitter": "x", "twiter": "x",
    "youtube": "youtube",
    "linkedin": "linkedin",
    "kwai": "kwai",
}
HANDLE_OK = re.compile(r"^[A-Za-z0-9._\-]{2,40}$")
RUIDO = {"https", "http", "e", "-", "oficial", "rede", "social", "perfil"}
# Palavras que a pessoa escreveu DEPOIS de um endereco para explicar o que ele e.
# Servem de prova de que o espaco ali separava mesmo dois campos.
ROTULO_DEPOIS = {"fanpage", "pagina", "página", "canal", "site", "twitter", "telegram",
                 "whatsapp", "spotify", "flickr", "linktree", "bluesky", "bsky"}

# O TSE CORTA DS_URL EM 80 CARACTERES. Medido na base: 1.899 enderecos tem
# exatamente 80, contra ~140 em cada comprimento vizinho. O corte cai quase
# sempre no rastreio (?igsh=, ?utm_source=), que nao faz falta — mas quando cai
# no caminho, o endereco aponta para lugar nenhum.
CORTE_TSE = 80

# Parametros que as redes grudam no endereco quando alguem usa "compartilhar".
# Nao identificam o perfil, envelhecem, e sao o pedaco que o corte do TSE come.
RASTREIO = re.compile(
    r"^(utm_\w+|igs\w*|si|xmt|s|t|rdid|share_url|hr|wtsid|fbclid|gclid|mibextid)$", re.I)

# Endereco escrito sem http://. So com TLD conhecido: sem a lista, "MILTONCARDOSO
# .OFICIAL" e "MARIANACARVALHO.RO" virariam dominios, e nao sao.
SEM_ESQUEMA = re.compile(
    r"(?:^|[\s:*])((?:www\.)?[a-z0-9][a-z0-9-]{0,60}"
    r"\.(?:com\.br|org\.br|net\.br|com|net|org|br|me|app|nz|ee|tv)"
    r"(?:/[^\s*]*)?)", re.I)


def arruma_esquema(u: str) -> str:
    """Esquema digitado errado, letra por letra: "TTPS://K.KWAI.COM/..." perdeu o
    H e "HTTPS:WWW.TIKTOK.COM/..." perdeu as duas barras. Os dois iam para o site
    como href e o navegador nao abre nenhum deles."""
    u = re.sub(r"^(t)(tps?://)", lambda m: ("H" if m.group(1).isupper() else "h") + m.group(0),
               u, flags=re.I)
    return re.sub(r"^(https?):(?!//)", r"\1://", u, flags=re.I)


def sem_rastreio(u: str) -> str:
    """Tira so o rastreio da query. Mantem tudo o que identifica a pagina."""
    if "?" not in u:
        return u
    base, _, query = u.partition("?")
    fica = [p for p in query.split("&") if p and not RASTREIO.match(p.split("=")[0])]
    return base + ("?" + "&".join(fica) if fica else "")


def _tokens(b: str) -> list[str]:
    b = re.sub(r"tik\s+tok", "tiktok", b, flags=re.I)
    brutos = (t.strip("@:/.,-*()[] ") for t in re.split(r"[\s:/,*()\[\]]+", b))
    return [t for t in brutos if t and t.lower() not in RUIDO]


def recuperar(u: str, cortada: bool = False) -> tuple[list[str], str]:
    """Devolve (urls, motivo). Lista vazia significa que nao deu para recuperar
    sem inventar, e o motivo diz por que — que e o que vai para a tela.

    `cortada` avisa que a linha bateu no limite de 80 do TSE, e portanto o ultimo
    pedaco dela pode estar pela metade."""
    b = limpa(u)
    if not b:
        return [], "campo vazio no registro"
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", b) and "instagram.com/" not in b.lower():
        return [], "e-mail no campo de rede social: dado pessoal que não republicamos"
    # Telefone digitado com ou sem rotulo ("TELEGRAM 8198377-0777"). Conta digitos
    # fora de URL: handle costuma ter um ou dois, telefone tem oito ou mais.
    if "http" not in b.lower() and len(re.findall(r"\d", b)) >= 8:
        return [], "telefone no campo de rede social: dado pessoal que não republicamos"
    if re.search(r"nome-de-urna|seu-nome|nomecandidato|exemplo", b, re.I):
        return [], "modelo do partido que ficou sem preencher"

    # 1) Endereco quase certo: sobra de digitacao em volta de uma URL boa.
    #    "https://.www.X" tem um ponto a mais; "URL#URL" e "URL - URL" sao a
    #    mesma URL repetida; "* URL * FACEBOOK: https://" tem uma URL e um resto.
    def _limpa(cru: str) -> str:
        cru = re.sub(r"^(https?://)\.+", r"\1", cru, flags=re.I).rstrip(".,-/")
        # Linha cortada perde a query INTEIRA, e nao so os parametros que eu
        # conheco: o ultimo parametro de uma linha de 80 esta pela metade, e um
        # parametro pela metade e lixo do mesmo jeito que o inteiro.
        return cru.split("?")[0] if cortada else sem_rastreio(cru)

    # Esquema digitado errado, letra por letra: "TTPS://K.KWAI.COM/..." perdeu o
    # H, "HTTPS:WWW.TIKTOK.COM/..." perdeu as duas barras. Os dois estavam indo
    # para o site como href, e o navegador nao abre nenhum dos dois.
    b = re.sub(r"(?<![a-z])(t)(tps?://)",
               lambda m: ("H" if m.group(1).isupper() else "h") + m.group(0), b, flags=re.I)
    b = re.sub(r"(https?):(?!//)", r"\1://", b, flags=re.I)

    achados = [(m.group(0), m.end()) for m in re.finditer(r"https?://[^\s*#]+", b, re.I)]
    # E TAMBEM os enderecos sem http:// na frente, na MESMA linha. Uma linha
    # so do Jaques Wagner tem "YOUTUBE: YOUTUBE.COM/@... FLICKR: HTTPS://..." —
    # se o sem-esquema so valesse quando nao ha nenhum http, o YouTube dele
    # sumiria por causa do Flickr que veio depois. Apago o que ja foi achado
    # antes de varrer, para nao pegar o mesmo endereco duas vezes.
    resto_b = b
    for u, fim in achados:
        resto_b = resto_b[:fim - len(u)] + " " * len(u) + resto_b[fim:]
    achados += [("https://" + m.group(1), m.end()) for m in SEM_ESQUEMA.finditer(resto_b)]
    achados.sort(key=lambda x: x[1])

    # ESPACO DENTRO DO ENDERECO PARECE FIM DE ENDERECO. Duas candidaturas
    # digitaram um espaco no meio do proprio link: "OPEN.SPOTIFY.COM/SHO
    # W/64IDJ..." e "WWW.FACEBOOK.COM/ ANDREMOURASE". Cortar ali produz
    # "spotify.com/SHO" e "facebook.com/" — enderecos que PARECEM bons e levam a
    # lugar nenhum, que e pior do que o texto quebrado que estava la antes.
    #
    # O que separa os dois casos e a palavra seguinte: quando e nome de rede ou
    # rotulo ("INSTAGRAM", "FANPAGE"), o espaco separa mesmo dois enderecos;
    # quando e qualquer outra coisa, o espaco caiu dentro de um endereco so.
    def _corte_confiavel(fim: int) -> bool:
        depois = b[fim:].lstrip(" \t*-—#|,.")
        if not depois:
            return True
        prox = re.split(r"[\s:/,*]+", depois)[0].strip("@:/.,-*()[] ").lower()
        return (not prox or prox in APELIDO_REDE or prox in RUIDO
                or prox in ROTULO_DEPOIS or depois.lower().startswith(("http", "www.")))

    achados = [(u, fim) for u, fim in achados if _corte_confiavel(fim)]
    # O QUE ENCOSTA NO FIM DE UMA LINHA CORTADA NAO ENTRA. Uma candidatura do
    # Piaui declarou o mesmo Instagram duas vezes e o corte comeu o fim do
    # segundo: ".../ANTONIOBARROSAF" e ".../ANTONIOBA". Os dois passariam como
    # enderecos validos, e o segundo levaria o eleitor a um perfil inexistente.
    # A regra e por POSICAO, e nao "o ultimo": na linha do Jaques Wagner o que
    # ficou pela metade foi um "YOUTU" solto depois do ultimo endereco inteiro,
    # e descartar o ultimo endereco jogaria fora um link bom.
    # Encostar no fim so condena o endereco se o corte caiu no CAMINHO. Se caiu
    # dentro da query — ".../mauromendesoficial?igsh=MTU0" —, o perfil esta
    # inteiro e so o rastreio ficou pela metade: joga fora a query, guarda o
    # endereco. Descartar tudo aqui perderia um link que funciona.
    achadas = [_limpa(u) for u, fim in achados
               if "?" in u or not (cortada and fim == len(b))]
    achadas = [u for u in achadas if re.match(r"^https?://[^/]+\.[a-z]{2,}", u, re.I)]
    # Endereco que e comeco de outro e o mesmo endereco cortado.
    achadas = [x for x in achadas
               if not any(y != x and chave(y).startswith(chave(x)) for y in achadas)]
    vistas, unicas = set(), []
    for x in achadas:
        if chave(x) not in vistas:
            vistas.add(chave(x)); unicas.append(x)
    if unicas:
        return unicas, "endereço recuperado do texto declarado"

    # 2) Plataforma nomeada + handle, cada um como palavra inteira. Palavra
    #    inteira importa: "THREADS_EITUVIU" e um token so, e nao da para saber se
    #    a rede e Threads com handle "eituviu" ou se o handle inteiro se chama
    #    assim. Fica de fora.
    toks = _tokens(b)
    redes = [APELIDO_REDE[t.lower()] for t in toks if t.lower() in APELIDO_REDE]
    resto = [t for t in toks if t.lower() not in APELIDO_REDE]
    if not redes:
        return [], "handle declarado sem dizer a rede, e a base do TSE não guarda a plataforma"
    handles = [t for t in resto if HANDLE_OK.match(t)]
    if len(resto) != 1 or len(handles) != 1:
        # Sobra palavra ("ALCIDES FERNANDES") ou ha mais de um candidato a
        # handle: escolher qual seria palpite nosso.
        return [], "não dá para separar a rede do handle sem escolher por conta própria"
    h = handles[0].lower()
    return [PERFIL[r].format(h=h) for r in dict.fromkeys(redes) if r in PERFIL], \
           "handle declarado como texto, com a rede nomeada ao lado"


def qual_rede(u: str) -> str | None:
    b = limpa(u).lower()
    for pedaco, nome in REDE_NOME.items():
        if pedaco in b:
            return nome
    return None


def handle(u: str) -> str | None:
    """Extrai @handle de uma URL de rede. So do caminho, e so se parecer handle."""
    m = re.search(r"(?:instagram\.com|threads\.(?:com|net))/@?([A-Za-z0-9._]{2,40})", u, re.I)
    return "@" + m.group(1).lower() if m else None


def urls_do_tse() -> dict[str, list[str]]:
    if not BASE.exists():
        raise SystemExit(f"nao achei {BASE}. Baixe a base de redes sociais do TSE antes.")
    fora: dict[str, list[str]] = collections.defaultdict(list)
    with zipfile.ZipFile(BASE) as z:
        nome = [n for n in z.namelist() if n.endswith("BRASIL.csv")][0]
        with z.open(nome) as fh:
            for l in csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"), delimiter=";"):
                u = limpa(l["DS_URL"])
                if u:
                    fora[str(l["SQ_CANDIDATO"])].append(u)
    return fora


def sequenciais(c: dict) -> list[str]:
    """Registro duplicado do TSE tem mais de um sequencial, e as URLs podem estar
    em qualquer um deles."""
    return [str(s) for s in ([c.get("sequencial_tse")] + (c.get("_sequenciais_duplicados") or []))
            if s]


def montar(uf: str, por_seq: dict[str, list[str]], uso: collections.Counter) -> tuple[list, dict]:
    cands = acervo.ler("candidaturas.json", uf)["candidaturas"]
    resumo = collections.Counter()
    for c in cands:
        brutas = []
        for s in sequenciais(c):
            brutas += por_seq.get(s, [])
        # a mesma URL aparece repetida com e sem barra final; uma vez basta
        vistas, urls = set(), []
        for u in brutas:
            if chave(u) in vistas:
                continue
            vistas.add(chave(u)); urls.append(u)

        contato = dict(c.get("contato") or {})
        problemas, recuperados = [], []
        sites, redes, compartilhadas = [], [], []
        for u in sorted(urls, key=lambda x: x.lower()):
            e = especie(u)
            if e == "site":
                # grava sem o rotulo "SITE: ", que nao faz parte do endereco
                lim = sem_rastreio(arruma_esquema(sem_rotulo(u)))
                (compartilhadas if uso[chave(lim)] > 1 else sites).append(lim)
            elif e == "rede":
                redes.append(sem_rastreio(arruma_esquema(u)))
            else:
                # SEGUNDA PASSADA. O que o classificador recusa nao e
                # necessariamente lixo: na maioria das vezes e um endereco bom
                # com sujeira em volta, ou um handle com a rede escrita ao lado.
                achadas, motivo = recuperar(u, cortada=len(limpa(u)) == CORTE_TSE)
                if achadas:
                    redes += achadas
                    recuperados.append(f'"{u}" — {motivo}: {", ".join(achadas)}')
                else:
                    problemas.append(f'"{u}" — {motivo}')

        if urls:
            contato["redes"] = redes + sites + compartilhadas
            contato["redes_fonte"] = FONTE
            contato["redes_consultado_em"] = date.today().isoformat()
            resumo["com alguma URL"] += 1
        else:
            resumo["sem URL declarada"] += 1

        # SITE da candidatura: so o que nao e de mais ninguem.
        #
        # ESCOLHA HUMANA NAO SE PERDE. Quem tem mais de um site declarado ja pode
        # ter tido o principal escolhido a mao — Simone Tebet declarou
        # simone400.com.br e simonetebet.com.br, e a curadoria escolheu o segundo.
        # Ordem alfabetica trocaria por outro, desfazendo a decisao em silencio.
        if sites:
            ja = contato.get("site")
            escolhido = ja if ja and chave(ja) in {chave(s) for s in sites} else sites[0]
            contato["site"] = escolhido
            contato["site_fonte"] = FONTE
            outros = [s for s in sites if chave(s) != chave(escolhido)]
            if outros:
                contato["outros_sites"] = outros
            else:
                contato.pop("outros_sites", None)
            resumo["com site proprio"] += 1
        # Site herdado que na verdade e pagina de partido tem de sair. Preservar
        # escolha humana nao pode virar preservar erro humano: uma candidatura do
        # PCO tinha a pagina do partido gravada a mao como "site" dela.
        herdado = contato.get("site")
        if herdado and uso[chave(herdado)] > 1:
            contato.pop("site", None)
            contato.pop("site_fonte", None)
            if chave(herdado) not in {chave(x) for x in compartilhadas}:
                compartilhadas.insert(0, herdado)
            resumo["site herdado era do partido"] += 1

        if compartilhadas:
            # Pagina de partido: outro fato, e o estado B do modelo.
            contato["site_do_partido"] = compartilhadas[0]
            contato["site_do_partido_nota"] = (
                f"URL declarada por {uso[chave(compartilhadas[0])]} candidaturas: e material "
                f"do partido, nao da candidatura.")
            resumo["com pagina de partido"] += 1

        # instagram, que a ficha de Sao Paulo ja mostra. Tambem nao sobrescreve
        # o que ja estava escolhido.
        if not contato.get("instagram"):
            for u in redes:
                if qual_rede(u) == "instagram" and handle(u):
                    contato["instagram"] = handle(u)
                    contato["instagram_fonte"] = FONTE
                    break

        contato.setdefault("email", None)
        contato.setdefault("email_fonte", None)
        contato.setdefault("email_tipo", None)
        if not contato.get("email"):
            contato["_email_indisponivel"] = MOTIVO_EMAIL

        # AUSENCIA DE CONTATO TEM DOIS TIPOS, e junta-los seria o mesmo erro que
        # o site combate nos temas. "Nao declarou" e um fato sobre a candidatura;
        # "declarou e nada serve" e um fato sobre o registro, e e recuperavel —
        # a maioria e handle de Instagram digitado como texto.
        if contato.get("redes"):
            c.pop("_contato_ausente", None)
        elif problemas:
            c["_contato_ausente"] = (
                f"A candidatura declarou {len(problemas)} endereço(s) ao TSE e nenhum é "
                f"utilizável como canal: ver _conferir_contato. Não é ausência de "
                f"declaração, é declaração que não dá contato.")
        else:
            c["_contato_ausente"] = (
                "A candidatura não declarou nenhuma URL na base de redes sociais do TSE, "
                "e o TSE não divulga e-mail. Ausência da fonte, não da nossa busca.")

        c["contato"] = contato
        if problemas:
            c["_conferir_contato"] = problemas
            resumo["com lixo no campo"] += 1
        else:
            c.pop("_conferir_contato", None)
        # O que foi recuperado fica escrito, com a linha crua ao lado. Endereco
        # que a maquina montou a partir de texto tem de poder ser desfeito por
        # quem revisa, e para desfazer e preciso ver de onde veio.
        if recuperados:
            c["_contato_recuperado"] = recuperados
            resumo["com endereco recuperado"] += 1
        else:
            c.pop("_contato_recuperado", None)
    return cands, resumo


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()
    if not a.uf and not a.todos:
        raise SystemExit("passe --uf XX ou --todos")

    ufs = acervo.com_acervo() if a.todos else [a.uf.upper()]
    por_seq = urls_do_tse()

    # Uma URL usada por mais de uma CANDIDATURA e do partido, nao da pessoa.
    # Contado sobre todas as candidaturas ao Senado, nao dentro do estado: o
    # PCO repete a mesma pagina em 13 estados diferentes.
    uso: collections.Counter = collections.Counter()
    for u in ufs:
        for c in acervo.ler("candidaturas.json", u)["candidaturas"]:
            vistas = set()
            for s in sequenciais(c):
                for x in por_seq.get(s, []):
                    if especie(x) == "site" and chave(sem_rotulo(x)) not in vistas:
                        vistas.add(chave(sem_rotulo(x)))
            for k in vistas:
                uso[k] += 1

    geral: collections.Counter = collections.Counter()
    for uf in ufs:
        cands, resumo = montar(uf, por_seq, uso)
        geral.update(resumo)
        n = acervo.estado(uf)["nome"]
        print(f"{n} ({uf}) — {len(cands)} candidaturas")
        for k in ("com site proprio", "com pagina de partido", "com alguma URL",
                  "sem URL declarada", "com endereco recuperado", "com lixo no campo"):
            if resumo.get(k):
                print(f"    {resumo[k]:3}  {k}")
        if a.gravar:
            f = acervo.de(uf) / "candidaturas.json"
            d = json.loads(f.read_text(encoding="utf-8"))
            d["candidaturas"] = cands
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if len(ufs) > 1:
        print()
        print(f"TOTAL em {len(ufs)} estados:")
        for k, v in geral.most_common():
            print(f"    {v:4}  {k}")
    if not a.gravar:
        print()
        print("(sem --gravar: nada foi escrito)")


if __name__ == "__main__":
    main()
