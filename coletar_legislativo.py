# -*- coding: utf-8 -*-
"""Coleta registro legislativo das APIs oficiais da Camara e do Senado.

POR QUE ESTE SCRIPT EXISTE. Os 32 registros do acervo foram montados a mao, e a
amostra ficou torta: a Simone Tebet aparece com 7 proposicoes cobrindo 2015-2017
de um mandato que foi ate 2022, quando ela tem 40 como autora principal. Salles
tem 16 no acervo e 85 na API. Amostra parcial montada a mao nao e neutra — ela
mostra o que quem montou encontrou primeiro.

O QUE ELE NAO FAZ. Nao escreve em dados/registros_legislativos.json. Escreve num
arquivo de trabalho, para a revisao humana decidir o que entra. Duas razoes:

  1. O TEMA e interpretacao nossa. A ementa e literal e vem da API, mas dizer que
     ela pertence a "Seguranca Publica" e uma leitura. O script SUGERE por
     palavra-chave e marca a confianca; quem decide e a revisao.

  2. Registro ja no acervo carrega conferencia humana (url_conferida_em, _nota,
     temas escolhidos a mao). O merge preserva o que existe, sempre. O script so
     acrescenta.

O QUE ENTRA. So proposicao substantiva: PL, PEC, PLP, PDL (e PLS/PDS no Senado).
Fora ficam REQ, RIC, EMC, EMP, PRL e afins — requerimento e emenda sao movimento
de tramitacao, e nao posicao. Isso derruba Salles de 561 registros na API para
~85, e Derrite de 408 para ~91. O corte e o que separa producao legislativa de
atividade de gabinete.

AUTORIA E MEDIDA JUNTO. A PEC 8/2026 tem 171 signatarios. Ser o 56o de 171 nao e
propor: e assinar. Por isso todo registro guarda ordem_autoria e total_autores,
que o site ja exibe — sem isso, contagem de proposicoes vira placar.

Uso:
    python coletar_legislativo.py            # coleta e escreve o arquivo de trabalho
    python coletar_legislativo.py --resumo   # so mostra o que mudaria
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import date

RAIZ = pathlib.Path(__file__).resolve().parent
DADOS = RAIZ / "dados"
SAIDA = DADOS / "_coleta_legislativa.json"

HOJE = date.today().isoformat()
UA = "senado-2026/1.0 (projeto civico; contato via github.com/kvgs/senado-2026)"

# Proposicao substantiva. Requerimento, emenda e parecer ficam de fora: sao
# movimento de tramitacao, e nao posicao sobre um assunto.
TIPOS_CAMARA = ["PL", "PEC", "PLP", "PDL"]
TIPOS_SENADO = {"PLS", "PL", "PEC", "PLP", "PDL", "PDS"}


# --------------------------------------------------------------------- rede
def buscar(url: str, tentativas: int = 4) -> dict:
    """GET com retentativa. A API da Camara devolve 429 sob rajada, e desistir na
    primeira faria a coleta ficar silenciosamente incompleta — que e o defeito
    que este script existe para corrigir."""
    ultimo = None
    for n in range(tentativas):
        req = urllib.request.Request(url, headers={"accept": "application/json", "User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            ultimo = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 * (n + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            ultimo = e
            time.sleep(2 * (n + 1))
    raise RuntimeError(f"falhou depois de {tentativas} tentativas: {url} ({ultimo})")


def url_responde(url: str) -> bool:
    """Confere que a ficha existe de verdade. Ja aconteceu de 12 registros
    apontarem para a raiz da API em vez da proposicao: link errado e pior que
    link nenhum, porque parece conferido."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


# ------------------------------------------------------------------- temas
# Sugestao por palavra-chave, para a revisao confirmar ou trocar. Nao e
# classificacao automatica: e um primeiro palpite que economiza leitura.
PISTAS = {
    "t1": ["seguranca publica", "policia", "policial", "crime", "penal", "pena ",
           "presidio", "prisional", "arma de fogo", "faccao", "organizacao criminosa",
           "maioridade penal", "violencia domestica", "feminicidio", "homicidio", "roubo",
           "furto", "trafico", "milicia", "delegacia", "guarda municipal"],
    "t2": ["educacao", "escola", "ensino", "professor", "aluno", "estudante",
           "universidade", "creche", "merenda", "fundeb", "alfabetiza", "magisterio",
           "curriculo", "bolsa de estudo"],
    "t3": ["saude", "sus ", "hospital", "medico", "enfermag", "vacina", "medicamento",
           "farmac", "doenca", "epidemi", "sanitar", "atendimento medico", "plano de saude",
           "agente comunitario de saude"],
    "t4": ["tributo", "imposto", "tributar", "economia", "emprego", "trabalho",
           "clt", "salario", "aposentad", "previdenc", "microempre", "empresa",
           "credito", "juros", "orcamento", "fiscal", "renda", "desemprego",
           "servidor publico", "concurso publico", "contrato de trabalho"],
    # Cuidado com pista curta: "trans" casava com TRANSparencia e TRANSmissao, e
    # mandou a PEC do ICMS para Infraestrutura. Pista tem de ser palavra, nao pedaco.
    "t5": ["transporte", "rodovia", "ferrovia", "mobilidade urbana", "aeroporto",
           "porto ", "saneamento", "infraestrutura", "obras publicas", "transito",
           "veiculo", "pedagio", "metroviar", "onibus", "energia eletrica",
           "mobilidade", "transporte coletivo"],
    "t6": ["meio ambiente", "ambiental", "clima", "climat", "floresta", "desmatamento",
           "amazonia", "poluic", "residuos", "carbono", "sustentab", "agrotoxico",
           "recursos hidricos", "unidade de conservacao", "fauna", "licenciamento ambiental"],
    "t7": ["habitac", "moradia", "casa propria", "aluguel", "imovel residencial",
           "regularizacao fundiaria", "favela", "assentamento urbano", "deficit habitacional"],
    "t8": ["tecnologia", "internet", "digital", "dados pessoais", "inteligencia artificial",
           "software", "telecomunica", "rede social", "plataforma digital", "cibern",
           "computac", "inovacao tecnologica"],
    "t9": ["cultura", "cultural", "direitos humanos", "crianca", "adolescente", "idoso",
           "deficiencia", "indigena", "quilombola", "racial", "racismo", "mulher",
           "lgbt", "religi", "patrimonio historico", "artista", "acessibilidade",
           "igualdade de genero"],
    "t10": ["constituicao federal", "processo legislativo", "eleitoral", "partido politico",
            "administracao publica", "ministerio", "agencia reguladora", "federativ",
            "competencia da uniao", "regimento", "codigo civil", "codigo de processo"],
}


def sem_acento(s: str) -> str:
    return unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()


def sugerir_temas(ementa: str) -> tuple[list[str], str]:
    """Devolve (temas sugeridos, confianca). Confianca 'nenhuma' significa que a
    revisao tem de ler a ementa: e melhor admitir que nao sabemos do que enfiar a
    proposicao no tema mais parecido."""
    a = sem_acento(ementa)
    pontos = {t: sum(1 for p in ps if p in a) for t, ps in PISTAS.items()}
    achados = sorted(((n, t) for t, n in pontos.items() if n), reverse=True)
    if not achados:
        return [], "nenhuma"
    topo = achados[0][0]
    escolhidos = [t for n, t in achados if n == topo]
    if len(escolhidos) > 1:
        return escolhidos, "ambigua"
    # Um so tema e mais de uma pista batendo: e o caso confortavel.
    return escolhidos, "boa" if topo >= 2 else "fraca"


# ------------------------------------------------------------------ camara
def coletar_camara(id_dep: str, id_cand: str) -> list[dict]:
    props: dict[int, dict] = {}
    for tipo in TIPOS_CAMARA:
        pagina = 1
        while True:
            u = ("https://dadosabertos.camara.leg.br/api/v2/proposicoes"
                 f"?idDeputadoAutor={id_dep}&siglaTipo={tipo}"
                 f"&itens=100&pagina={pagina}&ordem=DESC&ordenarPor=id")
            j = buscar(u)
            dados = j.get("dados") or []
            for d in dados:
                props[d["id"]] = d
            if len(dados) < 100:
                break
            pagina += 1
            time.sleep(0.3)
    saida = []
    for i, (pid, d) in enumerate(sorted(props.items()), 1):
        aut = buscar(f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{pid}/autores")
        lista = aut.get("dados") or []
        # So parlamentares contam para a ordem: 'proponente' marca quem propos de
        # fato, e a ordem de assinatura separa autor de signatario.
        eu = next((a for a in lista if str(a.get("uri") or "").endswith(f"/{id_dep}")), None)
        temas, conf = sugerir_temas(d.get("ementa") or "")
        saida.append({
            "id_registro": f"{d['siglaTipo'].lower()}-{d['numero']}-{d['ano']}",
            "casa": "camara",
            "tipo": d["siglaTipo"],
            "numero": str(d["numero"]),
            "ano": int(d["ano"]),
            "ementa": (d.get("ementa") or "").strip(),
            "autoria": [{
                "id_candidatura": id_cand,
                "papel": "autor" if (eu or {}).get("proponente") == 1 else "coautor",
                "ordem_autoria": (eu or {}).get("ordemAssinatura"),
                "total_autores": len(lista),
            }],
            "temas": temas,
            "id_documento": "doc-camara-api",
            "url": f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={pid}",
            "id_camara": pid,
            "url_conferida_em": None,
            "url_base": "API da Camara, ementa literal da API",
            "_apresentada_em": (d.get("dataApresentacao") or "")[:10],
            "_confianca_tema": conf,
        })
        if i % 20 == 0:
            print(f"      ... {i}/{len(props)} com autoria resolvida", flush=True)
        time.sleep(0.2)
    return saida


# ------------------------------------------------------------------ senado
def coletar_senado(cod: str, id_cand: str) -> list[dict]:
    j = buscar(f"https://legis.senado.leg.br/dadosabertos/senador/{cod}/autorias.json")
    raiz = ((j.get("MateriasAutoriaParlamentar") or {}).get("Parlamentar") or {})
    autorias = ((raiz.get("Autorias") or {}).get("Autoria")) or []
    if isinstance(autorias, dict):
        autorias = [autorias]
    saida = []
    for a in autorias:
        m = a.get("Materia") or {}
        sigla = m.get("Sigla")
        if sigla not in TIPOS_SENADO:
            continue
        # Autoria principal apenas. Assinar PEC coletiva de 40 senadores nao e
        # iniciativa, e o acervo nao pode apresentar as duas coisas como iguais.
        if a.get("IndicadorAutorPrincipal") != "Sim":
            continue
        temas, conf = sugerir_temas(m.get("Ementa") or "")
        cod_materia = m.get("Codigo")
        saida.append({
            "id_registro": f"sf-{sigla.lower()}-{m.get('Numero')}-{m.get('Ano')}",
            "casa": "senado",
            "tipo": sigla,
            "numero": str(m.get("Numero")),
            "ano": int(m.get("Ano")),
            "id_externo_senado": str(cod_materia),
            "ementa": (m.get("Ementa") or "").strip(),
            "autoria": [{
                "id_candidatura": id_cand,
                "papel": "autor",
                "ordem_autoria": 1,
                "total_autores": None if a.get("IndicadorOutrosAutores") == "Sim" else 1,
            }],
            "temas": temas,
            "id_documento": "doc-senado-api",
            "url": f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{cod_materia}",
            "url_conferida_em": None,
            "url_base": "API do Senado, ementa literal da API",
            "_apresentada_em": (m.get("Data") or "")[:10],
            "_confianca_tema": conf,
        })
    return saida


# -------------------------------------------------------------------- main
def main() -> int:
    so_resumo = "--resumo" in sys.argv

    cands = json.loads((DADOS / "candidaturas.json").read_text(encoding="utf-8"))["candidaturas"]
    atual = json.loads((DADOS / "registros_legislativos.json").read_text(encoding="utf-8"))
    ja_tem = {r["id_registro"] for r in atual["registros"]}

    alvos = []
    for c in cands:
        pl = (c.get("situacao_parlamentar") or [None])[0]
        if pl and pl.get("casa") in ("camara", "senado"):
            alvos.append((c["id_candidatura"], pl))

    # Mandato ENCERRADO nao aparece em situacao_parlamentar, que descreve o
    # presente. Mas mandato encerrado tem registro legislativo igual: a Tebet foi
    # senadora de 2015 a 2022 e o acervo mostra 7 das 40 proposicoes dela.
    # Enquanto for um caso so, mora aqui e a vista, em vez de virar campo novo no
    # cadastro que ficaria vazio para as outras catorze.
    ENCERRADOS = {"sen-sp-2026-tebet": {"casa": "senado", "id_externo": "5527",
                                        "_nota": "senadora por MS, 2015-2022"}}
    ja_alvo = {a for a, _ in alvos}
    for cid, pl in ENCERRADOS.items():
        if cid not in ja_alvo:
            alvos.append((cid, pl))

    novos: list[dict] = []
    for id_cand, pl in alvos:
        print(f"\n>> {id_cand}  ({pl['casa']} {pl.get('id_externo')})", flush=True)
        if pl["casa"] == "camara":
            r = coletar_camara(str(pl["id_externo"]), id_cand)
        else:
            r = coletar_senado(str(pl["id_externo"]), id_cand)
        ineditos = [x for x in r if x["id_registro"] not in ja_tem]
        print(f"   {len(r)} substantivas · {len(ineditos)} ineditas · "
              f"{len(r) - len(ineditos)} ja no acervo (preservadas como estao)", flush=True)
        novos.extend(ineditos)

    # Coautoria entre candidaturas: a mesma proposicao pode ter sido colhida duas
    # vezes, uma por autor. Fundir a autoria e o que o acervo ja fazia a mao.
    fundido: dict[str, dict] = {}
    for r in novos:
        chave = r["id_registro"]
        if chave in fundido:
            fundido[chave]["autoria"].extend(r["autoria"])
        else:
            fundido[chave] = r
    novos = list(fundido.values())

    conf = {}
    for r in novos:
        conf[r["_confianca_tema"]] = conf.get(r["_confianca_tema"], 0) + 1

    print("\n" + "=" * 62)
    print(f"registros ja no acervo, intocados: {len(ja_tem)}")
    print(f"ineditos coletados:                {len(novos)}")
    print("\nsugestao de tema, por confianca:")
    for k in ("boa", "fraca", "ambigua", "nenhuma"):
        if conf.get(k):
            print(f"   {k:9} {conf[k]:4}")
    print("\nNenhum destes entra no site: o tema e leitura nossa e precisa de revisao.")

    if so_resumo:
        print("\n(--resumo: nada foi escrito)")
        return 0

    SAIDA.write_text(json.dumps({
        "_nota": ("Coleta bruta das APIs oficiais, AGUARDANDO REVISAO. Nao e lida pelo "
                  "gerar_site.py. O tema sugerido veio de palavra-chave e precisa de "
                  "confirmacao humana; url_conferida_em fica nulo ate alguem abrir o link."),
        "_coletado_em": HOJE,
        "registros": sorted(novos, key=lambda r: (r["casa"], -r["ano"], r["tipo"], int(r["numero"]))),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nescrito: {SAIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
