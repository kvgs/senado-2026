# -*- coding: utf-8 -*-
"""Tela local para revisar as posicoes do acervo, uma a uma.

POR QUE UMA TELA E NAO UMA LISTA
Revisar num editor de JSON e uma tarefa que se abandona no item 15. Aqui cada
item aparece sozinho, com o link da fonte a um clique e tres botoes. Cada decisao
e gravada na hora em dados/<uf>/posicoes.json — fechar a janela no meio nao
perde nada.

O ACERVO INTEIRO, E NAO UM ESTADO
Sem --uf a tela abre os 27 estados juntos. Ela nasceu presa a um estado porque o
acervo tinha um so; hoje sao 27, e revisar estado por estado significa dar a Sao
Paulo uma atencao que o Acre nunca teria.

E OS ITENS VEM INTERCALADOS
Dentro de cada faixa de risco, a fila alterna estado e candidatura a cada item.
Ler quinze linhas seguidas da mesma pessoa cria expectativa: a decima quinta e
julgada pelo que as catorze anteriores pareciam, e nao pelo que a fonte diz.
Alternar quebra isso, e de quebra espalha a revisao pelo pais em vez de deixar
um estado revisado e vinte e seis intocados.

A ORDEM E POR RISCO, NAO POR ID
Primeiro o que veio de fonte secundaria e o que a IA marcou como conferencia
fraca; por ultimo os trechos lidos direto de PDF registrado no TSE. Se voce
parar na metade, terá revisado a metade que importa.

O QUE CADA BOTAO FAZ
  Confere   -> revisado_por_humano vira true. E a unica coisa neste projeto que
               marca uma informacao como conferida por gente, e por isso so
               voce pode aperta-lo.
  Corrigir  -> fica marcado como problema, com a sua nota, e NAO vira revisado.
  Remover   -> marcado para remocao, mas NADA e apagado aqui: apagar dado com um
               clique e como se perde acervo.

USO
    python revisar.py              # os 27 estados, intercalados
    python revisar.py --uf PE      # so Pernambuco
    (abre http://localhost:8765 no navegador)
"""
import collections
import http.server
import json
import pathlib
import shutil
import socketserver
import threading
import webbrowser
from datetime import date
from urllib.parse import urlparse

RAIZ = pathlib.Path(__file__).resolve().parent
import argparse as _argparse

import acervo
import conferir_citacoes as cc

# SEM --uf, TODOS OS ESTADOS. O padrao antigo era um estado so, herdado de quando
# o acervo tinha um. Revisar por estado nao e neutro: quem comeca por Sao Paulo
# revisa Sao Paulo e para, e os outros 26 ficam com o selo de nao revisado para
# sempre. --uf continua existindo para quando o alvo for mesmo um estado.
_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--uf", default=None)
_ap.add_argument("--quem", default=None)
# Filtrar por candidatura contraria a regra da intercalacao — que existe para nao
# julgar quinze linhas seguidas da mesma pessoa. Existe assim mesmo porque ha um
# caso em que o alvo E uma pessoa: quando material novo dela acabou de entrar e a
# curadoria quer conferir aquilo, e nao o acervo inteiro.
_ap.add_argument("--candidatura", default=None,
                 help="numero de urna ou pedaco do nome; so revisa essa candidatura")
_args = _ap.parse_known_args()[0]
_UF = _args.uf.upper() if _args.uf else None

NACIONAL = acervo.NACIONAL         # dados/ — referencia, estados, mapa
UFS = ([_UF] if _UF else
       [e["uf"] for e in json.loads((NACIONAL / "estados.json").read_text(encoding="utf-8"))["estados"]])
NOME_UF = {e["uf"]: e["nome"] for e in
           json.loads((NACIONAL / "estados.json").read_text(encoding="utf-8"))["estados"]}
for _u in UFS:
    acervo.exige(_u)               # falha aqui, e nao no meio da revisao
QUEM = acervo.quem(_args.quem)
ALVO = (_args.candidatura or "").strip().lower()
PORTA = 8765

ORDEM_FORCA = {"baixa": 0, "media": 1, "alta": 2}
ORDEM_FONTE = {"secundaria": 0, "declaracao_candidato": 1, "registro_legislativo": 2, "oficial": 3}

# Registro de ausencia (C e D) nao tem selo de fonte, e por isso caia sem
# instrucao nenhuma. E justamente nele que a instrucao importa mais: o que se
# confere e a lista de fontes, nao um trecho.
O_QUE_CONFERIR_AUSENCIA = (
    "Aqui nao ha trecho a conferir — a linha diz que NAO ha proposta. O que voce "
    "confere e a LISTA DE FONTES abaixo: ela cobre o que a candidatura publicou? "
    "Se existir site, perfil ou documento que nao esta nessa lista, esta linha "
    "afirma demais e deve ir para Corrigir. Foi o que aconteceu com o Gladson "
    "Cameli: sete linhas diziam “nao localizamos” e o site dele tinha "
    "pagina de proposta para cinco daqueles temas.")

O_QUE_CONFERIR = {
    "secundaria": "Abra a fonte e confira duas coisas: a matéria diz isso mesmo, e atribui "
                  "à candidatura certa? Fonte secundária é onde a atribuição se perde.",
    "declaracao_candidato": "Abra o site e confira se o texto ainda está lá. Site de campanha "
                            "muda sem aviso, e a data de referência tem de bater com o que se vê hoje.",
    "registro_legislativo": "Confira o número e o ano da proposição, e se a autoria é mesmo desta "
                            "candidatura — em projeto com muitos autores, ser um deles não é ser o autor.",
    # O estado entra por formatacao: a frase dizia "vale para Sao Paulo" fixo, e
    # seguiu dizendo isso depois que o acervo virou 27 estados. Instrucao errada
    # e pior que instrucao nenhuma — manda conferir a coisa errada.
    "oficial": "Aqui a pergunta não é se o assunto está no documento — costuma estar. É se a "
               "REDAÇÃO bate. Paráfrase escorrega: já houve um caso em que 'controle estatal dos "
               "preços' virou 'congelamento de preços', que é outra política. Confira palavra a "
               "palavra, e confira se o documento vale para {estado} — programa registrado por uma "
               "candidatura de outro estado não vale para esta.",
}


def carregar(uf):
    d = acervo.de(uf)
    pos = json.loads((d / "posicoes.json").read_text(encoding="utf-8"))
    docs = json.loads((d / "documentos.json").read_text(encoding="utf-8"))
    cand = json.loads((d / "candidaturas.json").read_text(encoding="utf-8"))
    ref = json.loads((NACIONAL / "referencia.json").read_text(encoding="utf-8"))
    return pos, docs, cand, ref


def lista(x, chave):
    return x[chave] if isinstance(x, dict) else x


def fonte_guardada(uf, r, doc, prog, sites):
    """O texto da fonte, quando o repositorio o guarda.

    A tela mostrava a citacao e um LINK. Conferir exigia abrir um PDF no TSE e
    procurar a frase a mao — e 23 citacoes que nao sao citacao passaram por esta
    tela aprovadas. Onde o texto esta no repositorio, ele aparece ao lado.
    """
    idd = r.get("id_documento") or ""
    sigla = cc.ALIAS.get(idd) or (idd[len("doc-programa-nacional-"):]
                                  if idd.startswith("doc-programa-nacional-") else None)
    if sigla:
        return prog.get(sigla) or prog.get(cc.nu(sigla))
    if doc.get("tipo") == "site_de_candidatura":
        return sites.get(r.get("atribuido_a_id"))
    return cc.arquivo_do_documento(doc)


def itens_de(uf):
    pos, docs, cand, ref = carregar(uf)
    prog, sites = cc.fontes_de_partido(), cc.texto_de_site(uf)
    dm = {d["id_documento"]: d for d in lista(docs, "documentos")}
    cm = {c["id_candidatura"]: c for c in lista(cand, "candidaturas")}
    pm = {p["id_partido"]: p for p in ref["partidos"]}
    tm = {t["id_tema"]: t["nome"] for t in ref["temas"]}

    itens = []
    for r in lista(pos, "posicoes"):
        conf = r.get("conferido_por_ia") or {}
        doc = dm.get(r.get("id_documento"), {})
        alvo = r.get("id_candidatura_contexto") or r.get("atribuido_a_id")
        c = cm.get(alvo, {})
        de_partido = r.get("atribuido_a_tipo") == "partido"
        cit = r.get("citacao_literal") or ""
        src = fonte_guardada(uf, r, doc, prog, sites)
        if not cit:
            sit, ctx = "sem_citacao", None
        elif src is None:
            sit, ctx = "fonte_nao_guardada", None
        else:
            sit = cc.situacao(cit, src)
            ctx = cc.contexto_na_fonte(cit, src)
        itens.append({
            "situacao_citacao": sit,
            "contexto": ctx,
            "escopo_busca": r.get("escopo_da_busca") or "",
            "busca_em": r.get("busca_realizada_em") or "",
            "id": r["id_posicao"],
            "uf": uf,
            "uf_nome": NOME_UF.get(uf, uf),
            "candidatura": (c.get("pessoa", {}).get("nome_urna") or alvo or "?"),
            "numero": c.get("numero_urna", ""),
            "tema": tm.get(r.get("id_tema"), r.get("id_tema", "")),
            "estado": r.get("estado_cobertura"),
            "de_partido": de_partido,
            "partido": pm.get(r.get("atribuido_a_id"), {}).get("sigla", "") if de_partido else "",
            "nivel_fonte": r.get("nivel_fonte"),
            "texto": r.get("texto") or "",
            "citacao": r.get("citacao_literal") or "",
            "escopo": r.get("escopo") or "",
            "data_referencia": r.get("data_referencia") or "",
            "fonte_titulo": doc.get("titulo", "fonte não registrada"),
            "fonte_url": r.get("url_especifica") or doc.get("url", ""),
            "fonte_url_documento": doc.get("url", ""),
            "pagina_na_fonte": r.get("_pagina_no_dou"),
            "fonte_local": doc.get("arquivo_local", ""),
            "forca": conf.get("forca", ""),
            "base": conf.get("base", ""),
            "ressalva": conf.get("ressalva", ""),
            "o_que_conferir": (
                O_QUE_CONFERIR_AUSENCIA
                if r.get("estado_cobertura") in ("C", "D")
                else O_QUE_CONFERIR.get(r.get("nivel_fonte"), "")
                     .replace("{estado}", NOME_UF.get(uf, uf))),
            "revisado": bool(r.get("revisado_por_humano")),
            "revisao": r.get("revisao") or {},
        })
    return itens


def so_a_candidatura(itens):
    if not ALVO:
        return itens
    fica = [x for x in itens
            if ALVO == str(x["numero"]).lower() or ALVO in x["candidatura"].lower()]
    if not fica:
        raise SystemExit(f"nenhuma candidatura casa com {ALVO!r} em {', '.join(UFS)}")
    return fica


def faixa_de_risco(x):
    """A ordem que existia antes, sem o id: dentro de cada faixa, primeiro o que
    NAO tem citacao literal. Hipotese, nao fato medido: parafrase sem trecho
    citado nao tem ancora, e foi assim que "controle estatal dos precos" virou
    "congelamento de precos" numa posicao do programa da UP."""
    return (bool(x["revisado"] or x["revisao"]),
            ORDEM_FORCA.get(x["forca"], 9),
            ORDEM_FONTE.get(x["nivel_fonte"], 9),
            bool(x["citacao"].strip()))


def intercalar(itens):
    """Alterna estado E candidatura a cada item, sem sair da faixa de risco.

    Sempre puxa do grupo (estado, candidatura) que tem MAIS itens na fila. E o
    que evita o final ruim: se os pequenos saem primeiro, sobram vinte itens da
    mesma pessoa no fim, exatamente a leitura em bloco que a intercalacao existe
    para impedir. Quando nao houver grupo que sirva, repete — repetir e melhor
    que travar."""
    grupos = collections.OrderedDict()
    for x in itens:
        grupos.setdefault((x["uf"], x["candidatura"]), []).append(x)
    saida, ultimo_uf, ultima_cand = [], None, None
    while grupos:
        ordenados = sorted(grupos.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        escolhido = next((k for k, _ in ordenados
                          if k[0] != ultimo_uf and k[1] != ultima_cand), None)
        if escolhido is None:                       # so um estado na fila
            escolhido = next((k for k, _ in ordenados if k[1] != ultima_cand), None)
        if escolhido is None:                       # so uma candidatura na fila
            escolhido = ordenados[0][0]
        saida.append(grupos[escolhido].pop(0))
        ultimo_uf, ultima_cand = escolhido
        if not grupos[escolhido]:
            del grupos[escolhido]
    return saida


def montar_itens():
    itens = []
    for uf in UFS:
        itens.extend(itens_de(uf))
    itens = so_a_candidatura(itens)
    # Intercala DENTRO de cada faixa de risco, e nunca entre faixas: misturar as
    # faixas daria variedade e perderia a garantia de que parar na metade deixa
    # revisada a metade que importa.
    porfaixa = collections.OrderedDict()
    for x in sorted(itens, key=lambda x: (faixa_de_risco(x), x["id"])):
        porfaixa.setdefault(faixa_de_risco(x), []).append(x)
    saida = []
    for grupo in porfaixa.values():
        saida.extend(intercalar(grupo))
    return saida


def gravar(uf, id_posicao, decisao, nota, citacao=""):
    # O ESTADO VEM DO ITEM, e nao de uma variavel global. Com um acervo so, errar
    # o arquivo era impossivel; com 27, escrever a decisao no estado errado seria
    # silencioso — marcaria como revisada uma linha que ninguem leu.
    if uf not in UFS:
        return False
    caminho = acervo.de(uf) / "posicoes.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    alvo = lista(dados, "posicoes")
    achou = False
    for r in alvo:
        if r["id_posicao"] != id_posicao:
            continue
        achou = True
        # QUEM decidiu, e nao so QUE alguem decidiu. Com uma pessoa "humano" e
        # "ela" eram a mesma coisa; com colaboradores, sem isto nao da para
        # revisar de novo so o que uma pessoa fez.
        # A HISTORIA NAO E SOBRESCRITA. Antes, esta linha trocava o objeto
        # revisao inteiro — e levava junto tudo o que explicava como a linha
        # chegou ate aqui: uma decisao anterior guardada, o motivo de uma
        # reabertura. Quatro posicoes do programa do PL foram reabertas porque a
        # fonte nao abria, a curadoria as decidiu na tela, e o registro do POR QUE
        # elas voltaram a fila desapareceu no mesmo clique. Fica so a decisao
        # final, sem como auditar o caminho.
        antes = r.get("revisao") or {}
        historia = list(antes.get("_antes", []))
        if antes.get("resultado") or antes.get("_porque_reaberta"):
            historia.append({k: v for k, v in antes.items() if k != "_antes"})
        r["revisao"] = {"em": date.today().isoformat(), "resultado": decisao,
                        "nota": nota or "", "por_quem": QUEM}
        if historia:
            r["revisao"]["_antes"] = historia
        # A frase colada na revisao vira a citacao literal do acervo: a revisao
        # nao so aprova, ela preenche a ancora que faltava. Guarda tambem a marca
        # de que veio da revisao humana, e nao da extracao automatica.
        # UMA LINHA DE AUSENCIA NUNCA RECEBE CITACAO, venha o que vier da tela.
        # Registro C e D afirmam que NAO ha proposta; escrever qualquer coisa no
        # campo da citacao transforma o texto em trecho de fonte, e a pagina o
        # publica entre aspas. Foi o que aconteceu: a curadoria escreveu "Nao ha
        # frase a ser conferida" na caixa que pedia a frase da fonte, e a pagina do
        # Acre passou a citar isso como se o documento dissesse.
        if citacao and citacao.strip():
            if r.get("estado_cobertura") in ("C", "D"):
                r["revisao"]["_texto_recusado_no_campo_citacao"] = citacao.strip()
            else:
                r["citacao_literal"] = citacao.strip()
                r["revisao"]["citacao_conferida_na_fonte"] = True
        # So "confere" marca como revisado por humano. As outras decisoes sao
        # registro de problema: um item com problema conhecido nao esta revisado,
        # esta condenado.
        r["revisado_por_humano"] = (decisao == "confere")
        if decisao == "confere":
            r["revisado_por"] = QUEM
    if not achou:
        return False
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    return True


# String CRUA. Sem o r, o Python interpreta as sequencias de escape que
# existem dentro do JavaScript e insere quebras de linha reais no meio de
# literais de string. O script inteiro morre e a pagina abre em branco, sem
# erro nenhum do lado do Python.
PAGINA = r"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Revisao do acervo</title>
<style>
:root{--ground:#F7F8F7;--surface:#fff;--surface-2:#EDEFED;--ink:#171A18;--ink-2:#3A403C;
  --muted:#5C645F;--rule:#D6DBD7;--rule-forte:#828A84;--ok:#1F6B41;--erro:#A32C20;--aviso:#7A5600}
@media(prefers-color-scheme:dark){:root{--ground:#0F1210;--surface:#171B18;--surface-2:#212621;
  --ink:#EDF0EE;--ink-2:#C3CAC5;--muted:#9AA29C;--rule:#2A302C;--rule-forte:#6E766F;
  --ok:#6FC091;--erro:#F0897C;--aviso:#E0B45E}}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);padding:22px 16px 90px;
  font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:760px;margin:0 auto}
h1{font-size:1.25rem;margin:0 0 3px}
.sub{color:var(--muted);font-size:.88rem;margin:0 0 18px}
.barra{height:7px;background:var(--surface-2);border-radius:99px;overflow:hidden;margin-bottom:6px}
.barra i{display:block;height:100%;background:var(--ok);width:0}
.cartao{background:var(--surface);border:1px solid var(--rule);border-radius:7px;padding:20px;
  margin-top:16px}
.topo{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:baseline;
  padding-bottom:12px;border-bottom:1px solid var(--rule);margin-bottom:14px}
.topo h2{font-size:1.05rem;margin:0}
.tag{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;
  padding:2px 7px;border-radius:3px;border:1px solid var(--rule-forte);color:var(--muted)}
.tag.baixa{color:var(--erro);border-color:var(--erro)}
.tag.media{color:var(--aviso);border-color:var(--aviso)}
/* A sigla do estado e o primeiro dado do cartao, e nao mais um selo entre os
   outros: a fila alterna estados a cada item, e quem revisa precisa saber ONDE
   esta antes de ler a frase. display:block porque span e inline e ignoraria a
   altura — ja aconteceu de uma barra vazar do cartao por isso. */
.uf{display:block;font:700 .8rem/1 ui-monospace,monospace;letter-spacing:.08em;
  padding:6px 9px;border-radius:4px;background:var(--surface-2);
  border:1px solid var(--rule-forte);color:var(--ink-2);align-self:center}
.nafonte{margin:10px 0 6px;padding:10px 12px;border-radius:8px;font-size:.9rem}
.nafonte.ok{background:#EAF6EE;border:1px solid #BEDFC8}
.nafonte.aviso{background:#FDF4E3;border:1px solid #EBD9A8}
.nafonte.erro{background:#FCEBEA;border:1px solid #EDC3BF}
.nafonte.neutro{background:#F2F2F0;border:1px solid #DDD}
.nafonte .selo{margin:0;font-weight:600}
.nafonte .ctx{margin:8px 0 0;color:#3A3A38;line-height:1.55;max-height:11em;overflow:auto}
.nafonte mark{background:#FFE08A;padding:1px 0}
blockquote{margin:0 0 12px;padding:11px 15px;background:var(--surface-2);
  border-left:4px solid var(--rule-forte);border-radius:0 4px 4px 0;font-size:1.02rem}
.txt{margin:0 0 12px}
.meta{font-size:.86rem;color:var(--muted);display:flex;flex-direction:column;gap:4px;margin-top:12px}
.confira{margin-top:14px;padding:11px 14px;border:1px dashed var(--rule-forte);border-radius:5px;
  font-size:.9rem;color:var(--ink-2)}
.acoes{display:flex;flex-wrap:wrap;gap:9px;margin-top:18px}
button{font:inherit;font-weight:600;padding:10px 16px;border-radius:5px;cursor:pointer;
  border:1px solid var(--rule-forte);background:var(--surface);color:var(--ink)}
button.ok{border-color:var(--ok);background:var(--ok);color:var(--ground)}
button.err{border-color:var(--erro);color:var(--erro)}
button:focus-visible,a:focus-visible,textarea:focus-visible{outline:3px solid var(--ok);outline-offset:2px}
a{color:var(--ok)}
textarea{width:100%;font:inherit;font-size:.94rem;padding:9px 11px;margin-top:10px;
  border:1px solid var(--rule-forte);border-radius:5px;background:var(--surface);color:var(--ink)}
.atalho{font-size:.78rem;color:var(--muted);margin-top:12px}
.fim{text-align:center;padding:40px 0;color:var(--muted)}
</style></head><body><main>
<h1>Revisao do acervo</h1>
<p class="sub" id="progresso"></p>
<div class="barra"><i id="preenche"></i></div>
<div id="alvo"></div>
</main>
<script>
var ITENS=[], i=0;
function esc(s){var d=document.createElement('div');d.textContent=s==null?'':String(s);return d.innerHTML;}

function progresso(){
  var feitos=0, ufs={}, ufsFeitos={};
  ITENS.forEach(function(x){
    ufs[x.uf]=1;
    if(x.revisado||x.revisao&&x.revisao.resultado){ feitos++; ufsFeitos[x.uf]=1; }
  });
  /* Conta ESTADOS ALCANCADOS, e nao so linhas. E o numero que diz se a revisao
     esta espalhada ou empilhada num canto — que e a coisa que a intercalacao
     existe para resolver, e que uma barra de progresso sozinha esconderia. */
  document.getElementById('progresso').textContent =
    feitos+' de '+ITENS.length+' decididas · restam '+(ITENS.length-feitos)+
    ' · '+Object.keys(ufsFeitos).length+' de '+Object.keys(ufs).length+' estados alcancados';
  document.getElementById('preenche').style.width=(feitos/ITENS.length*100)+'%';
}

/* O TEXTO DA FONTE AO LADO DA CITACAO.
   Antes daqui, conferir uma citacao era abrir um PDF no TSE e procurar a frase.
   Vinte e tres citacoes que NAO sao citacao passaram por esta tela aprovadas — nao
   por desatencao de quem revisou, mas porque a tela nao dava como conferir. Onde o
   repositorio guarda o texto da fonte, ele aparece com o trecho marcado e o
   paragrafo em volta.

   O selo NAO decide nada: "confere" aqui quer dizer que a frase existe na fonte,
   e nao que ela representa o que a candidatura defende. Essa segunda pergunta
   continua sendo sua, e e a unica que a maquina nao pode responder. */
var ROTULO = {
  literal:                 ['ok',   'A frase existe na fonte, palavra por palavra.'],
  literal_quebra_de_linha: ['ok',   'A frase existe na fonte. Difere so onde o documento quebra a linha.'],
  sem_acento:              ['aviso','Existe na fonte, mas transcrita sem acento. Rode conferir_citacoes.py --corrigir-grafia.'],
  difere_em_caixa:         ['aviso','Existe na fonte com outra caixa de letra. Pode ser a fonte que esta errada — decida voce.'],
  nao_achei:               ['erro', 'NAO ACHEI esta frase na fonte guardada. O campo pode ter sintese em vez de citacao — e a tela do site mostra esse campo entre aspas.'],
  sem_citacao:             ['erro', 'Sem citacao literal: nao ha trecho para conferir.'],
  fonte_nao_guardada:      ['neutro','O repositorio nao guarda o texto desta fonte, entao a conferencia nao pode ser feita aqui. Abra o link.']
};

function naFonte(it){
  var r = ROTULO[it.situacao_citacao] || ROTULO.fonte_nao_guardada;
  var h = '<div class="nafonte '+r[0]+'"><p class="selo">'+esc(r[1])+'</p>';
  if(it.contexto){
    h += '<p class="ctx">'+(it.contexto.cortado_no_inicio?'(...) ':'')+
         esc(it.contexto.antes)+'<mark>'+esc(it.contexto.trecho)+'</mark>'+
         esc(it.contexto.depois)+(it.contexto.cortado_no_fim?' (...)':'')+'</p>';
  }
  return h+'</div>';
}

function desenhar(){
  progresso();
  var alvo=document.getElementById('alvo');
  var pend=ITENS.filter(function(x){return !(x.revisado||x.revisao&&x.revisao.resultado);});
  if(!pend.length){ alvo.innerHTML='<p class="fim">Tudo decidido. Rode <code>python validar.py</code> e '+
    '<code>python gerar_site.py</code> para publicar.</p>'; return; }
  var it=pend[0];
  alvo.innerHTML='<div class="cartao"><div class="topo">'+
    '<span class="uf">'+esc(it.uf)+'</span>'+
    '<h2>'+esc(it.numero)+' · '+esc(it.candidatura)+'</h2>'+
    '<span class="tag">'+esc(it.tema)+'</span>'+
    '<span class="tag '+esc(it.forca)+'">conferencia '+esc(it.forca)+'</span>'+
    '<span class="tag">'+esc(it.nivel_fonte)+'</span>'+
    (it.de_partido?'<span class="tag">programa do '+esc(it.partido)+'</span>':'')+
    '</div>'+
    (it.citacao?'<blockquote>'+esc(it.citacao)+'</blockquote>':'<p class="confira" style="border-style:solid"><strong>Sem citação literal.</strong> Esta linha é paráfrase da fonte, sem trecho citado que a ancore — é onde a redação costuma escorregar. Compare com o documento palavra a palavra.</p>')+
    naFonte(it)+
    (it.texto?'<p class="txt">'+esc(it.texto)+'</p>':'')+
    /* O ESCOPO DA BUSCA E O QUE SE REVISA num registro de ausencia. Sem ele na
       tela, a decisao seria sobre uma frase ("nao localizamos") sem o unico dado
       que permite julga-la: onde se procurou. */
    (it.escopo_busca
      ? '<div class="nafonte neutro"><p class="selo">Onde se procurou'+
        (it.busca_em?' (busca em '+esc(it.busca_em)+')':'')+'</p>'+
        '<p class="ctx">'+esc(it.escopo_busca)+'</p></div>'
      : '')+
    (it.escopo?'<p class="txt"><strong>Escopo:</strong> '+esc(it.escopo)+'</p>':'')+
    '<div class="meta">'+
      '<span>Fonte: '+(it.fonte_url?'<a href="'+esc(it.fonte_url)+'" target="_blank" rel="noopener">'+
        esc(it.fonte_titulo)+'</a>':esc(it.fonte_titulo))+
        (it.pagina_na_fonte?' <b>— pagina '+esc(it.pagina_na_fonte)+
          '</b>, que e onde ESTE trecho esta':'')+'</span>'+
      (it.fonte_local?'<span>Arquivo local: '+esc(it.fonte_local)+'</span>':'')+
      '<span>Data de referencia: '+esc(it.data_referencia)+'</span>'+
      (it.base?'<span>Base da conferencia por IA: '+esc(it.base)+'</span>':'')+
      (it.ressalva?'<span><strong>Ressalva anotada:</strong> '+esc(it.ressalva)+'</span>':'')+
    '</div>'+
    '<p class="confira">'+esc(it.o_que_conferir)+'</p>'+
    /* EM LINHA DE AUSENCIA A CAIXA DA CITACAO NAO EXISTE.
       Ela existia, com o rotulo "Cole a frase da fonte que sustenta isto" — a
       unica caixa grande da tela. Numa linha que diz que NAO ha proposta, essa
       pergunta nao tem resposta possivel, e a curadoria respondeu o obvio: "Nao ha
       frase a ser conferida". O servidor gravou isso no campo da citacao, e a
       pagina do Acre publicou a frase entre aspas como se fosse trecho do
       documento. O campo que nao deve ser preenchido nao pode estar na tela. */
    ((it.estado==='C'||it.estado==='D')
      ? '<p style="font-size:.84rem;color:var(--muted);margin-top:14px">'+
        'Esta linha nao tem citacao, e nao deve ter: ela afirma que NAO ha proposta. '+
        'O que se confere aqui e a lista de fontes acima. Se algo estiver faltando '+
        'nela, use Corrigir e escreva o que falta na nota.</p>'
      : it.citacao
      ? '<label for="cit" style="display:block;font-size:.84rem;color:var(--muted);margin-top:14px">'+
        'Citacao errada? Cole a correta (opcional)</label>'+
        '<textarea id="cit" rows="2"></textarea>'
      : '<label for="cit" style="display:block;font-size:.84rem;font-weight:600;margin-top:14px">'+
        'Cole a frase da fonte que sustenta isto</label>'+
        '<p style="font-size:.83rem;color:var(--muted);margin:2px 0 6px">Obrigatoria para confirmar. '+
        'Ela vira a citacao literal desta linha no acervo — e o que impede a parafrase de escorregar '+
        'depois.</p>'+
        '<textarea id="cit" rows="3"></textarea>')+
    '<textarea id="nota" rows="2" placeholder="Nota (obrigatoria se houver problema)"></textarea>'+
    '<div class="acoes">'+
      '<button class="ok" data-d="confere">Confere (1)</button>'+
      '<button class="err" data-d="corrigir">Tem erro (2)</button>'+
      '<button data-d="remover">Nao deveria estar aqui (3)</button>'+
      '<button data-d="pular">Pular</button>'+
    '</div>'+
    '<p class="atalho">Teclas 1, 2 e 3. A decisao e gravada na hora em dados/'+
      esc(it.uf.toLowerCase())+'/posicoes.json.</p>'+
    '</div>';
}

function decidir(d){
  var pend=ITENS.filter(function(x){return !(x.revisado||x.revisao&&x.revisao.resultado);});
  if(!pend.length) return;
  var it=pend[0];
  if(d==='pular'){ ITENS.splice(ITENS.indexOf(it),1); ITENS.push(it); desenhar(); return; }
  var nota=(document.getElementById('nota')||{}).value||'';
  var cit=(document.getElementById('cit')||{}).value||'';
  if(d!=='confere' && !nota.trim()){
    alert('Escreva o que esta errado. Problema sem descricao nao da para consertar depois.');
    document.getElementById('nota').focus(); return;
  }
  /* Confirmar linha sem ancora exige a frase. Nao e burocracia: foi assim que
     "controle estatal dos precos" virou "congelamento de precos" sem ninguem ver.

     MAS A TRAVA NAO VALE PARA AUSENCIA. Registro C e D nao tem trecho a citar —
     eles dizem que NAO ha proposta, e o que a revisao confere neles e o escopo da
     busca. Exigir citacao aqui impediria de aprovar exatamente o registro que
     afirma que nada foi achado, e deixaria a ausencia fora da revisao para
     sempre. */
  var ausencia = (it.estado==='C' || it.estado==='D');
  if(d==='confere' && !ausencia && !it.citacao && !cit.trim()){
    alert('Cole a frase da fonte que sustenta esta linha.\n\n'+
          'Sem trecho citado nao ha como conferir depois se a redacao escorregou.');
    document.getElementById('cit').focus(); return;
  }
  fetch('/api/decidir',{method:'POST',headers:{'content-type':'application/json'},
    body:JSON.stringify({uf:it.uf,id:it.id,decisao:d,nota:nota,citacao:cit})})
    .then(function(r){return r.json();})
    .then(function(r){
      if(r.erro){ alert(r.erro); return; }
      it.revisado=(d==='confere'); it.revisao={resultado:d,nota:nota};
      if(cit.trim()) it.citacao=cit.trim();
      desenhar();
    });
}

document.addEventListener('click',function(e){
  var b=e.target.closest('button'); if(b&&b.dataset.d) decidir(b.dataset.d);
});
document.addEventListener('keydown',function(e){
  if(e.target.tagName==='TEXTAREA') return;
  if(e.key==='1') decidir('confere');
  if(e.key==='2') decidir('corrigir');
  if(e.key==='3') decidir('remover');
});

fetch('/api/itens').then(function(r){return r.json();}).then(function(d){
  ITENS=d.itens; desenhar();
});
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def _envia(self, corpo, tipo="application/json; charset=utf-8", status=200):
        dados = corpo if isinstance(corpo, bytes) else corpo.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        rota = urlparse(self.path).path
        if rota in ("/", "/index.html"):
            return self._envia(PAGINA, "text/html; charset=utf-8")
        if rota == "/api/itens":
            return self._envia(json.dumps({"itens": montar_itens()}, ensure_ascii=False))
        self._envia(json.dumps({"erro": "rota desconhecida"}), status=404)

    def do_POST(self):
        if urlparse(self.path).path != "/api/decidir":
            return self._envia(json.dumps({"erro": "rota desconhecida"}), status=404)
        n = int(self.headers.get("Content-Length", 0))
        try:
            c = json.loads(self.rfile.read(n).decode("utf-8"))
        except ValueError:
            return self._envia(json.dumps({"erro": "pedido malformado"}), status=400)
        if c.get("decisao") not in ("confere", "corrigir", "remover"):
            return self._envia(json.dumps({"erro": "decisao invalida"}), status=400)
        ok = gravar(c.get("uf", ""), c.get("id"), c["decisao"],
                    c.get("nota", ""), c.get("citacao", ""))
        self._envia(json.dumps({"ok": ok} if ok else
                               {"erro": "posicao nao encontrada neste estado"}))

    def log_message(self, *a):
        pass


def conferir_pagina():
    """Recusa subir com JavaScript quebrado, em vez de servir tela em branco."""
    import re
    achado = re.search(r"<script>(.*?)</script>", PAGINA, re.S)
    if not achado:
        raise SystemExit("A pagina perdeu o bloco <script>.")
    js = achado.group(1)

    partidas = [n for n, linha in enumerate(js.split("\n"), 1) if linha.count("'") % 2]
    if partidas:
        raise SystemExit(
            "JavaScript quebrado nas linhas " + ", ".join(map(str, partidas[:5])) + " do bloco.\n"
            "Quase sempre e uma sequencia de escape interpretada pelo Python: confira se\n"
            'PAGINA continua sendo string CRUA (r"""), senao \\n vira quebra de linha real\n'
            "dentro de um literal de string e a pagina abre vazia."
        )

    for marca in ('id="cit"', 'id="nota"', 'data-d="confere"', "/api/decidir",
                  # Sem o uf no corpo do POST, o servidor nao sabe em qual dos 27
                  # arquivos escrever, e recusa tudo. Sem o uf no cartao, a tela
                  # alterna estados sem dizer que alternou.
                  "uf:it.uf", 'class="uf"'):
        if marca not in js and marca not in PAGINA:
            raise SystemExit(f"A pagina perdeu um elemento essencial: {marca}")


def main():
    # PORTA OCUPADA TEM DE PARAR, e nao subir por cima.
    #
    # allow_reuse_address liga SO_REUSEADDR, que no Linux so serve para reaproveitar
    # porta em TIME_WAIT. No Windows ele deixa DOIS processos escutarem a mesma
    # porta ao mesmo tempo — e quem recebe as conexoes e o PRIMEIRO. O efeito: a
    # curadoria abria a tela para revisar o Marcio Bittar, o navegador falava com um
    # servidor esquecido do Gladson Cameli, e a tela dizia "13 de 13 decididas,
    # restam 0". Tudo certo na aparencia, e a fila errada por tras.
    import socket
    with socket.socket() as s:
        s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", PORTA)) == 0:
            raise SystemExit(
                f"PAROU: ja existe algo respondendo em http://localhost:{PORTA}.\n"
                "  E quase sempre uma tela de revisao anterior, aberta com outro "
                "--uf ou outra --candidatura.\n"
                "  Subir por cima nao daria erro no Windows, e o navegador "
                "continuaria falando com a antiga.\n\n"
                "  Feche a janela do terminal onde ela roda, ou no PowerShell:\n"
                "    Get-NetTCPConnection -LocalPort " + str(PORTA) +
                " -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }")

    conferir_pagina()
    novas = 0
    for uf in UFS:
        origem = acervo.de(uf) / "posicoes.json"
        backup = acervo.de(uf) / "posicoes.json.antes-da-revisao"
        if not backup.exists():
            shutil.copy2(origem, backup)
            novas += 1
    if novas:
        print(f"copia de seguranca criada em {novas} estado(s)")

    itens = montar_itens()
    pend = [x for x in itens if not (x["revisado"] or x["revisao"])]
    ufs_pend = sorted({x["uf"] for x in pend})
    print(f"{len(itens)} posicoes em {len(UFS)} estado(s) · {len(pend)} ainda sem decisao")
    print(f"pendencias em {len(ufs_pend)} estado(s): {' '.join(ufs_pend)}")
    print("ordem: fonte secundaria e conferencia fraca primeiro")
    print("a fila alterna estado e candidatura a cada item")
    if pend:
        print("\nprimeiros da fila:")
        for x in pend[:6]:
            print(f"  {x['uf']}  {x['candidatura'][:34]:34}  {x['tema']}")
    print(f"\nabra http://localhost:{PORTA}  (ctrl+c aqui para parar)\n")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORTA), Handler) as srv:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORTA}")).start()
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nparado. o que voce decidiu ja esta gravado.")


if __name__ == "__main__":
    main()
