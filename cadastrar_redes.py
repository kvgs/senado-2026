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

MOTIVO_EMAIL = ("O TSE nao divulga e-mail de candidato: a coluna DS_EMAIL traz "
                "\"NAO DIVULGAVEL\" em todas as linhas. Ausencia da fonte, nao da "
                "nossa busca.")

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
    if any(d in b for d in REDES):
        return "rede"
    # Texto livre com varias palavras nao e endereco: uma candidatura declarou
    # dois e-mails e um site na mesma linha, separados por " - ".
    corpo = re.sub(r"^https?://", "", b)
    if len(corpo.split()) > 1:
        return "texto_livre"
    dominio = corpo.split("/")[0].rstrip(".")
    if not any(dominio.endswith(t) for t in TLD):
        return "dominio_improvavel"
    # Placeholder de modelo que o partido nao preencheu.
    if re.search(r"nome-de-urna|seu-nome|nomecandidato|exemplo", b):
        return "placeholder_do_partido"
    return "site"


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
        problemas = []
        sites, redes, compartilhadas = [], [], []
        for u in sorted(urls, key=lambda x: x.lower()):
            e = especie(u)
            if e == "site":
                # grava sem o rotulo "SITE: ", que nao faz parte do endereco
                lim = sem_rotulo(u)
                (compartilhadas if uso[chave(lim)] > 1 else sites).append(lim)
            elif e == "rede":
                redes.append(u)
            else:
                problemas.append(f'"{u}" — {e.replace("_", " ")}, nao entra como contato')

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

        c["contato"] = contato
        c.pop("_contato_ausente", None)
        if problemas:
            c["_conferir_contato"] = problemas
            resumo["com lixo no campo"] += 1
        else:
            c.pop("_conferir_contato", None)
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
                  "sem URL declarada", "com lixo no campo"):
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
