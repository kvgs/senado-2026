# -*- coding: utf-8 -*-
"""Gera a pagina inicial nacional a partir de _template_inicio.html.

POR QUE SEPARADO DO gerar_site.py. O gerar_site.py monta a pagina de UM estado,
com o acervo daquele estado. Esta pagina nao tem acervo: ela tem a tese (o bloco
da lei, que vale nos 27) e a escolha do estado. Misturar os dois faria o gerador
de estado carregar coisa nacional e vice-versa.

O ESTILO NAO E COPIADO. Os tokens, as fontes e o reset saem do
_template_site.html em tempo de geracao. Duas paletas divergem — uma so, nao.
Se o recorte falhar, este script para em vez de publicar pagina sem estilo.

ESTADO SEM ACERVO NAO E LINK. Um link que abre pagina vazia promete o que nao
existe. A lista diz "ainda nao comecamos", que e a verdade e e informacao.

SAIDA: index.html na raiz. A pagina de cada estado vive em <uf>/index.html, e os
assets (fontes, fotos) ficam na raiz, compartilhados — nao copiados 27 vezes.
"""
import json
import pathlib
import re
import urllib.parse

AQUI = pathlib.Path(__file__).resolve().parent
DADOS = AQUI / "dados"
SAIDA = AQUI / "index.html"

ORDEM_REGIAO = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

ROTULO_ACERVO = {
    "publicado": "{n} candidaturas · acervo publicado",
    "em_construcao": "{n} candidaturas · acervo em construção",
    "nao_comecamos": "{n} candidaturas · ainda não começamos",
}


def estilo_base() -> str:
    """Recorta tokens + fontes + reset do template do estado.

    Marcos: comeca em ':root{' e termina no fim da regra de body. Se qualquer um
    dos dois nao aparecer, o template mudou de forma e o recorte cego produziria
    uma pagina sem estilo — melhor parar."""
    t = (AQUI / "_template_site.html").read_text(encoding="utf-8")
    i = t.find("  :root{")
    j = t.find("-webkit-font-smoothing:antialiased}")
    if i < 0 or j < 0:
        raise SystemExit(
            "nao achei o bloco de estilo base em _template_site.html.\n"
            "Marcos esperados: '  :root{' e '-webkit-font-smoothing:antialiased}'.\n"
            "Se o template mudou, ajuste estilo_base() — nao publique sem estilo."
        )
    css = t[i:t.index("}", j) + 1]
    # A pagina inicial mora NA RAIZ, entao o prefixo de asset e vazio. O marcador
    # vem junto com o CSS recortado do template do estado, que desceu um nivel.
    return css.replace("{{RAIZ}}", "")


def lista_estados(estados: list[dict]) -> str:
    partes = []
    for regiao in ORDEM_REGIAO:
        ufs = [e for e in estados if e["regiao"] == regiao]
        if not ufs:
            continue
        ufs.sort(key=lambda e: e["nome"])
        itens = []
        for e in ufs:
            st = ROTULO_ACERVO[e["acervo"]].format(n=e["candidaturas_tse"])
            corpo = (f'<span class="sigla">{e["uf"]}</span>'
                     f'<span class="txt"><span class="nome">{e["nome"]}</span>'
                     f'<span class="st">{st}</span></span>')
            if e["acervo"] == "nao_comecamos":
                itens.append(f'<li><div class="uf vazio">{corpo}</div></li>')
            else:
                alvo = f'{e["uf"].lower()}/'
                itens.append(f'<li><a class="uf" href="{alvo}">{corpo}</a></li>')
        partes.append(f'<div class="regiao"><h3>{regiao}</h3>'
                      f'<ul class="ufs">{"".join(itens)}</ul></div>')
    return "\n  ".join(partes)


def mapa(estados: list[dict]) -> str:
    """Monta o SVG do mapa a partir de dados/mapa-uf.json.

    Reproduz o viewBox e o transform do IBGE em vez de refazer a aritmetica: as
    coordenadas do path sao latitude*10000 e o transform nega o y. Recalcular
    isso a mao e uma chance de espelhar o pais e nao notar.

    So o que e clicavel entra na arvore de acessibilidade. Estado com acervo vira
    <a> com nome acessivel; os outros ficam fora, porque 27 formas anunciadas uma
    a uma seriam ruido e a lista abaixo diz tudo, melhor.
    """
    m = json.loads((DADOS / "mapa-uf.json").read_text(encoding="utf-8"))
    faltam = sorted({e["uf"] for e in estados} - set(m["paths"]))
    if faltam:
        raise SystemExit(f"mapa-uf.json nao tem os estados: {faltam}")

    formas = []
    for e in sorted(estados, key=lambda x: x["uf"]):
        d = m["paths"][e["uf"]]
        forma = f'<path class="uf-forma" d="{d}"/>'
        if e["acervo"] == "nao_comecamos":
            formas.append(forma)
        else:
            rotulo = f'{e["nome"]} — {e["candidaturas_tse"]} candidaturas'
            formas.append(
                f'<a href="{e["uf"].lower()}/" aria-label="{rotulo}">'
                f'<title>{rotulo}</title>{forma}</a>')

    com = [e for e in estados if e["acervo"] != "nao_comecamos"]
    resumo = (f'Mapa do Brasil. {len(com)} de {len(estados)} unidades da federação '
              f'têm acervo publicado: {", ".join(e["nome"] for e in com)}. '
              'A lista abaixo traz todas, com o estado de cada uma.')

    return (
        f'<div class="mapa">'
        f'<svg viewBox="{m["viewBox"]}" role="group" aria-label="{resumo}">'
        f'<g transform="{m["transform"]}">{"".join(formas)}</g>'
        f'</svg>'
        f'<p class="mapa-leg" aria-hidden="true">'
        f'<span><i class="tem"></i>com acervo publicado</span>'
        f'<span><i class="nao"></i>ainda não começamos</span>'
        f'</p></div>'
    )


def main() -> int:
    est = json.loads((DADOS / "estados.json").read_text(encoding="utf-8"))
    estados = est["estados"]
    ref = json.loads((DADOS / "referencia.json").read_text(encoding="utf-8"))

    email = ((ref.get("contato") or {}).get("email") or "").strip()
    if not email:
        raise SystemExit("dados/referencia.json nao tem contato.email")
    insta = ((ref.get("contato") or {}).get("instagram") or "").strip()
    insta_url = ((ref.get("contato") or {}).get("instagram_url") or "").strip()
    if not insta or not insta_url:
        raise SystemExit("dados/referencia.json nao tem contato.instagram e instagram_url")

    tpl = (AQUI / "_template_inicio.html").read_text(encoding="utf-8")
    # Cada marcador tem de aparecer UMA vez. Mencionar o nome do marcador num
    # comentario do template fez o replace trocar as duas ocorrencias, e o
    # comentario recebeu o CSS inteiro. Barato de conferir, silencioso se nao.
    for marca in ("{{ESTILO_BASE}}", "{{ESTADOS}}", "{{TOTAL_CANDIDATURAS}}", "{{MAPA}}"):
        n = tpl.count(marca)
        if n != 1:
            raise SystemExit(f"{marca} aparece {n} vezes no template; esperado 1")
    assunto = urllib.parse.quote("Senado 2026 — feedback")
    html = (tpl
            .replace("{{ESTILO_BASE}}", estilo_base())
            .replace("{{MAPA}}", mapa(estados))
            .replace("{{ESTADOS}}", lista_estados(estados))
            .replace("{{TOTAL_CANDIDATURAS}}",
                     str(sum(e["candidaturas_tse"] for e in estados)))
            .replace("{{MAILTO}}", f"mailto:{email}?subject={assunto}")
            .replace("{{EMAIL}}", email)
            .replace("{{INSTAGRAM_URL}}", insta_url)
            .replace("{{INSTAGRAM}}", insta))

    faltou = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if faltou:
        raise SystemExit(f"marcador nao substituido: {sorted(set(faltou))}")

    SAIDA.write_text(html, encoding="utf-8", newline="\n")
    pub = [e["uf"] for e in estados if e["acervo"] != "nao_comecamos"]
    print(f"{SAIDA.name}: {len(estados)} unidades, "
          f"{sum(e['candidaturas_tse'] for e in estados)} candidaturas")
    print(f"  com pagina: {', '.join(pub) or 'nenhuma'}")
    print(f"  sem acervo, mostrados sem link: {len(estados) - len(pub)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
