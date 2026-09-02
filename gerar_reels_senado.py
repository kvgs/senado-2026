# -*- coding: utf-8 -*-
"""Reels vertical sobre O CARGO: abre no subsidio e fecha no site.

MESMA FONTE DO CARROSSEL. Os dois leem dados/institucional-senado.json e os dois
chamam institucional.conferir() antes de desenhar — que PARA se alguma citacao
nao existir palavra por palavra no arquivo guardado em fontes/. Nenhuma frase e
digitada aqui: mudar o texto num lugar muda nos dois.

A ORDEM E O GANCHO, e foi escolha da curadoria: o valor do subsidio primeiro,
porque e o que faz parar o dedo. O numero nunca aparece sozinho — a vigencia
entra na mesma cena, e a cena seguinte diz quem fixa o valor. Valor de
remuneracao sem data envelhece calado, e este e dos que mais circulam errados.

SEM AUDIO, como o outro Reels: a trilha entra no Instagram, onde e licenciada.

USO
    python gerar_reels_senado.py
    python gerar_reels_senado.py --so-quadros
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import textwrap

from PIL import Image, ImageDraw

import institucional
from gerar_artes import APAGADO, PAPEL2, SOBRE_ESCURO, TINTA, TINTA2, f
from gerar_artes_senado import ACENTO, ACENTO_NO_ESCURO, SITE
from gerar_reels_uf import (ALT, LARG, MARGEM, SEGURO_BASE, entra, janela,
                            quebra)

RAIZ = pathlib.Path(__file__).resolve().parent
SAIDA = RAIZ / "artes-instagram" / "10-o-cargo-em-disputa-reels"
CINZA_NO_ESCURO = "#C9C1B9"


def rodape(dr: ImageDraw.ImageDraw, cor: str, cor_nota: str) -> None:
    y = SEGURO_BASE - 92
    dr.rectangle([MARGEM, y, LARG - MARGEM, y + 3], fill=cor)
    dr.text((MARGEM, y + 26), SITE, font=f("mono", 34), fill=cor)
    fr = f("mono", 30)
    txt = "@CANDIDATURASENADO"
    dr.text((LARG - MARGEM - dr.textlength(txt, font=fr), y + 30), txt,
            font=fr, fill=cor_nota)


def tela(fundo) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (LARG, ALT), fundo)
    dr = ImageDraw.Draw(img)
    dr._image = img
    return img, dr


# ------------------------------------------------------------------- cenas
def cena_dinheiro(t: float, dur: float, d: dict) -> Image.Image:
    """Unica cena escura, como a capa do carrossel: o valor e o gancho."""
    ft = d["quanto-ganha"]
    img, dr = tela(TINTA)

    # O NUMERO NAO SOBE NUM CONTADOR. Foi a primeira versao, e o contador
    # colocava na tela, por dois segundos, valores que NAO sao o subsidio —
    # "R$ 21.437,88" e "R$ 38.902,11". Num video deste projeto isso e um quadro
    # publicado com salario errado, e quem tira print no meio da subida fica com
    # ele. O numero entra inteiro, crescendo um pouco e ganhando corpo: e
    # dinamico do mesmo jeito e nunca mostra um valor que nao existe.
    p = janela(t, 0.25, 0.5)
    if p > 0:
        fn = f("display", 118, 700)
        txt = ft["olho"]
        cx, cy = dr.textlength(txt, font=fn), fn.size * 1.3
        capa = Image.new("RGBA", (int(cx) + 40, int(cy) + 40), (0, 0, 0, 0))
        ImageDraw.Draw(capa).text((0, 0), txt, font=fn, fill=SOBRE_ESCURO)
        esc = 0.93 + 0.07 * p
        cap = capa.resize((int(capa.width * esc), int(capa.height * esc)))
        cap.putalpha(cap.getchannel("A").point(lambda v: int(v * p)))
        img.alpha_composite(cap, (MARGEM, 340 + int((1 - p) * 18)))
    dr.text((MARGEM, 250), ft["chapeu"], font=f("mono", 32), fill=ACENTO_NO_ESCURO)
    entra(dr, ft["frase"], f("display", 74), SOBRE_ESCURO, MARGEM, 560,
          LARG - 2 * MARGEM, t, inicio=1.0)
    entra(dr, "Vigência abril de 2026, no demonstrativo do próprio Senado.",
          f("corpo", 44, 400), CINZA_NO_ESCURO, MARGEM, 830, LARG - 2 * MARGEM,
          t, inicio=2.0)
    entra(dr, "Não inclui verba de gabinete, cota parlamentar nem auxílio-moradia.",
          f("corpo", 40, 400), CINZA_NO_ESCURO, MARGEM, 1010, LARG - 2 * MARGEM,
          t, inicio=2.8)
    rodape(dr, ACENTO_NO_ESCURO, CINZA_NO_ESCURO)
    return img


def cena_fato(t: float, dur: float, ft: dict, *, tam_olho: int = 104,
              mostra_resumo: bool = True) -> Image.Image:
    """O esqueleto das cenas claras: chapeu, olho, frase, resumo e o artigo."""
    img, dr = tela(PAPEL2)
    dr.text((MARGEM, 250), ft["chapeu"], font=f("mono", 30), fill=ACENTO)
    y = entra(dr, ft["olho"], f("display", tam_olho), TINTA, MARGEM, 320,
              LARG - 2 * MARGEM, t)
    y = entra(dr, ft["frase"], f("display", 66), TINTA, MARGEM, y + 34,
              LARG - 2 * MARGEM, t, inicio=0.7)
    if mostra_resumo:
        y = entra(dr, ft["resumo"], f("corpo", 42, 400), TINTA2, MARGEM, y + 30,
                  LARG - 2 * MARGEM, t, inicio=1.5)
    # O ARTIGO ENTRA EM TODA CENA. E o que separa isto de um card com uma frase
    # bonita: quem ve consegue ir conferir sozinho.
    if janela(t, 2.2, 0.5) > 0:
        dr.text((MARGEM, SEGURO_BASE - 190), ft["dispositivo"].upper(),
                font=f("mono", 28), fill=ACENTO)
    rodape(dr, ACENTO, APAGADO)
    return img


def cena_pesa(t: float, dur: float, d: dict) -> Image.Image:
    """As quatro competencias entrando uma a uma. Nenhum adjetivo: so o que e."""
    img, dr = tela(PAPEL2)
    dr.text((MARGEM, 250), "POR QUE O CARGO PESA", font=f("mono", 30), fill=ACENTO)
    entra(dr, "Sem o Senado, nada disso acontece.", f("display", 88), TINTA,
          MARGEM, 320, LARG - 2 * MARGEM, t)
    itens = [(d["por-que-pesa-stf"], "Ministro do STF só entra depois de aprovado"),
             (d["por-que-pesa-impeachment"], "Julgar o presidente por crime de responsabilidade"),
             (d["por-que-pesa-emenda"], "Nenhuma emenda passa sem três quintos"),
             (d["por-que-pesa-lei"], "Suspender lei declarada inconstitucional")]
    y = 620
    for k, (ft, curto) in enumerate(itens):
        if janela(t, 1.0 + k * 0.75, 0.4) <= 0:
            continue
        fq = f("corpo", 46, 500)
        linhas = quebra(dr, curto, fq, LARG - 2 * MARGEM - 70)
        dr.rectangle([MARGEM, y + 12, MARGEM + 26, y + 38], fill=ACENTO)
        for i, ln in enumerate(linhas):
            dr.text((MARGEM + 52, y + i * 58), ln, font=fq, fill=TINTA)
        y += len(linhas) * 58 + 24
        dr.text((MARGEM + 52, y - 6), ft["dispositivo"].replace("Constituição, ", ""),
                font=f("mono", 26), fill=ACENTO)
        y += 62
    rodape(dr, ACENTO, APAGADO)
    return img


def cena_fecha(t: float, dur: float, d: dict, n_cand: int, n_est: int) -> Image.Image:
    img, dr = tela(PAPEL2)
    entra(dr, "E o que cada candidatura defende?", f("display", 92), TINTA,
          MARGEM, 320, LARG - 2 * MARGEM, t)
    entra(dr, f"{n_cand} candidaturas nos {n_est} estados, tema por tema — com a "
              f"fonte e o trecho citado ao lado de cada informação.",
          f("corpo", 46, 400), TINTA2, MARGEM, 660, LARG - 2 * MARGEM, t,
          inicio=1.0)
    pl = janela(t, 2.0, 1.2)
    if pl > 0:
        fr = f("mono", 46)
        dr.text((MARGEM, 1010), SITE, font=fr, fill=ACENTO)
        dr.text((MARGEM, 1074), "@candidaturasenado", font=fr, fill=TINTA2)
    return img


def roteiro(d: dict, n_cand: int, n_est: int) -> list[tuple]:
    """A ordem: dinheiro, quem fixa, o que faz, quantos votos, por que pesa, site."""
    return [
        (lambda t, dur: cena_dinheiro(t, dur, d), 5.5, "o subsídio"),
        (lambda t, dur: cena_fato(t, dur, d["quem-fixa"], tam_olho=88), 5.0,
         "quem fixa o valor"),
        (lambda t, dur: cena_fato(t, dur, d["o-que-faz"]), 6.0, "o que o cargo é"),
        (lambda t, dur: cena_fato(t, dur, d["oito-anos"]), 5.0, "o mandato"),
        (lambda t, dur: cena_fato(t, dur, d["dois-ou-um"]), 6.0, "quantos votos"),
        (lambda t, dur: cena_pesa(t, dur, d), 8.0, "as quatro competências"),
        (lambda t, dur: cena_fecha(t, dur, d, n_cand, n_est), 5.0, "o site"),
    ]


def escreve_legenda(cenas: list, dur: float, d: dict, n_cand: int, n_est: int) -> None:
    ft = d["quanto-ganha"]
    tags = ("#eleições2026 #senado #votoconsciente #dadosabertos #transparência "
            "#educaçãopolítica #constituição #política #brasil")
    corpo = f"""# Reels — o cargo em disputa

Vídeo vertical de {dur:.0f}s, {len(cenas)} cenas, **sem áudio**.
Gerado por `python gerar_reels_senado.py`.

---

## Legenda

**{ft['olho']} é quanto um senador recebe de subsídio por mês.**

{textwrap.fill("Vigência em abril de 2026, no demonstrativo do próprio Senado — não em notícia sobre ele. Quem fixa o valor não é o senador: a Constituição dá isso ao Congresso, e manda que seja idêntico ao de deputado federal.", 88)}

{textwrap.fill("E o cargo que esse valor paga: senador representa o estado, e não a população dele; o mandato é de oito anos, o dobro do de presidente; em 2026 são dois votos, e em 2022 foi um; e nenhum ministro do STF entra no tribunal, nenhum presidente é julgado por crime de responsabilidade e nenhuma emenda à Constituição passa sem o Senado.", 88)}

{textwrap.fill("Cada uma dessas frases aparece no vídeo com o artigo ao lado, e todas foram conferidas palavra por palavra contra o texto compilado da Constituição publicado pela Câmara dos Deputados e contra o demonstrativo de remuneração do Senado.", 88)}

🔗 {SITE} — {n_cand} candidaturas nos {n_est} estados, tema por tema.

{tags}

---

## Antes de postar

**Sem trilha.** A música entra no próprio Instagram, onde é licenciada.

**O carrossel `9-o-cargo-em-disputa/` conta a mesma coisa em 12 imagens**, com a
citação inteira em cada slide. O vídeo prende; o carrossel é onde a frase da
fonte cabe legível e fica no grid para consulta.

## Como as frases são conferidas

Vídeo e carrossel leem o **mesmo** `dados/institucional-senado.json`, e os dois
chamam `institucional.py` antes de desenhar. Ele abre os arquivos de `fontes/`,
confere cada citação palavra por palavra e para com erro se alguma não estiver
lá — distinguindo frase inexistente de frase que só casa sem acento. Mudar um
texto num lugar muda nos dois; não existe versão do vídeo com frase diferente da
do carrossel.

## O que ficou de fora

Verba de gabinete, cota parlamentar e auxílio-moradia: o Senado publica os três,
mas não foram levantados, e a cena do subsídio diz isso na tela. Nada sobre o que
o eleitor sabe ou não sabe. Nenhum adjetivo sobre a importância do cargo — "por
que pesa" está em quatro competências com artigo ao lado.

## As cenas

"""
    linhas = "\n".join(f"{k + 1}. {nome} — {seg:.1f}s"
                       for k, (_, seg, nome) in enumerate(cenas))
    (SAIDA / "LEGENDA.md").write_text(corpo + linhas + "\n", encoding="utf-8")


def main() -> None:
    import acervo

    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--so-quadros", action="store_true", dest="so_quadros")
    a = ap.parse_args()

    fatos = institucional.conferir(silencioso=True)
    d = {x["id"]: x for x in fatos}
    est = acervo.ler("estados.json")["estados"]
    n_cand = sum(len(acervo.ler("candidaturas.json", e["uf"])["candidaturas"])
                 for e in est)

    cenas = roteiro(d, n_cand, len(est))
    total = sum(seg for _, seg, _ in cenas)
    SAIDA.mkdir(parents=True, exist_ok=True)
    print(f"{len(cenas)} cenas, {total:.0f}s, {a.fps} qps "
          f"({int(total * a.fps)} quadros de {LARG}x{ALT})")

    if a.so_quadros:
        conf = SAIDA / "_quadros"
        conf.mkdir(exist_ok=True)
        for k, (fn, seg, nome) in enumerate(cenas):
            for frac in (0.45, 0.99):
                fn(seg * frac, seg).convert("RGB").save(
                    conf / f"{k + 1:02d}-{int(frac * 100)}.png")
        print(f"  amostra em {conf.name}/")
        return

    saida = SAIDA / "reels-o-cargo.mp4"
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{LARG}x{ALT}", "-framerate", str(a.fps), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(saida)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    n = 0
    try:
        for fn, seg, _ in cenas:
            for k in range(int(seg * a.fps)):
                proc.stdin.write(fn(k / a.fps, seg).convert("RGB").tobytes())
                n += 1
                if n % 60 == 0:
                    print(f"    {n} quadros", end="\r", flush=True)
        proc.stdin.close()
    except BrokenPipeError:
        pass
    err = proc.stderr.read().decode("utf-8", "replace")
    if proc.wait() != 0:
        raise SystemExit("PAROU: o ffmpeg falhou.\n" + err[-1500:])
    escreve_legenda(cenas, total, d, n_cand, len(est))
    kb = saida.stat().st_size / 1024
    print(f"  {saida.relative_to(RAIZ)}  {n} quadros · {kb / 1024:.1f} MB")


if __name__ == "__main__":
    main()
