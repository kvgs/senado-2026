# -*- coding: utf-8 -*-
"""Carrossel sobre O CARGO: quanto ganha, o que faz, quantos votos, por que pesa.

O QUE ESTA AQUI NAO SAI DO ACERVO. Sai da Constituicao e do demonstrativo de
remuneracao do proprio Senado, guardados em fontes/ e conferidos por
institucional.py — que PARA se alguma citacao nao existir palavra por palavra no
arquivo. Por isso cada slide mostra o dispositivo e a frase citada: quem ve
confere sem depender de acreditar em mim.

A ORDEM E O GANCHO. O carrossel abre no valor do subsidio, que e a informacao
que mais faz parar o dedo — e, por isso mesmo, a que mais circula errada. O
numero nunca aparece sozinho: na mesma tela vem a vigencia (um valor de
remuneracao sem data envelhece calado), quem fixa o valor, e o que ele NAO
inclui.

O QUE NAO ENTRA: nenhuma frase sobre o que o eleitor sabe ou deixa de saber, e
nenhum adjetivo sobre a importancia do cargo. "Por que pesa" e respondido em
competencias, que sao conferiveis, e nao em opiniao.

USO
    python gerar_artes_senado.py
"""
from __future__ import annotations

import importlib.util
import pathlib

import institucional

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
SAIDA = RAIZ / "artes-instagram" / "9-o-cargo-em-disputa"
SITE = "kvgs.github.io/senado-2026"

# O CIANO CLARO E FUNDO, E NAO TEXTO. Medido: #2FB4E4 sobre o papel da #0C6C8F
# sobre o papel da 5,39:1. Texto pede 4,5:1, entao o claro so entra como fundo
# ou sobre tinta escura, onde ele passa de 7:1.
ACENTO = CIANO_FUNDO
ACENTO_NO_ESCURO = CIANO


def contraste(a: str, b: str) -> float:
    def lum(h: str) -> float:
        r, g, bl = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        g_ = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * g_(r) + 0.7152 * g_(g) + 0.0722 * g_(bl)
    l1, l2 = sorted((lum(a), lum(b)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def cabe(t: Tela, txt: str, familia: str, maior: int, menor: int, peso=None,
         larg: int | None = None) -> object:
    """A maior fonte em que o texto ainda cabe numa linha. Nunca corta.

    Nome de tema cortado ("Tecnologia e Inteligencia Artifici") ja saiu numa arte
    deste projeto. Encolher e feio; cortar inventa outra palavra.
    """
    larg = larg or t.larg
    for tam in range(maior, menor - 1, -4):
        fonte = f(familia, tam, peso) if peso else f(familia, tam)
        if t.d.textlength(txt, font=fonte) <= larg:
            return fonte
    raise SystemExit(f"PAROU: '{txt}' nao cabe numa linha nem em {menor}px.")


def rodape_seguro(t: Tela, nota: str, cor: str, cor_nota: str) -> None:
    """Rodape com a nota MEDIDA antes de desenhar.

    O Tela.rodape desenha a URL a esquerda e a nota a direita na MESMA linha. Com
    a nota comprida as duas se escreveram uma por cima da outra, e o resultado
    foi um borrao ilegivel exatamente sobre o endereco do site — a unica coisa
    que a arte precisa que se leia. Colisao de texto e o defeito que o olho ve
    quando ja e tarde: aqui ela vira erro de execucao.
    """
    fm, fn = f("mono", 22), f("mono", 18)
    larg_url = sum(t.d.textlength(c, font=fm) + 1 for c in SITE)
    larg_nota = sum(t.d.textlength(c, font=fn) + 1.6 for c in nota)
    folga = t.larg - (larg_url + larg_nota)
    if folga < 40:
        raise SystemExit(
            f"PAROU: a nota do rodape nao cabe ao lado do endereco.\n"
            f"       nota: {nota!r}\n"
            f"       endereco {larg_url:.0f}px + nota {larg_nota:.0f}px = "
            f"{larg_url + larg_nota:.0f}px em {t.larg}px de linha.\n"
            "       Encurte a nota: as duas coisas se escrevem na mesma linha.")
    t.rodape(SITE, nota, cor, cor_nota)


def bloco_citacao(t: Tela, ft: dict, cor_texto: str, cor_disp: str,
                  cor_linha: str, *, ancorado: bool = True) -> None:
    """A citacao ancorada acima do rodape: aspas, frase da fonte, dispositivo.

    Fica no pe e nao no meio porque e o que se le DEPOIS de entender o slide —
    mas fica em todo slide, porque e o que separa esta arte de um card qualquer
    com um numero grande.
    """
    cit = ft["citacao_literal"]
    fc, fd = f("corpo", 27, 400), f("mono", 19)
    linhas = t.quebra(f"“{cit}”", fc, t.larg)
    if ancorado:
        alto = len(linhas) * int(fc.size * 1.34) + int(fd.size * 1.4) + 30
        t.y = t.base_do_rodape() - alto - 40
    t.regua(cor_linha, 1, cima=0 if ancorado else 46, baixo=22)
    for ln in linhas:
        t.d.text((t.m, t.y), ln, font=fc, fill=cor_texto)
        t.y += int(fc.size * 1.34)
    t.espaco(8)
    t.mono(ft["dispositivo"].upper(), fd, cor_disp, espacamento=2)


def altura_citacao(t: Tela, ft: dict) -> int:
    fc, fd = f("corpo", 27, 400), f("mono", 19)
    n = len(t.quebra(f"“{ft['citacao_literal']}”", fc, t.larg))
    return n * int(fc.size * 1.34) + int(fd.size * 1.4) + 30


def compoe_topo(t: Tela, ft: dict, cores: dict, tam_olho: tuple[int, int],
                tam_frase: int) -> int:
    """Chapeu, olho, frase e resumo. Devolve o y do fim. Nao desenha citacao."""
    t.mono(ft["chapeu"], f("mono", cores["chapeu_tam"]), cores["acento"],
           espacamento=4)
    t.espaco(cores["depois_chapeu"])
    fn = cabe(t, ft["olho"], "display", tam_olho[0], tam_olho[1], peso=700)
    t.d.text((t.m, t.y), ft["olho"], font=fn, fill=cores["olho"])
    t.y += int(fn.size * 1.16)
    t.espaco(26)
    t.texto(ft["frase"], f("corpo", tam_frase, 500), cores["frase"], entre=1.34)
    t.espaco(20)
    t.texto(ft["resumo"], f("corpo", 30, 400), cores["resumo"], entre=1.44)
    return t.y


def desenha_slide(ft: dict, cores: dict, tam_olho, tam_frase, nota: str,
                  ancorar_citacao: bool) -> Tela:
    """Compoe medindo antes.

    O BLOCO DE CIMA E CENTRADO NO ESPACO QUE SOBRA, e nao encostado no topo. Na
    primeira versao tudo comecava em y=96 e a citacao ficava ancorada no pe: cada
    um dos doze slides tinha 450px de buraco no meio. Medir custa desenhar duas
    vezes — a primeira num descarte — e sai barato em imagem estatica.
    """
    topo = 96
    molde = Tela(cores["fundo"])
    molde.y = topo
    fim = compoe_topo(molde, ft, cores, tam_olho, tam_frase)
    alto = fim - topo

    t = Tela(cores["fundo"])
    if ancorar_citacao:
        limite = t.base_do_rodape() - altura_citacao(t, ft) - 40
        # 0.38 e nao 0.5: bloco optidamente centrado fica um pouco acima do meio
        # geometrico, senao a tela parece cair.
        t.y = max(topo, topo + int((limite - topo - alto) * 0.38))
    else:
        t.y = topo
    compoe_topo(t, ft, cores, tam_olho, tam_frase)
    bloco_citacao(t, ft, cores["citacao"], cores["acento"], cores["linha"],
                  ancorado=ancorar_citacao)
    rodape_seguro(t, nota, cores["acento"], cores["resumo"])
    return t


ESCURO = {"fundo": TINTA, "acento": ACENTO_NO_ESCURO, "olho": SOBRE_ESCURO,
          "frase": SOBRE_ESCURO, "resumo": "#C9C1B9", "citacao": "#C9C1B9",
          "linha": LINHA_ESCURA, "chapeu_tam": 24, "depois_chapeu": 40}
CLARO = {"fundo": PAPEL2, "acento": ACENTO, "olho": TINTA, "frase": TINTA,
         "resumo": TINTA2, "citacao": TINTA2, "linha": LINHA,
         "chapeu_tam": 22, "depois_chapeu": 36}


def slide_dinheiro(ft: dict, doc: dict) -> Tela:
    """A capa: fundo escuro e o valor grande. E o unico slide invertido.

    Escuro porque e o gancho do carrossel e precisa se separar do feed; e uma vez
    so, porque doze slides escuros cansam e a citacao fica menos legivel. Aqui a
    citacao NAO desce para o pe: o numero grande pede ar em volta, e nao um vao.
    """
    return desenha_slide(ft, ESCURO, (168, 96), 46, "EMITIDO EM 21/05/2026",
                         ancorar_citacao=False)


def slide_fato(ft: dict) -> Tela:
    return desenha_slide(ft, CLARO, (128, 72), 44,
                         "CÂMARA DOS DEPUTADOS · CEDI", ancorar_citacao=True)


def slide_fecho(n_cand: int, n_est: int) -> Tela:
    """O unico slide que fala do acervo, e por isso o unico com numero medido."""
    t = Tela(PAPEL2)
    t.y = 96
    t.mono("E O QUE CADA UMA DEFENDE?", f("mono", 22), ACENTO, espacamento=4)
    t.espaco(36)
    t.texto("Agora que o cargo está claro, falta o que cada candidatura propõe.",
            f("display", 76, 700), TINTA, entre=1.14)
    t.espaco(34)
    t.texto(f"São {n_cand} candidaturas nos {n_est} estados. No site, o que cada "
            f"uma defende tema por tema — com a fonte, o trecho citado e a data "
            f"ao lado de cada informação.",
            f("corpo", 38, 400), TINTA2, entre=1.44)
    t.espaco(30)
    t.texto("E onde não localizamos nada, está escrito que não localizamos, e "
            "onde procuramos.", f("corpo", 32, 500), TINTA, entre=1.44)

    t.y = t.base_do_rodape() - 150
    t.regua(LINHA, 1, baixo=26)
    t.texto(SITE, f("mono", 40), ACENTO)
    t.espaco(6)
    t.texto("@candidaturasenado", f("mono", 30), TINTA2)
    return t


def escreve_legenda(fatos: list, n_slides: int, n_cand: int, n_est: int) -> None:
    """Legenda gerada, como as outras: o valor e a vigencia saem do JSON."""
    import textwrap
    d = {x["id"]: x for x in fatos}
    dinheiro, doc = d["quanto-ganha"], institucional.documento(
        d["quanto-ganha"]["id_documento"])
    tags = ("#eleições2026 #senado #votoconsciente #dadosabertos #transparência "
            "#educaçãopolítica #constituição #política #brasil")
    itens = [f"▪️ **{x['olho']}** — {x['frase']} ({x['dispositivo']})"
             for x in fatos if x["id"] != "quanto-ganha"]
    corpo = f"""# O cargo em disputa — {n_slides} slides

Gerado por `python gerar_artes_senado.py`.
Abre no valor do subsídio, que é o gancho, e fecha no site.

---

## Legenda

**{dinheiro['olho']} é quanto um senador recebe de subsídio por mês.**

{textwrap.fill(f"Valor com vigência em {doc['vigencia'].lower()}, no demonstrativo do próprio Senado — não em notícia sobre ele. Quem fixa o valor não é o senador: a Constituição dá isso ao Congresso, e manda que seja idêntico ao de deputado federal (art. 49, VII).", 88)}

E o cargo que esse valor paga, ponto por ponto — cada um com o artigo ao lado. 👇

{chr(10).join(textwrap.fill(x, 88) for x in itens)}

{textwrap.fill("Todas as citações destes slides foram conferidas palavra por palavra contra o texto compilado da Constituição publicado pela Câmara dos Deputados e contra o demonstrativo de remuneração do Senado. Os dois arquivos estão no repositório, com hash.", 88)}

🔗 {SITE} — dados abertos, código público.

{tags}

---

## O que ficou de fora, e por quê

**Verba de gabinete, cota parlamentar (CEAPS) e auxílio-moradia.** O Senado
publica os três, mas eles não foram levantados aqui. Cada um tem regra própria e
teto que varia por estado — é onde o número circula errado. O slide do subsídio
diz, escrito, que não os inclui.

**Qualquer frase sobre o que o eleitor sabe ou não sabe.** Seria afirmação sobre
pessoas que não foram medidas. É a mesma regra do carrossel dos dois votos.

**Adjetivo sobre a importância do cargo.** "Por que pesa" está respondido em
quatro competências com artigo ao lado: aprovar ministro do STF, julgar o
presidente por crime de responsabilidade, os três quintos de qualquer emenda, e
suspender lei declarada inconstitucional. Isso é conferível; "o Senado é
poderoso" não é.

## Uma citação que teria saído errada

A frase sobre o STF ia citar o **art. 52, III, "a"**, que diz apenas
"magistrados, nos casos estabelecidos nesta Constituição" — não menciona o
Supremo. A citação certa é o **art. 101, parágrafo único**. Artigo errado no pé
de uma arte é o mesmo defeito do link que apontava para a página errada do DOU.

## Como as citações são conferidas

`python institucional.py` abre os arquivos de `fontes/`, confere cada citação
palavra por palavra e **para com erro** se alguma não estiver lá. Ele distingue
dois casos: frase que não existe na fonte, e frase que só casa sem acento — que
são problemas diferentes. O gerador chama o conferidor antes de desenhar, então
não existe arte com citação não conferida.
"""
    (SAIDA / "LEGENDA.md").write_text(corpo, encoding="utf-8")


def main() -> None:
    import acervo

    # A CONFERENCIA VEM ANTES DO DESENHO, e nao depois. Conferidor que roda
    # depois de a arte existir e conferidor que se esquece de rodar.
    fatos = institucional.conferir()

    est = acervo.ler("estados.json")["estados"]
    n_cand = sum(len(acervo.ler("candidaturas.json", e["uf"])["candidaturas"])
                 for e in est)

    SAIDA.mkdir(parents=True, exist_ok=True)
    for p in SAIDA.glob("*.png"):
        p.unlink()

    print(f"\ncontraste medido:")
    for nome, a, b, minimo in (
            ("olho claro sobre tinta", SOBRE_ESCURO, TINTA, 4.5),
            ("resumo sobre tinta", "#C9C1B9", TINTA, 4.5),
            ("acento no escuro", ACENTO_NO_ESCURO, TINTA, 4.5),
            ("acento no papel", ACENTO, PAPEL2, 4.5),
            ("resumo no papel", TINTA2, PAPEL2, 4.5)):
        r = contraste(a, b)
        if r < minimo:
            raise SystemExit(f"PAROU: {nome} da {r:.2f}:1, abaixo de {minimo}:1.")
        print(f"  {nome:24} {r:5.2f}:1  ok")

    print()
    n = 0
    for ft in fatos:
        n += 1
        if ft["id"] == "quanto-ganha":
            t = slide_dinheiro(ft, institucional.documento(ft["id_documento"]))
        else:
            t = slide_fato(ft)
        nome = f"{n:02d}-{ft['id']}.png"
        t.img.save(SAIDA / nome)
        print(f"  {nome}")
    n += 1
    slide_fecho(n_cand, len(est)).img.save(SAIDA / f"{n:02d}-o-site.png")
    print(f"  {n:02d}-o-site.png")

    escreve_legenda(fatos, n, n_cand, len(est))
    kb = sum(p.stat().st_size for p in SAIDA.glob("*.png")) / 1024
    print(f"\n{n} slides · {kb/1024:.1f} MB · {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
