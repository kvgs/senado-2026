# -*- coding: utf-8 -*-
"""Carrossel "Você conhece os candidatos ao Senado?" — um post por região,
um slide por estado, com foto, número de urna e nome de cada candidatura.

A ORDEM E O NUMERO DE URNA, E A ARTE DIZ ISSO EM TODO SLIDE. Uma grade de
rostos e lida como ranking se nada disser o contrario. E a regra central do
projeto: a pagina do estado escreve "a ordem nao expressa preferencia nem
posicao em pesquisa", e aqui nao pode ser diferente.

O SLIDE E O ESTADO, E NAO A REGIAO. O Nordeste tem 103 candidaturas; nao cabem
numa grade legivel. Estado por estado, nenhum passa de 20, e cada slide fica
sendo o espelho de uma pagina do site.

CINCO COLUNAS, POR CAUSA DA FOTO. As 315 fotos do TSE tem 161x225 pixels. Em
1080px de largura, cinco por linha da 164px cada — o tamanho nativo. Tres por
linha exigiria ampliar 2,1x, e rosto ampliado fica borrado. O layout aqui e
consequencia do material, nao escolha estetica.

NOME NUNCA E CORTADO. Se nao couber em duas linhas, o corpo diminui ate caber.
Cortar o nome de alguem com "..." para o layout fechar seria resolver um
problema meu no nome de outra pessoa.

USO
    python gerar_artes_regiao.py --regiao Norte
    python gerar_artes_regiao.py --regiao Norte --uf AC   # so um slide, para conferir
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import pathlib
import unicodedata

from PIL import Image

import acervo

_spec = importlib.util.spec_from_file_location(
    "artes", pathlib.Path(__file__).resolve().parent / "gerar_artes.py")
_ar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ar)

Tela, f, L, A = _ar.Tela, _ar.f, _ar.L, _ar.A
TINTA, TINTA2 = _ar.TINTA, _ar.TINTA2
PAPEL, PAPEL2, LINHA = _ar.PAPEL, _ar.PAPEL2, _ar.LINHA
CIANO, CIANO_FUNDO = _ar.CIANO, _ar.CIANO_FUNDO
SOBRE_ESCURO, APAGADO, LINHA_ESCURA = _ar.SOBRE_ESCURO, _ar.APAGADO, _ar.LINHA_ESCURA

RAIZ = pathlib.Path(__file__).resolve().parent
FOTO_BORDA = "#2FB4E4"          # o mesmo token do site: --foto-borda
COLS = 5
CREDITO = "FOTO E @ DECLARADOS NO REGISTRO NO TSE"

# "NAO LOCALIZADO" SERIA FALSO PARA A MAIORIA. Das 14 candidaturas do Norte sem
# @, dez nao declararam nada ao TSE — nao e que a busca falhou, e que nao ha o
# que buscar. Outras duas declararam redes que nao sao Instagram, e duas
# declararam algo que nao vira canal. Uma frase so tem de ser verdade nos tres
# casos, e "sem Instagram no registro" e: nenhuma das tres tem @ utilizavel no
# registro. E a mesma distincao que o site inteiro faz entre ausencia da FONTE e
# ausencia da nossa BUSCA.
SEM_HANDLE = "sem Instagram no registro"


def sem_acento(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()


def pasta_da_regiao(regiao: str) -> str:
    return f"5-{sem_acento(regiao).lower().replace(' ', '-')}-quem-sao"


def handle_de(c: dict) -> str | None:
    """O @ vem do que a candidatura declarou AO TSE, e nunca de busca nossa.
    Contato achado em busca manda o eleitor escrever para um estranho — e a
    regra do projeto e que contato so entra de fonte oficial.

    Primeiro o campo ja escolhido em contato.instagram; depois, qualquer URL de
    instagram.com entre as redes declaradas. Caminhos que nao sao perfil (/p/,
    /reel/) ficam de fora."""
    ct = c.get("contato") or {}
    h = (ct.get("instagram") or "").strip()
    if h:
        return h if h.startswith("@") else "@" + h
    for u in (ct.get("redes") or []):
        m = re.search(r"instagram\.com/@?([A-Za-z0-9._]{2,40})", u, re.I)
        if m and m.group(1).lower() not in ("p", "reel", "reels", "explore", "channel", "stories"):
            return "@" + m.group(1).lower()
    return None


def medir(regiao: str) -> dict:
    est = [e for e in acervo.ler("estados.json")["estados"] if e["regiao"] == regiao]
    if not est:
        raise SystemExit(f"regiao {regiao!r} nao existe em estados.json")
    est.sort(key=lambda e: sem_acento(e["nome"]))
    saida = []
    for e in est:
        cands = acervo.ler("candidaturas.json", e["uf"])["candidaturas"]
        pos = [p for p in acervo.ler("posicoes.json", e["uf"])["posicoes"]
               if (p.get("revisao") or {}).get("resultado") not in ("remover", "corrigir")]
        gente = []
        for c in sorted(cands, key=lambda c: int(c["numero_urna"])):
            arq = (c.get("foto") or {}).get("arquivo")
            gente.append({"nome": c["pessoa"]["nome_urna"],
                          "numero": str(c["numero_urna"]),
                          "handle": handle_de(c),
                          "foto": RAIZ / arq if arq else None})
        saida.append({"uf": e["uf"], "nome": e["nome"], "gente": gente,
                      "posicoes": len(pos)})
    return {"regiao": regiao, "estados": saida,
            "total": sum(len(x["gente"]) for x in saida)}


# ---------------------------------------------------------------------------
def cartao(t: Tela, p: dict, x: int, y: int, larg: int, alt_foto: int) -> int:
    """Uma foto, o numero de urna e o nome. Devolve o y do fim do cartao."""
    if p["foto"] and p["foto"].exists():
        img = Image.open(p["foto"]).convert("RGB")
        img = img.resize((larg, alt_foto), Image.LANCZOS)
        t.img.paste(img, (x, y))
    else:
        t.d.rectangle([x, y, x + larg, y + alt_foto], fill=PAPEL2, outline=LINHA)
    # Fio fino na cor da moldura do site, para a foto nao sangrar no fundo.
    t.d.rectangle([x, y, x + larg, y + alt_foto], outline=FOTO_BORDA, width=2)

    yy = y + alt_foto + 12
    fnum = f("mono", 21)
    t.d.text((x, yy), p["numero"], font=fnum, fill=CIANO_FUNDO)
    yy += int(fnum.size * 1.35)

    # O corpo do nome cede antes do nome. Duas linhas e o limite; se nao couber,
    # tenta um corpo menor, e so no fim aceita a terceira linha.
    for corpo in (20, 18, 16, 15):
        fn = f("corpo", corpo)
        linhas = t.quebra(p["nome"], fn, larg)
        if len(linhas) <= 2:
            break
    for ln in linhas[:3]:
        t.d.text((x, yy), ln, font=fn, fill=TINTA)
        yy += int(fn.size * 1.22)

    # O @ TEM DE CABER NA CELULA, E quebra() NAO RESOLVE ISSO. quebra() corta em
    # ESPACO, e handle nao tem espaco nenhum: ela devolvia a linha inteira e o
    # texto invadia a celula vizinha — "@chicorodrigues" por cima de
    # "@hiperion_oliveira". Aqui o corpo cede primeiro; se nem no menor couber,
    # o handle vira duas linhas cortadas por LARGURA, nunca por espaco.
    yy += 2
    if p["handle"]:
        yy = escreve_handle(t, p["handle"], x, yy, larg)
    else:
        fh = f("corpo", 14)
        for ln in t.quebra(SEM_HANDLE, fh, larg):
            t.d.text((x, yy), ln, font=fh, fill=APAGADO)
            yy += int(fh.size * 1.24)
    return yy


def escreve_handle(t: Tela, handle: str, x: int, y: int, larg: int) -> int:
    """Desenha o @ dentro da largura da celula, custe o corpo que custar."""
    for corpo in (16, 15, 14, 13, 12):
        fh = f("corpo", corpo)
        if t.d.textlength(handle, font=fh) <= larg:
            t.d.text((x, y), handle, font=fh, fill=CIANO_FUNDO)
            return y + int(fh.size * 1.24)
    # Nem no corpo 12: parte em duas linhas pela largura. Handle nunca e cortado
    # com reticencias — cortado ele nao serve para procurar ninguem, que e a
    # unica coisa que ele existe para fazer.
    fh = f("corpo", 13)
    corte = len(handle)
    while corte > 1 and t.d.textlength(handle[:corte], font=fh) > larg:
        corte -= 1
    for parte in (handle[:corte], handle[corte:]):
        if parte:
            t.d.text((x, y), parte, font=fh, fill=CIANO_FUNDO)
            y += int(fh.size * 1.24)
    return y


def arte_estado(d: dict, e: dict, i: int):
    t = Tela(PAPEL, 96)
    t.y = 92
    t.mono(f"{d['regiao'].upper()} · {e['uf']}", f("mono", 19), CIANO_FUNDO, espacamento=4)
    t.espaco(14)
    t.texto(e["nome"], f("display", 64), TINTA, entre=1.05, larg=900)
    t.espaco(6)
    t.texto(f"{len(e['gente'])} candidaturas, e este ano você vota em duas. Em ordem de "
            f"número de urna — a ordem não expressa preferência nem posição em pesquisa.",
            f("corpo", 24), TINTA2, entre=1.36, larg=880)
    t.espaco(26)

    gap = 16
    linhas_n = -(-len(e["gente"]) // COLS)
    base = t.base_do_rodape()
    fim_grade = base - 52

    # A ALTURA DA LINHA E O MAIOR CARTAO, e nao o primeiro. Medindo pelo
    # primeiro, um nome que quebra em duas linhas mais adiante ("Hiperion de
    # Oliveira") empurra a ultima fileira para cima da linha de credito — foi o
    # que aconteceu em Roraima, e so apareceu no PNG.
    def mede(larg, alt_foto):
        prova = Tela(PAPEL, 96)
        return max(cartao(prova, p, 0, 0, larg, alt_foto) for p in e["gente"]) + 22

    # A foto nunca passa do tamanho nativo (161px de largura): ampliar borra o
    # rosto. Se com esse tamanho a grade nao couber, ela DIMINUI ate caber.
    larg = min(164, (L - 2 * 96 - (COLS - 1) * gap) // COLS)
    while larg > 96:
        alt_foto = round(larg * 225 / 161)
        alt_linha = mede(larg, alt_foto)
        if t.y + linhas_n * alt_linha <= fim_grade:
            break
        larg -= 6
    x0 = (L - (COLS * larg + (COLS - 1) * gap)) // 2
    y0 = t.y + max(0, (fim_grade - t.y - linhas_n * alt_linha) // 2)
    for k, p in enumerate(e["gente"]):
        cartao(t, p, x0 + (k % COLS) * (larg + gap),
               y0 + (k // COLS) * alt_linha, larg, alt_foto)

    t.y = base - 40
    t.mono(f"{e['posicoes']} INFORMAÇÕES DESTE ESTADO NO SITE · {CREDITO}",
           f("mono", 16), APAGADO, espacamento=2)
    t.rodape("kvgs.github.io/senado-2026", f"{e['uf']} · ARRASTA PARA O LADO",
             CIANO_FUNDO, APAGADO)
    t.salvar(f"{pasta_da_regiao(d['regiao'])}/{i}-{sem_acento(e['nome']).lower().replace(' ', '-')}.png")


def arte_capa(d: dict, i: int):
    """Capa clara, para nao brigar com a grade de rostos que vem logo depois.

    O fundo bege fecha o carrossel com o slide do convite, que tambem e bege: no
    meio ficam os estados, em branco. Assim a sequencia tem comeco, corpo e fim
    sem precisar de nenhuma palavra dizendo isso.
    """
    t = Tela(PAPEL2, 96)
    t.y = 100
    t.mono(f"ELEIÇÕES 2026 · SENADO FEDERAL · {d['regiao'].upper()}",
           f("mono", 20), CIANO_FUNDO, espacamento=4)
    t.espaco(20)
    t.texto(f"Conheça as candidaturas do {d['regiao']}",
            f("display", 86), TINTA, entre=1.06, larg=890)
    t.espaco(24)
    t.texto(f"São {d['total']} candidaturas nos {len(d['estados'])} estados "
            f"do {d['regiao']} — e este ano você vota em duas.",
            f("corpo", 36), TINTA2, entre=1.38, larg=860)

    fnum = f("display", 230)
    fc = f("corpo", 32)
    frase = ("Nos próximos slides, todas elas: foto, número de urna e nome, "
             "estado por estado.")
    linhas = t.quebra(frase, fc, 850)
    alto_baixo = 2 + 42 + len(linhas) * int(fc.size * 1.42)
    fim = t.base_do_rodape() - 62 - alto_baixo

    # O numero e a lista dos estados dividem a faixa livre: o numero da a escala,
    # e os nomes dizem de quais estados se trata, que e o que a pessoa procura.
    fest = f("corpo", 30)
    nomes = " · ".join(f"{e['nome']} {len(e['gente'])}" for e in d["estados"])
    linhas_est = t.quebra(nomes, fest, 860)
    alto_bloco = int(fnum.size * 0.9) + 26 + len(linhas_est) * int(fest.size * 1.4)
    y = t.y + max(0, (fim - t.y - alto_bloco) // 2)

    t.d.text((96, y), str(d["total"]), font=fnum, fill=CIANO_FUNDO)
    larg_n = t.d.textlength(str(d["total"]), font=fnum)
    t.d.text((96 + larg_n + 24, y + 104), "CANDIDATURAS",
             font=f("mono", 30), fill=APAGADO)
    t.y = y + int(fnum.size * 0.9) + 26
    for ln in linhas_est:
        t.d.text((96, t.y), ln, font=fest, fill=TINTA2)
        t.y += int(fest.size * 1.4)

    t.y = fim
    t.d.rectangle([t.m, t.y, L - t.m, t.y + 2], fill=CIANO_FUNDO)
    t.espaco(42)
    t.texto(frase, fc, TINTA, entre=1.42, larg=850)
    t.rodape("kvgs.github.io/senado-2026", "ARRASTA PARA O LADO", CIANO_FUNDO, APAGADO)
    t.salvar(f"{pasta_da_regiao(d['regiao'])}/{i}-capa.png")


def arte_comente(d: dict, i: int):
    t = Tela(PAPEL2, 96)
    t.y = 100
    t.mono("SE VOCÊ AINDA NÃO DECIDIU", f("mono", 20), CIANO_FUNDO, espacamento=4)
    t.espaco(18)
    t.texto("Comente aqui o que ainda te deixa indeciso",
            f("display", 82), TINTA, entre=1.08, larg=890)
    t.espaco(26)
    t.texto("Um tema que falta, uma dúvida sobre alguém, uma fonte que você "
            "conhece e o site não tem.",
            f("corpo", 34), TINTA2, entre=1.4, larg=860)

    t.espaco(44)
    t.mono("OS DEZ TEMAS DO SITE", f("mono", 18), APAGADO, espacamento=3)
    t.espaco(12)
    ft = f("corpo", 27)
    x, y = t.m, t.y
    for nome in [x["nome"] for x in acervo.ler("referencia.json")["temas"]]:
        larg = t.d.textlength(nome, font=ft) + 34
        if x + larg > L - t.m:
            x = t.m; y += 58
        t.d.rounded_rectangle([x, y, x + larg, y + 46], 23, fill=PAPEL,
                              outline="#D8D0C8", width=2)
        t.d.text((x + 17, y + 9), nome, font=ft, fill=TINTA2)
        x += larg + 12
    t.y = y + 46

    base = t.base_do_rodape()
    fc = f("corpo", 32)
    frase = ("No site, cada candidatura tem uma página com o que já foi levantado, "
             "a fonte de cada informação e o que ainda não foi encontrado.")
    linhas = t.quebra(frase, fc, 830)
    alto = 32 + len(linhas) * int(fc.size * 1.45) + 32
    t.y = base - 52 - alto
    t.d.rounded_rectangle([t.m, t.y, L - t.m, t.y + alto], 14, fill=TINTA)
    yy = t.y + 32
    for ln in linhas:
        t.d.text((t.m + 38, yy), ln, font=fc, fill=SOBRE_ESCURO)
        yy += int(fc.size * 1.45)
    t.rodape("kvgs.github.io/senado-2026", "@CANDIDATURASENADO", CIANO_FUNDO, APAGADO)
    t.salvar(f"{pasta_da_regiao(d['regiao'])}/{i}-comente.png")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regiao", required=True)
    ap.add_argument("--uf", help="gera so o slide deste estado, para conferir")
    ap.add_argument("--sem-capa", action="store_true", dest="sem_capa",
                    help="abre o carrossel direto na primeira grade de rostos")
    a = ap.parse_args()

    d = medir(a.regiao)
    print(f"{a.regiao}: {len(d['estados'])} estados, {d['total']} candidaturas")
    for e in d["estados"]:
        print(f"    {e['uf']} {e['nome'][:18]:18} {len(e['gente']):3} candidaturas "
              f"· {e['posicoes']:3} informacoes")
    print()
    if a.uf:
        e = next(x for x in d["estados"] if x["uf"] == a.uf.upper())
        arte_estado(d, e, d["estados"].index(e) + 1)
        return
    # A numeracao segue a ordem de postagem. Com --capa ela ocupa o 1 e os
    # estados comecam no 2; sem ela, o primeiro estado E o primeiro slide.
    n = 1
    if not a.sem_capa:
        arte_capa(d, n); n += 1
    for e in d["estados"]:
        arte_estado(d, e, n); n += 1
    arte_comente(d, n)


if __name__ == "__main__":
    main()
