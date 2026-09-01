# -*- coding: utf-8 -*-
"""Confere se cada citacao_literal do acervo esta MESMO literal na fonte.

POR QUE ISTO E A PROMESSA CENTRAL DO SITE. O template mostra esse campo dentro de
aspas curvas, num blockquote (_template_site.html, "h+='<blockquote>“'+..."). Aspas
dizem ao leitor: estas sao as palavras da pessoa. Se o que esta ali e sintese
nossa, o site afirma algo falso sobre a coisa mais importante que ele publica — e
afirma com a cara de quem conferiu.

E O MODO DE FALHAR QUE O PROJETO JA CONHECE. Esta escrito no coletar_sites.py:
"O MODO DE FALHAR E OUTRO: PARAFRASE. Foi assim que 'controle estatal dos precos'
virou 'congelamento de precos' numa revisao — outra politica, mesma frase
aproximada." Saber do defeito nao impediu de comete-lo: 29 posicoes da era SP
tem sintese no campo da citacao.

COMO O ARQUIVO DA FONTE E ENCONTRADO, sem tabela escrita a mao:
  - programa de partido -> extracoes/partido-<id>.json, campo texto_extraido
  - site de candidatura -> dados/<uf>/_coleta_sites.json, texto das paginas
  - documento com arquivo local -> campos arquivo_local / extracao_local
  - o resto -> NAO CONFERIVEL, e sai dito como tal. Fonte que nao guardamos nao
    pode ser conferida por script, e chamar isso de "ok" seria pior que nao olhar.

COMO A COMPARACAO E FEITA. Quatro niveis, do mais exigente ao menos:
  1. igual ao caractere    — a citacao existe no texto tal e qual
  2. difere so por espaco  — o .txt da fonte quebra a linha no meio da frase e o
                             PDF parte a palavra ("compro- misso"). Isto TAMBEM e
                             literal: nao ha diferenca de conteudo.
  3. transcrito sem acento — casa ignorando acento e caixa. A citacao esta certa,
                             a grafia nao. Corrigivel copiando a fonte.
  4. nao literal           — nem assim casa. O campo tem sintese, nao citacao.
Para o nivel 4 o script mede que fracao da citacao existe na fonte, em palavras
seguidas, para separar "quase tudo, faltou um pedaco" de "frase composta".

O QUE ELE NAO FAZ. Nao reescreve citacao. Corrigir citacao e curadoria: exige ler
a fonte e escolher o trecho, e trecho escolhido de forma que distorce pode ser
perfeitamente literal. Script nao decide isso.

USO
    python conferir_citacoes.py
    python conferir_citacoes.py --uf SP --detalhe
    python conferir_citacoes.py --porteiro     # sai com 1 se achar nao_literal
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import pathlib
import re
import sys
import unicodedata
from datetime import date

HOJE = date.today().isoformat()

RAIZ = pathlib.Path(__file__).resolve().parent

# Documentos da era SP, com id fora do padrao doc-programa-nacional-<sigla>.
ALIAS = {
    "doc-programa-pstu-tse": "pstu",
    "doc-programa-up-tse": "up",
    "doc-programa-pcb-tse": "pcb",
    "doc-programa-pcb": "pcb",
    "doc-programa-missao-tse": "missao",
    "doc-programa-missao": "missao",
}


# TRES NORMALIZACOES, porque as diferencas nao sao todas do mesmo tipo:
#
#   esp()  colapsa espaco e desfaz hifenizacao de fim de linha. Isto NAO e
#          diferenca de conteudo: o .txt da fonte quebra a linha no meio da frase
#          e o PDF parte a palavra ("compro- misso"). Citacao que casa aqui esta
#          literal. Confundir isso com erro fez o primeiro relatorio deste script
#          dizer "1020 transcritas sem acento" — eram quebras de linha.
#   nu()   tira tambem acento e caixa. Casar SO aqui significa transcricao sem
#          acento: a citacao esta certa, a grafia nao.
#   nada   se nem em nu() casa, o campo nao tem citacao: tem sintese.
def esp(s: str) -> str:
    s = re.sub(r"-\s*\n\s*", "", s or "")
    return re.sub(r"\s+", " ", s).strip()


def nu(s: str) -> str:
    s = unicodedata.normalize("NFD", esp(s)).encode("ascii", "ignore").decode().lower()
    # Colapsar o espaco DEPOIS de tirar o que nao e ASCII, e nao antes. O
    # travessao "–" nao e ASCII e desaparece aqui: "pragmatismo – nao" ficava com
    # dois espacos, enquanto o mapa de indices deixava um, e a citacao com
    # travessao nao era localizada na fonte.
    return re.sub(r"\s+", " ", re.sub(r"-\s+", "", s)).strip()


def fontes_de_partido() -> dict[str, str]:
    """id_documento de programa -> texto da fonte, via extracoes/partido-*.json."""
    saida = {}
    for f in glob.glob(str(RAIZ / "extracoes" / "partido-*.json")):
        d = json.load(open(f, encoding="utf-8"))
        cam = d.get("texto_extraido")
        if not cam:
            continue
        p = RAIZ / cam
        if not p.exists():
            continue
        sigla = os.path.basename(f)[len("partido-"):-len(".json")]
        saida[sigla] = p.read_text(encoding="utf-8")
    return saida


def texto_de_site(uf: str) -> dict[str, str]:
    """id_candidatura -> texto coletado do site, de _coleta_sites.json."""
    p = RAIZ / "dados" / uf / "_coleta_sites.json"
    if not p.exists():
        return {}
    saida = {}
    for r in json.loads(p.read_text(encoding="utf-8"))["registros"]:
        saida[r["id_candidatura"]] = "\n".join(
            x.get("texto") or "" for x in r.get("paginas") or [])
    return saida


def arquivo_do_documento(doc: dict) -> str | None:
    for k in ("extracao_local", "arquivo_local"):
        v = doc.get(k)
        if v and (RAIZ / v).exists() and str(v).endswith(".txt"):
            return (RAIZ / v).read_text(encoding="utf-8")
    return None


def trecho_da_fonte(cit: str, src: str) -> str | None:
    """Devolve o trecho da FONTE que corresponde a citacao transcrita sem acento.

    Isto e o unico jeito legitimo de mexer numa citacao: o texto novo sai do
    documento, e nao de mim escolhendo onde por acento. Acho a posicao casando as
    versoes sem acento e recorto o original na mesma posicao.
    """
    chapado, de_onde = mapa_chapado(src)
    alvo = nu(cit)
    i = chapado.find(alvo)
    if i < 0:
        return None
    ini = de_onde[i]
    fim = de_onde[min(i + len(alvo) - 1, len(de_onde) - 1)] + 1
    achado = esp(src[ini:fim])
    return achado if nu(achado) == alvo else None


def mapa_chapado(src: str) -> tuple[str, list[int]]:
    """Versao sem acento/caixa/espaco-duplo do texto, com o indice de origem de
    cada caractere. Usado para achar a citacao na fonte e recortar o ORIGINAL."""
    plano, de_onde = [], []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        # Hifen seguido de espaco e quebra de palavra do PDF ("compro- misso"): sai
        # o hifen E o espaco, igual ao que nu() faz. Sem isto, o mapa e nu()
        # discordavam e a citacao hifenizada ganhava selo verde sem paragrafo.
        if ch == "-" and i + 1 < n and src[i + 1].isspace():
            i += 1
            while i < n and src[i].isspace():
                i += 1
            continue
        if ch.isspace():
            if not plano or plano[-1] != " ":
                plano.append(" "); de_onde.append(i)
            i += 1
            continue
        for c in unicodedata.normalize("NFD", ch).encode(
                "ascii", "ignore").decode().lower():
            plano.append(c); de_onde.append(i)
        i += 1
    return "".join(plano), de_onde


def contexto_na_fonte(cit: str, src: str, janela: int = 420) -> dict | None:
    """Onde a citacao aparece na fonte, com o texto em volta.

    Existe para a tela de revisao. Sem isto, conferir uma citacao exige abrir um
    PDF no TSE e procurar a frase a mao — e foi assim que 23 citacoes que NAO sao
    citacao passaram pela revisao humana como aprovadas. Ver o paragrafo de origem
    ao lado e a diferenca entre conferir e confiar.
    """
    chapado, de_onde = mapa_chapado(src)
    alvo = nu(cit)
    if not alvo:
        return None
    i = chapado.find(alvo)
    if i < 0:
        return None
    ini = de_onde[i]
    fim = de_onde[min(i + len(alvo) - 1, len(de_onde) - 1)] + 1
    return {"antes": esp(src[max(0, ini - janela):ini]),
            "trecho": esp(src[ini:fim]),
            "depois": esp(src[fim:fim + janela]),
            "cortado_no_inicio": ini - janela > 0,
            "cortado_no_fim": fim + janela < len(src)}


def situacao(cit: str, src: str) -> str:
    """Como a citacao se compara com a fonte, num rotulo curto para a tela."""
    if cit in src:
        return "literal"
    if esp(cit) in esp(src):
        return "literal_quebra_de_linha"
    if nu(cit) in nu(src):
        novo = trecho_da_fonte(cit, src)
        if novo and not so_acento(esp(cit), novo):
            return "difere_em_caixa"
        return "sem_acento"
    return "nao_achei"


def so_acento(a: str, b: str) -> bool:
    """True se a diferenca entre os dois for SO de acento, com a caixa igual.

    Existe por um caso concreto: o PDF do PSTU escreve "gratuito pelo sus"
    minusculo, e a citacao no acervo escreve "pelo SUS". Copiar a fonte ali
    trocaria um acerto por um erro de caixa. Diferenca de caixa e reportada, e nao
    corrigida — decidir entre a sigla da fonte e a sigla certa nao e trabalho de
    script.
    """
    def tira(s):
        return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    return tira(a) == tira(b) and a != b


def fracao_presente(cit: str, src: str) -> float:
    """Maior pedaco seguido da citacao que existe na fonte, em fracao de palavras.
    Separa "faltou um pedaco" de "frase composta de trechos espalhados"."""
    ws = nu(cit).split()
    if not ws:
        return 0.0
    s = nu(src)
    maior = 0
    for i in range(len(ws)):
        for j in range(len(ws), i + maior, -1):
            if " ".join(ws[i:j]) in s:
                maior = j - i
                break
    return maior / len(ws)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf")
    ap.add_argument("--detalhe", action="store_true")
    ap.add_argument("--porteiro", action="store_true")
    ap.add_argument("--corrigir-grafia", action="store_true",
                    dest="corrigir_grafia",
                    help="reescreve as citacoes transcritas sem acento, copiando o "
                         "trecho do documento de origem")
    a = ap.parse_args()

    prog = fontes_de_partido()
    ufs = ([a.uf.lower()] if a.uf else
           sorted(os.path.basename(os.path.dirname(f))
                  for f in glob.glob(str(RAIZ / "dados" / "*" / "posicoes.json"))))

    r: collections.Counter = collections.Counter()
    problemas, grafia, caixa = [], [], []
    for uf in ufs:
        docs = {d["id_documento"]: d for d in json.load(
            open(RAIZ / "dados" / uf / "documentos.json", encoding="utf-8"))["documentos"]}
        sites = texto_de_site(uf)
        arq_pos = RAIZ / "dados" / uf / "posicoes.json"
        dpos = json.loads(arq_pos.read_text(encoding="utf-8"))
        mudou_uf = False
        for p in dpos["posicoes"]:
            cit = p.get("citacao_literal")
            if not cit:
                r["sem citacao"] += 1
                continue
            idd = p.get("id_documento") or ""
            doc = docs.get(idd) or {}
            src = None
            # CASAMENTO EXATO, e nao endswith. Com endswith a sigla "pl" casava com
            # qualquer id terminado em "pl", e conferir uma citacao contra o
            # programa do partido errado daria "nao literal" por culpa do script.
            sigla = ALIAS.get(idd) or (idd[len("doc-programa-nacional-"):]
                                       if idd.startswith("doc-programa-nacional-") else None)
            if sigla:
                # O id do documento escreve a sigla com acento ("...-união") e o
                # arquivo de extracao, sem ("partido-uniao.json"). Sem isto, 150
                # citacoes de UNIAO e MISSAO saiam como "fonte nao guardada" — a
                # fonte estava ali, era a chave que nao batia.
                src = prog.get(sigla) or prog.get(nu(sigla))
                if src is None:
                    r[f"NAO CONFERIVEL (sem fonte guardada: {sigla})"] += 1
                    continue
            if src is None and doc.get("tipo") == "site_de_candidatura":
                src = sites.get(p.get("atribuido_a_id"))
            if src is None:
                src = arquivo_do_documento(doc)
            if src is None:
                r["NAO CONFERIVEL (fonte nao guardada)"] += 1
                continue

            if cit in src:
                r["literal, igual ao caractere"] += 1
            elif esp(cit) in esp(src):
                r["literal (difere so por quebra de linha da fonte)"] += 1
            elif nu(cit) in nu(src):
                r["TRANSCRITO SEM ACENTO (citacao certa, grafia errada)"] += 1
                novo = trecho_da_fonte(cit, src)
                if novo and not so_acento(esp(cit), novo):
                    r["difere da fonte em CAIXA, nao em acento (nao corrijo)"] += 1
                    r["TRANSCRITO SEM ACENTO (citacao certa, grafia errada)"] -= 1
                    caixa.append((uf, p["id_posicao"], esp(cit), novo))
                    continue
                grafia.append((uf, p["id_posicao"], p.get("id_documento"), cit, novo))
                if a.corrigir_grafia and novo:
                    p["citacao_literal"] = novo
                    p.setdefault("_correcoes", []).append(
                        {"campo": "citacao_literal", "em": HOJE,
                         "porque": ("a citacao estava transcrita sem acento; o trecho "
                                    "foi recopiado do documento de origem, sem escolha "
                                    "nossa de palavra"),
                         "antes": cit})
                    mudou_uf = True
            else:
                frac = fracao_presente(cit, src)
                faixa = ("quase tudo" if frac >= .8 else "metade" if frac >= .4
                         else "composta")
                r[f"NAO LITERAL — {faixa}"] += 1
                problemas.append((uf, p["id_posicao"], p.get("id_documento"),
                                  round(frac, 2), p.get("revisado_por_humano"), cit))

        if mudou_uf and a.corrigir_grafia:
            arq_pos.write_text(json.dumps(dpos, ensure_ascii=False, indent=1) + "\n",
                               encoding="utf-8")

    print("=" * 70)
    print("CONFERENCIA DAS CITACOES LITERAIS")
    print("=" * 70)
    total = sum(r.values())
    for k in sorted(r, key=lambda k: -r[k]):
        print(f"  {r[k]:5}  {k}")
    print(f"  {total:5}  total")

    if grafia:
        print(f"\n{len(grafia)} citacao(oes) CERTA(S) transcrita(s) sem acento — "
              "corrigivel copiando a fonte:")
        vistos = set()
        for uf, idp, idd, antes, novo in grafia:
            if antes in vistos and not a.detalhe:
                continue
            vistos.add(antes)
            print(f"  [{uf}] {idp} ({idd})")
            print(f"     estava: {antes[:120]}")
            print(f"     fonte:  {(novo or '[NAO LOCALIZEI O TRECHO]')[:120]}")
        if len(grafia) > len(vistos) and not a.detalhe:
            print(f"  (+{len(grafia) - len(vistos)} repeticoes do mesmo trecho em "
                  "outras candidaturas; --detalhe lista todas)")

    if problemas:
        print(f"\n{len(problemas)} citacao(oes) NAO LITERAL(IS) — o campo tem sintese, "
              "e o site mostra entre aspas:")
        for uf, idp, idd, frac, rev, cit in sorted(problemas, key=lambda x: x[3]):
            print(f"  [{uf}] {idp:8} {str(idd)[-22:]:22} {int(frac*100):3}% "
                  f"revisado={rev}")
            if a.detalhe:
                print(f"          {cit[:150]}")

    if a.porteiro:
        if problemas:
            print(f"\nPORTEIRO: {len(problemas)} citacao(oes) nao literal(is).")
            return 1
        print("\nPORTEIRO: nenhuma citacao nao literal entre as conferiveis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
