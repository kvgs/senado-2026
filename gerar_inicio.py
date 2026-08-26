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

SAIDA: inicio.html, ao lado do index.html de Sao Paulo. Enquanto for so um
estado, publicar a escolha como index.html esconderia o unico conteudo que
existe — a troca acontece quando houver um segundo estado.
"""
import json
import pathlib
import re
import urllib.parse

AQUI = pathlib.Path(__file__).resolve().parent
DADOS = AQUI / "dados"
SAIDA = AQUI / "inicio.html"

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
    return t[i:t.index("}", j) + 1]


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
                # Enquanto Sao Paulo e a unica pagina, ela vive em index.html.
                # Quando houver o segundo estado, o caminho passa a ser uf/.
                alvo = "index.html" if e["uf"] == "SP" else f'{e["uf"].lower()}/'
                itens.append(f'<li><a class="uf" href="{alvo}">{corpo}</a></li>')
        partes.append(f'<div class="regiao"><h3>{regiao}</h3>'
                      f'<ul class="ufs">{"".join(itens)}</ul></div>')
    return "\n  ".join(partes)


def main() -> int:
    est = json.loads((DADOS / "estados.json").read_text(encoding="utf-8"))
    estados = est["estados"]
    ref = json.loads((DADOS / "referencia.json").read_text(encoding="utf-8"))

    email = ((ref.get("contato") or {}).get("email") or "").strip()
    if not email:
        raise SystemExit("dados/referencia.json nao tem contato.email")

    tpl = (AQUI / "_template_inicio.html").read_text(encoding="utf-8")
    # Cada marcador tem de aparecer UMA vez. Mencionar o nome do marcador num
    # comentario do template fez o replace trocar as duas ocorrencias, e o
    # comentario recebeu o CSS inteiro. Barato de conferir, silencioso se nao.
    for marca in ("{{ESTILO_BASE}}", "{{ESTADOS}}", "{{TOTAL_CANDIDATURAS}}"):
        n = tpl.count(marca)
        if n != 1:
            raise SystemExit(f"{marca} aparece {n} vezes no template; esperado 1")
    assunto = urllib.parse.quote("Senado 2026 — feedback")
    html = (tpl
            .replace("{{ESTILO_BASE}}", estilo_base())
            .replace("{{ESTADOS}}", lista_estados(estados))
            .replace("{{TOTAL_CANDIDATURAS}}",
                     str(sum(e["candidaturas_tse"] for e in estados)))
            .replace("{{MAILTO}}", f"mailto:{email}?subject={assunto}")
            .replace("{{EMAIL}}", email))

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
