# -*- coding: utf-8 -*-
"""Acha e corrige resumo nosso escrito sem acento, e serve de porteiro.

POR QUE ISTO EXISTE. O campo `texto` de cada posicao e resumo NOSSO, e vai para a
tela do site. Ele foi escrito sem acento quatro vezes neste projeto — 783 resumos,
2.415 ressalvas, 611 avisos de ausencia, e agora 82 resumos. Nao e falta de saber:
e o que acontece quando texto em portugues passa por script. Saber do defeito nao
impediu de comete-lo; so impediu de publica-lo. Entao o defeito passa a ter
detector.

O DICIONARIO SAI DO PROPRIO ACERVO, E NAO DE MIM. Para cada palavra, olho como ela
aparece nas CITACOES LITERAIS — que vem da fonte e por isso estao acentuadas como
a fonte escreveu. Se uma palavra aparece na fonte SEMPRE com acento e nunca sem,
entao a forma sem acento num resumo nosso e erro de digitacao, e a correcao e a
forma da fonte. Isso e importante: eu nao estou decidindo a grafia, estou copiando
a que a fonte usa.

A REGRA SE PROTEGE SOZINHA NOS CASOS AMBIGUOS. "esta" e "está" sao duas palavras
diferentes, e "para" e "Pará" tambem. Como a forma sem acento aparece nas citacoes
(muito), essas palavras nunca entram no dicionario. O mesmo vale para "e/é" e
"so/só". O que sobra e palavra que em portugues so existe acentuada.

USO
    python arrumar_acentos.py                 # mostra o que faria
    python arrumar_acentos.py --gravar
    python arrumar_acentos.py --conferir      # sai com erro se achar algo: porteiro
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys
import unicodedata

PALAVRA = re.compile(r"[A-Za-zÀ-ÿ]{3,}")

# SEGUNDO DEGRAU, e por que ele precisa existir. O dicionario tirado das citacoes e
# conservador de proposito: palavra que a fonte tambem escreve sem acento fica fora.
# Isso protege "esta/está", "para/Pará" e "so/só" — e, sem querer, deixou passar
# "nao" e "publico", que aparecem sem acento em 21 citacoes da era SP. Como essas
# citacoes eram elas mesmas o defeito, o dicionario aprendeu o erro.
#
# A lista abaixo e conhecimento de portugues, e nao leitura do acervo: sao palavras
# que NAO TEM forma sem acento na lingua. Nenhuma delas e homografa de outra
# palavra — e esse e o unico critetio para entrar aqui. "esta", "para", "as", "e" e
# "so" jamais entram, porque para essas a forma nua tambem existe e significa
# outra coisa.
SEMPRE_ACENTUADA = {
    "nao": "não", "tambem": "também", "atraves": "através",
    "orgao": "órgão", "orgaos": "órgãos", "questao": "questão",
    "publico": "público", "publica": "pública",
    "publicos": "públicos", "publicas": "públicas",
    "saude": "saúde", "educacao": "educação", "seguranca": "segurança",
    "regiao": "região", "regioes": "regiões", "reducao": "redução",
    "servico": "serviço", "servicos": "serviços",
    "criterio": "critério", "criterios": "critérios",
    "proprio": "próprio", "propria": "própria",
    "proprios": "próprios", "proprias": "próprias",
    "capitulo": "capítulo", "familia": "família", "familias": "famílias",
    "eleicao": "eleição", "eleicoes": "eleições",
    "indenizacao": "indenização", "especulacao": "especulação",
    "estatizacao": "estatização", "opressoes": "opressões",
    "basica": "básica", "basico": "básico", "medio": "médio",
}

# HOMOGRAFOS QUE SO O ACENTO SEPARA, e que por isso NUNCA podem ser trocados por
# script — nem pelo dicionario tirado das citacoes, que aprende a forma mais
# frequente e depois a aplica na errada.
#
# O caso que obrigou esta lista: o acervo dizia "o documento critica a tarifa zero"
# — verbo, correto sem acento. As citacoes usam muito "crítica" (substantivo), o
# dicionario aprendeu "critica -> crítica" e ia reescrever o verbo como
# substantivo. A troca seria de acento, mas a mudanca seria de classe gramatical.
#
# Cada par abaixo e verbo (sem acento) contra substantivo ou adjetivo (com acento):
# ele critica / a crítica · ele pratica / a prática · o site publica / rede pública
# ele media / a média · ele duvida / a dúvida · ele fabrica / a fábrica
# ele secretaria / a secretária · que ele analise / a análise · ele valida / válida
# ele intima / íntima · ele policia / a polícia · ele especifica / específica
HOMOGRAFOS = {
    "critica", "criticas", "pratica", "praticas", "publica", "media", "duvida",
    "fabrica", "secretaria", "analise", "valida", "intima", "policia", "especifica",
    "continua", "domestica",
}
# Campos que sao TEXTO NOSSO. citacao_literal nao entra: la a grafia e da fonte, e
# mexer nela seria falsificar a citacao.
CAMPOS = ["texto"]
MINIMO_NA_FONTE = 2      # a forma acentuada tem de aparecer ao menos 2x na fonte


def sem_acento(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()


def dicionario_da_fonte() -> dict[str, str]:
    """Palavras que as citacoes literais escrevem SEMPRE com acento."""
    formas: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for f in glob.glob("dados/*/posicoes.json"):
        for p in json.load(open(f, encoding="utf-8"))["posicoes"]:
            for w in PALAVRA.findall(p.get("citacao_literal") or ""):
                formas[sem_acento(w).lower()][w.lower()] += 1
    saida = {}
    for nua, cont in formas.items():
        if nua in cont:
            continue                       # a fonte tambem escreve sem acento
        forma, n = cont.most_common(1)[0]
        if forma != nua and n >= MINIMO_NA_FONTE and nua not in HOMOGRAFOS:
            saida[nua] = forma
    return saida


def com_caixa(molde: str, alvo: str) -> str:
    """Devolve `alvo` com a caixa de `molde`: NAO -> NÃO, Nao -> Não."""
    if molde.isupper():
        return alvo.upper()
    if molde[:1].isupper():
        return alvo[:1].upper() + alvo[1:]
    return alvo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gravar", action="store_true")
    ap.add_argument("--conferir", action="store_true",
                    help="sai com codigo 1 se achar resumo sem acento")
    a = ap.parse_args()

    dic = dicionario_da_fonte()
    n_fonte = len(dic)
    dic.update(SEMPRE_ACENTUADA)      # a lista da lingua manda sobre a do acervo
    for h in HOMOGRAFOS:              # nem uma nem outra troca homografo
        dic.pop(h, None)
    print(f"dicionario: {n_fonte} palavras tiradas das citacoes da fonte + "
          f"{len(SEMPRE_ACENTUADA)} que nao existem sem acento em portugues\n")

    trocas: collections.Counter = collections.Counter()
    afetadas, por_uf = [], collections.Counter()
    for f in sorted(glob.glob("dados/*/posicoes.json")):
        uf = os.path.basename(os.path.dirname(f))
        d = json.load(open(f, encoding="utf-8"))
        mudou = False
        for p in d["posicoes"]:
            for campo in CAMPOS:
                v = p.get(campo)
                if not v:
                    continue
                def troca(m: re.Match) -> str:
                    w = m.group(0)
                    certa = dic.get(w.lower())
                    if not certa:
                        return w
                    trocas[f"{w.lower()} -> {certa}"] += 1
                    return com_caixa(w, certa)
                novo = PALAVRA.sub(troca, v)
                if novo != v:
                    afetadas.append((uf, p["id_posicao"], v, novo))
                    por_uf[uf] += 1
                    p[campo] = novo
                    mudou = True
        if mudou and a.gravar:
            with open(f, "w", encoding="utf-8") as fh:
                json.dump(d, fh, ensure_ascii=False, indent=1)
                fh.write("\n")

    print(f"{len(afetadas)} resumo(s) com palavra sem acento, "
          f"em {len(por_uf)} estado(s): {dict(por_uf)}\n")
    print("TROCAS, uma linha por palavra distinta (confira antes de gravar):")
    for k, n in sorted(trocas.items()):
        print(f"  {n:4}x  {k}")
    print("\nEXEMPLOS:")
    for uf, idp, antes, depois in afetadas[:8]:
        print(f"  [{uf}] {idp}")
        print(f"     antes:  {antes[:120]}")
        print(f"     depois: {depois[:120]}")

    if a.conferir:
        if afetadas:
            print(f"\nPORTEIRO: {len(afetadas)} resumo(s) sem acento. "
                  "Rode com --gravar.")
            return 1
        print("\nPORTEIRO: nenhum resumo sem acento.")
        return 0
    if a.gravar:
        print(f"\ngravado: {len(afetadas)} resumo(s) corrigido(s)")
    else:
        print("\n(sem --gravar: nada escrito)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
