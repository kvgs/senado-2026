# -*- coding: utf-8 -*-
"""Gera as seis artes do carrossel do Instagram como PNG, em 1080x1440.

POR QUE ISTO EXISTE. As artes viviam so num HTML: para postar era preciso
recortar da tela, e recorte depende da tela de quem recortou — escala, densidade
de pixel, e a mao. Aqui sai arquivo, no tamanho certo, sempre igual.

A TIPOGRAFIA E A DO SITE. As tres fontes proprias sao .woff2, que o Pillow nao
abre; sao convertidas para .ttf em fontes-ttf/ (derivado, fora do git). Usar
Arial aqui quebraria a unica coisa que faz o post e a pagina se reconhecerem.

O CONTEUDO E O MESMO DO HTML, e nao uma segunda versao. Quando um texto mudar,
muda aqui — e o HTML serve de prova visual antes de gerar.

USO
    python gerar_artes.py            # as seis, em artes-instagram/
    python gerar_artes.py --arte 3
"""
from __future__ import annotations

import argparse
import pathlib

from PIL import Image, ImageDraw, ImageFont

RAIZ = pathlib.Path(__file__).resolve().parent
FONTES = RAIZ / "fontes-ttf"
SAIDA = RAIZ / "artes-instagram"

L, A = 1080, 1440          # o retrato 4:5 do feed

# Tokens do site. Nao inventar cor aqui: se mudar no site, muda aqui.
TINTA, TINTA2 = "#141110", "#3E3833"
PAPEL, PAPEL2, LINHA = "#FFFFFF", "#F7F4F1", "#EDE7E1"
CIANO, CIANO_FUNDO = "#2FB4E4", "#0C6C8F"
SOBRE_ESCURO, APAGADO = "#EFE9E3", "#8C8279"
LINHA_ESCURA = "#34302C"


PESO_PADRAO = {"display": 700, "corpo": 400, "mono": 400}


def f(nome: str, tam: int, peso: int | None = None) -> ImageFont.FreeTypeFont:
    """A fonte, no tamanho e no PESO pedidos.

    O PESO PRECISOU EXISTIR, E O PADRAO ESTAVA ERRADO. Public Sans e Bricolage
    Grotesque sao fontes VARIAVEIS, com eixo wght. O Pillow abre a instancia
    padrao do arquivo, e no Public Sans essa instancia e Thin (100) — o peso mais
    fino que existe. Todo texto de corpo de todas as artes ja publicadas saiu em
    Thin, sem ninguem ter escolhido isso; a curadoria leu uma arte no celular e
    disse que o texto estava "muito claro e fino". Estava mesmo, e nao era
    decisao de desenho: era o padrao do arquivo vazando.

    Agora o padrao e Regular no corpo e Bold no display, e quem quiser outro peso
    pede. Arte antiga so muda quando for regerada, que e o modelo do projeto.
    """
    arq = {"display": "bricolage-grotesque.ttf", "corpo": "public-sans.ttf",
           "mono": "ibm-plex-mono.ttf"}[nome]
    p = FONTES / arq
    if not p.exists():
        raise SystemExit(
            f"falta {p}. Rode a conversao das fontes:" + chr(10)
            + "  python -c \"import pathlib;from fontTools.ttLib import TTFont;"
              "[ (lambda t: (setattr(t,'flavor',None), t.save('fontes-ttf/'+w.stem+'.ttf')))"
              "(TTFont(str(w))) for w in pathlib.Path('fontes-web').glob('*.woff2') ]\"")
    fonte = ImageFont.truetype(str(p), tam)
    alvo = peso if peso is not None else PESO_PADRAO[nome]
    try:
        eixos = fonte.get_variation_axes()
    except OSError:
        return fonte                      # fonte estatica: nao ha o que ajustar
    # CASAR PELO NOME DO EIXO, e nao pela posicao. Passar uma lista de um valor
    # ajusta o PRIMEIRO eixo — e no Bricolage o primeiro e "opsz", nao "wght".
    # Escrito assim, o peso do display nao mudava e a largura do texto era a
    # mesma em 400, 500 e 700; o defeito passava porque a arte continuava saindo.
    valores = []
    for e in eixos:
        tag = e["name"]
        tag = tag.decode() if isinstance(tag, bytes) else str(tag)
        v = alvo if tag.lower().startswith("wght") or "weight" in tag.lower() else \
            min(max(tam, e["minimum"]), e["maximum"])
        valores.append(min(max(v, e["minimum"]), e["maximum"]))
    fonte.set_variation_by_axes(valores)
    return fonte


class Tela:
    """Cursor de desenho: cada bloco desenha e avanca o y. Assim a composicao e
    lida na ordem em que aparece, e nao em coordenadas soltas."""

    def __init__(self, fundo: str, margem: int = 96):
        self.img = Image.new("RGB", (L, A), fundo)
        self.d = ImageDraw.Draw(self.img)
        self.m = margem
        self.y = 0
        self.larg = L - 2 * margem

    # -- medidas ---------------------------------------------------------
    def quebra(self, txt: str, fonte, larg: int) -> list[str]:
        linhas, atual = [], ""
        for p in txt.split():
            teste = (atual + " " + p).strip()
            if self.d.textlength(teste, font=fonte) <= larg:
                atual = teste
            else:
                if atual:
                    linhas.append(atual)
                atual = p
        if atual:
            linhas.append(atual)
        return linhas

    # -- blocos ----------------------------------------------------------
    def espaco(self, px: int):
        self.y += px

    def texto(self, txt, fonte, cor, *, entre=1.4, larg=None, x=None):
        larg = larg or self.larg
        x = self.m if x is None else x
        alt = int(fonte.size * entre)
        for ln in self.quebra(txt, fonte, larg):
            self.d.text((x, self.y), ln, font=fonte, fill=cor)
            self.y += alt
        return self.y

    def mono(self, txt, fonte, cor, *, espacamento=3, x=None):
        """Letter-spacing nao existe no Pillow: desenha caractere a caractere."""
        x = self.m if x is None else x
        for ch in txt:
            self.d.text((x, self.y), ch, font=fonte, fill=cor)
            x += self.d.textlength(ch, font=fonte) + espacamento
        self.y += int(fonte.size * 1.4)

    def regua(self, cor, grossura=1, *, cima=0, baixo=0):
        self.y += cima
        self.d.rectangle([self.m, self.y, L - self.m, self.y + grossura - 1], fill=cor)
        self.y += grossura + baixo

    def base_do_rodape(self, grossura=3) -> int:
        """Onde o rodape comeca. Serve para ancorar o que vem logo acima dele
        sem desenhar nada — antes eu chamava rodape() com espessura zero so para
        obter este numero, e o retangulo de altura negativa estourava."""
        return A - self.m - (grossura + 34 + int(f("mono", 22).size * 1.4))

    def rodape(self, url, nota, cor, cor_nota, *, grossura=3):
        """Ancorado embaixo: mede a altura propria e desenha a partir do pe."""
        fm, fn = f("mono", 22), f("mono", 18)
        base = self.base_do_rodape(grossura)
        self.d.rectangle([self.m, base, L - self.m, base + grossura - 1], fill=cor)
        yy = base + grossura + 34
        x = self.m
        for ch in url:
            self.d.text((x, yy), ch, font=fm, fill=cor)
            x += self.d.textlength(ch, font=fm) + 1
        if nota:
            larg_n = sum(self.d.textlength(c, font=fn) + 1.6 for c in nota)
            x = L - self.m - larg_n
            for ch in nota:
                self.d.text((x, yy + 5), ch, font=fn, fill=cor_nota)
                x += self.d.textlength(ch, font=fn) + 1.6
        return base

    def salvar(self, nome: str):
        """`nome` pode trazer a subpasta: "1-o-site/1-oito-anos.png". Cada
        carrossel mora na sua pasta, e o numero do arquivo e a ordem em que o
        slide entra no post — assim o proprio explorador de arquivos ja mostra
        na ordem certa, e nao e preciso lembrar qual vinha antes."""
        p = SAIDA / nome
        p.parent.mkdir(parents=True, exist_ok=True)
        self.img.save(p, "PNG", optimize=True)
        print(f"  {nome:44} {p.stat().st_size/1024:5.0f} KB")


# ---------------------------------------------------------------------------
def arte1():
    t = Tela(TINTA, 96)
    t.y = 104
    t.mono("ELEIÇÃO DE 4 DE OUTUBRO", f("mono", 19), CIANO, espacamento=4)
    # O "8" e o "anos" sao MEDIDOS, e nao posicionados por deslocamento chutado:
    # o primeiro palpite encostou os dois. textbbox devolve a caixa real da
    # tinta, que e o que importa quando o corpo da fonte e 430pt.
    f8, fa, fc = f("display", 430), f("display", 118), f("corpo", 36)
    cx8 = t.d.textbbox((0, 0), "8", font=f8)
    cxa = t.d.textbbox((0, 0), "anos", font=fa)
    corpo = ("É quanto dura o mandato de senador. O dobro do presidente "
             "que você elege no mesmo dia.")
    n_linhas = len(t.quebra(corpo, fc, 760))

    # O GRUPO E CENTRADO na faixa livre, e nao ancorado no topo. Com posicao
    # fixa sobrava um vazio de 300px ora em cima, ora embaixo, conforme o texto
    # mudava de tamanho — e vazio grande so num lado le como erro.
    alt_8, alt_a = cx8[3] - cx8[1], cxa[3] - cxa[1]
    alt_corpo = n_linhas * int(fc.size * 1.4)
    grupo = alt_8 + 26 + alt_a + 74 + alt_corpo
    faixa_topo, faixa_base = t.y + 40, t.base_do_rodape() - 40
    topo_do_8 = faixa_topo + max(0, (faixa_base - faixa_topo - grupo) // 2)

    t.d.text((t.m - cx8[0], topo_do_8 - cx8[1]), "8", font=f8, fill=PAPEL)
    y_anos = topo_do_8 + alt_8 + 26
    t.d.text((t.m - cxa[0], y_anos - cxa[1]), "anos", font=fa, fill=CIANO)
    t.y = y_anos + alt_a + 74
    t.texto(corpo, fc, SOBRE_ESCURO, larg=760)
    t.rodape("kvgs.github.io/senado-2026", "CADA ESTADO ELEGE 2", CIANO, APAGADO)
    t.salvar("1-o-site/1-oito-anos.png")


def arte2():
    t = Tela(PAPEL, 96)
    t.y = 104
    t.texto("Coisas que só o Senado faz", f("display", 84), TINTA, entre=1.16)
    # Titulo de 84px com entrelinha apertada precisa de folga ABAIXO: com 22px o
    # "faz" encostava no subtitulo, e as duas linhas liam como uma so.
    t.espaco(48)
    t.texto("Nenhuma lei federal passa sem as duas Casas. Mas estas quatro "
            "atribuições são do Senado — e é o único voto em que o Acre pesa "
            "igual a São Paulo.", f("corpo", 33), TINTA2, larg=830)
    t.espaco(40)
    itens = [
        "Aprova quem entra no Supremo Tribunal Federal",
        "Aprova a diretoria do Banco Central e das agências reguladoras",
        "Aprova embaixadores e autoriza empréstimos externos dos estados",
        "Julga o presidente da República em impeachment, depois de a Câmara autorizar",
    ]
    fc = f("corpo", 38)
    for i, it in enumerate(itens):
        t.regua(LINHA, 1, baixo=30)
        t.d.rectangle([t.m, t.y + 12, t.m + 15, t.y + 27], fill=CIANO)
        y0 = t.y
        t.texto(it, fc, TINTA, entre=1.32, larg=t.larg - 44, x=t.m + 44)
        t.y = max(t.y, y0) + 26
    t.regua(LINHA, 1)
    t.rodape("kvgs.github.io/senado-2026", "", CIANO_FUNDO, APAGADO)
    t.salvar("1-o-site/2-so-o-senado.png")


def arte3():
    t = Tela(TINTA, 96)
    t.y = 100
    t.mono("A LACUNA QUE NINGUÉM CONTA", f("mono", 19), CIANO, espacamento=4)
    t.espaco(14)
    t.texto("Quem concorre ao Senado não precisa registrar plano de governo",
            f("display", 74), PAPEL, entre=1.12, larg=880)
    t.espaco(46)
    fc, fm = f("corpo", 42), f("mono", 20)
    for nome, marca, vazio in (("Presidente", "PLANO OBRIGATÓRIO", False),
                               ("Governador", "PLANO OBRIGATÓRIO", False),
                               ("Prefeito", "PLANO OBRIGATÓRIO", False),
                               ("Senador", "nada é exigido", True)):
        t.d.rectangle([t.m, t.y, L - t.m, t.y], fill=LINHA_ESCURA)
        t.y += 1
        alto = 34 + int(fc.size * 1.2) + 34
        if vazio:
            t.d.rectangle([t.m - 28, t.y, L - t.m + 28, t.y + alto], fill="#221E1B")
        t.d.text((t.m, t.y + 34), nome, font=fc,
                 fill=PAPEL if vazio else SOBRE_ESCURO)
        larg_m = sum(t.d.textlength(c, font=fm) + 2 for c in marca)
        x = L - t.m - larg_m
        for ch in marca:
            t.d.text((x, t.y + 34 + 14), ch, font=fm, fill="#6B635B" if vazio else CIANO)
            x += t.d.textlength(ch, font=fm) + 2
        t.y += alto
    t.d.rectangle([t.m, t.y, L - t.m, t.y], fill=LINHA_ESCURA)

    # A conclusao e ANCORADA NO PE, como o margin-top:auto do HTML. Calculada de
    # cima para baixo ela parava no meio e deixava 180px de vazio embaixo, que
    # numa arte de formato fixo le como corte errado.
    fcc, fl = f("corpo", 37), f("mono", 19)
    conclusao = ("Por isso é difícil saber o que cada candidatura defende: não existe "
                 "um documento único onde procurar.")
    n = len(t.quebra(conclusao, fcc, 860))
    alto_bloco = 2 + 44 + n * int(fcc.size * 1.42) + 16 + int(fl.size * 1.4)
    t.y = A - t.m - alto_bloco
    t.d.rectangle([t.m, t.y, L - t.m, t.y + 2], fill=CIANO)
    t.y += 44
    t.texto(conclusao, fcc, PAPEL, entre=1.42, larg=860)
    t.espaco(16)
    t.mono("LEI 9.504/1997, ART. 11, §1º, IX", fl, APAGADO, espacamento=2)
    t.salvar("1-o-site/3-por-que-existe.png")


def arte4():
    t = Tela(PAPEL2, 96)
    t.y = 100
    t.mono("INDEPENDENTE · CÓDIGO E DADOS ABERTOS", f("mono", 19), CIANO_FUNDO, espacamento=4)
    t.espaco(16)
    t.texto("O que cada candidatura defende, com a fonte ao lado",
            f("display", 76), TINTA, entre=1.1)
    t.espaco(44)

    topo, largc, gap = t.y, (t.larg - 34) // 2, 34
    fh, fp = f("mono", 18), f("corpo", 30)
    for i, (titulo, cor_topo, linhas) in enumerate((
        ("O QUE ELE FAZ", CIANO,
         ["Reúne posições em 10 temas, estado por estado",
          "Mostra a fonte e o link de cada informação",
          "Diz qual tipo de ausência, quando não há nada"]),
        ("O QUE ELE NUNCA FAZ", TINTA,
         ["Ranquear candidaturas", "Recomendar voto", "Tratar silêncio como posição"]),
    )):
        x0 = t.m + i * (largc + gap)
        y = topo
        alto = 430
        t.d.rectangle([x0, y, x0 + largc, y + alto], fill=PAPEL, outline=LINHA)
        t.d.rectangle([x0, y, x0 + largc, y + 4], fill=cor_topo)
        yy = y + 30
        xx = x0 + 32
        for ch in titulo:
            t.d.text((xx, yy), ch, font=fh, fill=APAGADO)
            xx += t.d.textlength(ch, font=fh) + 2.4
        yy += 46
        for k, ln in enumerate(linhas):
            if k:
                t.d.rectangle([x0 + 32, yy, x0 + largc - 32, yy], fill=LINHA)
                yy += 16
            for w in t.quebra(ln, fp, largc - 64):
                t.d.text((x0 + 32, yy), w, font=fp, fill=TINTA)
                yy += int(fp.size * 1.4)
            yy += 14
    t.y = topo + 430 + 46

    cx, cy = t.m, t.y
    fe = f("corpo", 29)
    linhas = t.quebra("Hoje: 27 estados e 315 candidaturas cadastradas direto da base "
                      "do TSE. As informações ainda não revisadas por uma pessoa "
                      "aparecem marcadas, uma a uma, com o link da fonte.", fe, t.larg - 76)
    alto = 34 + len(linhas) * int(fe.size * 1.45) + 34
    t.d.rounded_rectangle([cx, cy, L - t.m, cy + alto], 12, fill=TINTA)
    yy = cy + 34
    for ln in linhas:
        t.d.text((cx + 38, yy), ln, font=fe, fill=SOBRE_ESCURO)
        yy += int(fe.size * 1.45)
    t.rodape("kvgs.github.io/senado-2026", "FALTA MUITO — E FALTAR É O CONVITE",
             CIANO_FUNDO, APAGADO)
    t.salvar("1-o-site/4-faz-e-nao-faz.png")


def arte5():
    t = Tela(PAPEL, 96)
    t.y = 100
    t.mono("AUSÊNCIA NÃO É PONTO FINAL", f("mono", 19), CIANO_FUNDO, espacamento=4)
    t.espaco(16)
    t.texto("Quando o site não sabe, ele te ajuda a perguntar",
            f("display", 74), TINTA, entre=1.12, larg=820)
    t.espaco(52)
    fh, fp = f("mono", 18), f("corpo", 34)
    for titulo, cor_t, corpo, escuro in (
        ("PERGUNTE VOCÊ MESMO", CIANO_FUNDO,
         "Sem informação sobre um tema? O site abre um e-mail já redigido, em tom "
         "formal, para o contato oficial que a candidatura declarou ao TSE. Você "
         "lê, ajusta e envia.", False),
        ("CÓDIGO E DADOS ABERTOS", CIANO,
         "Todo o acervo e todo o código estão públicos no GitHub. Dá para conferir "
         "qualquer informação até a origem — ou apontar um erro, que é contribuição "
         "bem-vinda.", True),
    ):
        linhas = t.quebra(corpo, fp, t.larg - 92)
        alto = 44 + 40 + len(linhas) * int(fp.size * 1.4) + 30
        t.d.rounded_rectangle([t.m, t.y, L - t.m, t.y + alto], 14,
                              fill=TINTA if escuro else PAPEL2,
                              outline=TINTA if escuro else LINHA)
        yy, xx = t.y + 44, t.m + 46
        for ch in titulo:
            t.d.text((xx, yy), ch, font=fh, fill=cor_t)
            xx += t.d.textlength(ch, font=fh) + 2.4
        yy += 40
        for ln in linhas:
            t.d.text((t.m + 46, yy), ln, font=fp,
                     fill=SOBRE_ESCURO if escuro else TINTA)
            yy += int(fp.size * 1.4)
        t.y += alto + 30
    t.rodape("kvgs.github.io/senado-2026", "SILÊNCIO NÃO VIRA POSIÇÃO",
             CIANO_FUNDO, APAGADO)
    t.salvar("1-o-site/5-perguntar.png")


def arte6():
    t = Tela(TINTA, 96)
    t.y = 100
    t.mono("O ESTADO REAL, HOJE", f("mono", 19), CIANO, espacamento=4)
    t.espaco(18)
    t.texto("Nenhum site cobre 315 candidaturas sozinho",
            f("display", 74), PAPEL, entre=1.12, larg=800)
    t.espaco(60)

    fn, fq, fcc = f("display", 128), f("corpo", 26), f("corpo", 38)
    conclusao = ("O que falta não é segredo — está escrito em cada página. "
                 "Conferir uma informação já é contribuir.")

    # A conclusao e ancorada logo acima do rodape, e o PLACAR e centrado na faixa
    # que sobra. Fixar os dois pelo topo deixava 350px de buraco no meio.
    n_cc = len(t.quebra(conclusao, fcc, 830))
    alto_cc = 2 + 44 + n_cc * int(fcc.size * 1.4)
    y_conclusao = t.base_do_rodape() - 34 - alto_cc

    col = t.larg // 3
    gap = 26                     # respiro entre a coluna e o divisor a sua direita
    alto_placar = 1 + 30 + 130 + 2 * int(fq.size * 1.34) + 20
    topo = t.y + max(0, (y_conclusao - t.y - alto_placar) // 2)

    t.d.rectangle([t.m, topo, L - t.m, topo], fill=LINHA_ESCURA)
    for i, (n, q, acende) in enumerate((("692", "informações publicadas", False),
                                        ("41", "conferidas contra a fonte por uma pessoa", True),
                                        ("201", "candidaturas ainda sem nada", False))):
        x0 = t.m + i * col
        if i:
            t.d.rectangle([x0 - gap, topo, x0 - gap, topo + alto_placar], fill=LINHA_ESCURA)
        t.d.text((x0, topo + 30), n, font=fn, fill=CIANO if acende else PAPEL)
        yy = topo + 30 + 130
        for ln in t.quebra(q, fq, col - gap - 20):
            t.d.text((x0, yy), ln, font=fq, fill=APAGADO)
            yy += int(fq.size * 1.34)

    t.rodape("kvgs.github.io/senado-2026", "", CIANO, APAGADO)
    t.y = y_conclusao
    t.d.rectangle([t.m, t.y, L - t.m, t.y + 2], fill=CIANO)
    t.y += 44
    t.texto(conclusao, fcc, PAPEL, entre=1.4, larg=830)
    t.salvar("1-o-site/6-o-convite.png")


ARTES = {1: arte1, 2: arte2, 3: arte3, 4: arte4, 5: arte5, 6: arte6}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arte", type=int, choices=sorted(ARTES))
    a = ap.parse_args()
    print(f"gerando em {SAIDA.name}/  ({L}x{A})")
    for n in ([a.arte] if a.arte else sorted(ARTES)):
        ARTES[n]()


if __name__ == "__main__":
    main()
