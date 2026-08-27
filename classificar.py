# -*- coding: utf-8 -*-
"""Tela local para CONFERIR a classificacao dos 304 itens coletados.

MUDOU O QUE ESTA TELA FAZ. Ela nascia pedindo que a curadoria classificasse os 304
um a um, e ela perguntou por que — se eu nao conseguia fazer isso. Consigo, e o
desenho estava errado: eu tinha aplicado a disciplina que existe para AFIRMACAO
a uma tarefa de ARQUIVAMENTO.

A diferenca importa. Na revisao das 122 posicoes a maquina afirmava "este
candidato propoe X" a partir de um documento, e errou em 66% — fonte que nao
sustentava, candidato trocado, parafrase escorregando. Aqui a ementa ja e
literal, ja veio da API e ja esta atribuida a quem assinou. Nao se afirma nada
sobre ninguem: a pergunta e so em qual das 10 gavetas o item aparece.

Entao eu classifiquei os 304, lendo cada ementa e cada indexacao oficial. Esta
tela mostra so o que sobra para o olho dela:

  - os 22 em que a escolha foi EDITORIAL e nao leitura (assunto que nao cabe em
    nenhum dos 10 temas, ou ementa que nao diz do que trata);
  - uma AMOSTRA sorteada do resto, para medir se eu acertei — sorteio fixo, pelo
    id, para a amostra nao mudar a cada abertura da tela.

Quem decide continua sendo ela: cada item guarda quem decidiu, e por="modelo"
nunca vira por="humano" sozinho.

E IRMA DO revisar.py, MAS A PERGUNTA E OUTRA
No revisar.py a pergunta e "a fonte sustenta o que esta escrito?" — e uma
conferencia de verdade. Aqui a ementa ja e literal e ja veio da API oficial: nao
ha o que conferir no texto. A pergunta e "de que assunto isto trata?", que e
escolha nossa de organizacao, e nao afirmacao sobre a candidatura.

Por isso esta tela nao escreve revisado_por_humano em lugar nenhum. Ela decide
onde o item aparece, e nao se ele e verdade.

A ORDEM
Primeiro os marcados como editoriais, que sao onde eu menos confio em mim.
Depois a amostra de auditoria. Parar no meio deixa conferido o que mais precisa.

TECLADO
  Enter    aceita o tema sugerido
  1 a 0    escolhe o tema (1=Seguranca ... 0=Organizacao do Estado)
  X        nao se aplica a nenhum tema (procedimental, local, fora de escopo)
  L        o link nao abre a peca certa
  seta ->  pula sem decidir

USO
    python classificar.py
    (abre http://localhost:8766 no navegador)
"""
import http.server
import sys as _sys
import json
import pathlib
import re
import socketserver
import threading
import webbrowser
from datetime import date
from urllib.parse import urlparse

RAIZ = pathlib.Path(__file__).resolve().parent
import argparse as _argparse

import acervo

# Qual estado esta ferramenta trabalha. --uf existe para nao ser preciso editar
# referencia.json e lembrar de voltar: esquecer de voltar escreveria no acervo
# errado achando que era o certo.
_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--uf", default=None)
_UF = (_ap.parse_known_args()[0].uf or acervo.uf_padrao()).upper()

DADOS = acervo.exige(_UF)          # dados/<uf>/ — acervo daquele estado
_ap.add_argument("--quem", default=None)
# Em sandbox nao pergunta: o teste roda sem ninguem no teclado.
QUEM = ("teste-automatizado" if "--sandbox" in _sys.argv
        else acervo.quem(_ap.parse_known_args()[0].quem))
NACIONAL = acervo.NACIONAL         # dados/ — referencia, estados, mapa
PORTA = 8766
HOJE = date.today().isoformat()

# --sandbox faz a tela trabalhar numa COPIA dos arquivos, em pasta temporaria.
#
# Existe porque o teste automatizado grava uma decisao de verdade para conferir
# que a gravacao funciona — e as execucoes que morriam antes da limpeza deixavam
# a decisao para tras. Sete itens de Sao Paulo ficaram marcados como decididos
# por gente sem que ninguem os tivesse decidido, com tema errado.
#
# Limpeza depois do fato depende de o teste chegar ao fim. Copia nao depende de
# nada: o arquivo de verdade fica fora de alcance.
_SANDBOX = "--sandbox" in _sys.argv
if _SANDBOX:
    import shutil as _shutil
    import tempfile as _tempfile
    _tmp = pathlib.Path(_tempfile.mkdtemp(prefix="classificar-sandbox-"))
    # candidaturas.json entra na copia porque a tela LE dele (o nome de cada
    # candidatura). Ficou de fora na primeira versao e a tela nem subiu.
    for _n in ("_coleta_legislativa.json", "_coleta_discursos.json", "candidaturas.json"):
        if (DADOS / _n).exists():
            _shutil.copy2(DADOS / _n, _tmp / _n)
    DADOS = _tmp

ARQUIVOS = {
    "proposicao": DADOS / "_coleta_legislativa.json",
    "discurso": DADOS / "_coleta_discursos.json",
}

# Candidaturas que hoje nao tem NENHUMA proposta no site. Sao o motivo de tudo
# isto existir, entao vem primeiro.
PRIORIDADE = ["sen-sp-2026-salles", "sen-sp-2026-derrite",
              "sen-sp-2026-tebet", "sen-sp-2026-marina"]

ORDEM_CONF = {"boa": 0, "ambigua": 1, "fraca": 2, "nenhuma": 3}

# Um em cada QUANTOS entra na amostra de auditoria. Com 282 itens nao marcados,
# 1 em 9 da ~31 — o bastante para uma taxa de acerto significar alguma coisa, e
# pouco o bastante para caber numa sentada.
AMOSTRA = 9


def na_amostra(id_item: str) -> bool:
    """Sorteio ESTAVEL: depende so do id, entao a amostra e a mesma toda vez que
    a tela abre. Amostra que muda a cada abertura nao mede nada."""
    return sum(ord(c) for c in id_item) % AMOSTRA == 0


def carregar():
    ref = json.loads((NACIONAL / "referencia.json").read_text(encoding="utf-8"))
    cand = json.loads((DADOS / "candidaturas.json").read_text(encoding="utf-8"))["candidaturas"]
    nomes = {c["id_candidatura"]: c["pessoa"]["nome_urna"] for c in cand}
    temas = [{"id": t["id_tema"], "nome": t["nome"]} for t in sorted(ref["temas"], key=lambda t: t["ordem"])]
    return temas, nomes


def montar_itens():
    temas, nomes = carregar()
    itens = []
    for especie, caminho in ARQUIVOS.items():
        if not caminho.exists():
            continue
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        for r in dados["registros"]:
            cid = r.get("id_candidatura") or (r.get("autoria") or [{}])[0].get("id_candidatura", "")
            a = (r.get("autoria") or [{}])[0]
            cl = r.get("_classificacao") or {}
            # Item SEM classificacao nenhuma nao esta pronto para a conferencia:
            # falta o passo do modelo, que e trabalho meu e nao dela. Em PE isso
            # sao 516 itens de duas candidaturas ainda nao lidas — na fila, eles
            # afogariam os 30 que precisam mesmo de um olhar.
            if not cl:
                continue
            # Ja conferido por gente sai da fila. O que eu classifiquei so
            # aparece se for editorial ou se caiu na amostra de auditoria.
            if cl.get("por") == "humano":
                continue
            if cl.get("por") == "modelo" and not (cl.get("precisa_de_olho")
                                                  or na_amostra(r["id_registro"])):
                continue
            itens.append({
                "id": r["id_registro"],
                "especie": especie,
                "candidatura": nomes.get(cid, cid),
                "id_candidatura": cid,
                "rotulo": (f'{r.get("tipo","")} {r.get("numero","")}/{r.get("ano","")}'
                           if especie == "proposicao"
                           else f'{r.get("tipo_sessao","")} · {r.get("data","")}'),
                "texto": r.get("ementa") or r.get("sumario_oficial") or "",
                "transcricao": r.get("trecho_transcricao") or "",
                "indexacao": r.get("indexacao_oficial") or "",
                "url": r.get("url") or "",
                "ordem_autoria": a.get("ordem_autoria"),
                "total_autores": a.get("total_autores"),
                "ressalva": r.get("_ressalva") or "",
                "sugestao": r.get("temas") or [],
                "confianca": r.get("_confianca_tema") or "nenhuma",
                "decisao": r.get("_classificacao") or {},
                "minha": cl.get("temas") if cl.get("por") == "modelo" else None,
                "precisa_de_olho": cl.get("precisa_de_olho") or "",
            })

    # Editorial primeiro: e onde eu menos confio em mim.
    itens.sort(key=lambda x: (
        not bool(x["precisa_de_olho"]),
        PRIORIDADE.index(x["id_candidatura"]) if x["id_candidatura"] in PRIORIDADE else 9,
        x["id"],
    ))
    return itens, temas


def gravar(id_item, temas, motivo):
    """Grava na hora, no arquivo de coleta. Fechar a janela no meio nao perde nada."""
    for caminho in ARQUIVOS.values():
        if not caminho.exists():
            continue
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        for r in dados["registros"]:
            if r["id_registro"] != id_item:
                continue
            antes = (r.get("_classificacao") or {})
            r["_classificacao"] = {
                "temas": temas, "motivo": motivo, "por": "humano",
                "por_quem": QUEM, "decidido_em": HOJE,
            }
            # Guarda se ela concordou comigo. E a unica forma honesta de saber se
            # a minha classificacao presta: medida, e nao afirmada.
            if antes.get("por") == "modelo":
                r["_classificacao"]["modelo_propos"] = antes.get("temas")
                r["_classificacao"]["concordou"] = sorted(antes.get("temas") or []) == sorted(temas)
                if antes.get("precisa_de_olho"):
                    r["_classificacao"]["precisa_de_olho"] = antes["precisa_de_olho"]
            caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
            return True
    return False


def esquecer(id_item):
    """Desfaz a decisao HUMANA de um item e devolve a do modelo. So o teste usa.

    Apagar _classificacao inteiro era o obvio e estava errado: levava junto a
    classificacao do modelo, e o teste comia trabalho de verdade — aconteceu em
    dois itens. Por isso gravar() guarda modelo_propos: e o que permite voltar."""
    for caminho in ARQUIVOS.values():
        if not caminho.exists():
            continue
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        for r in dados["registros"]:
            if r["id_registro"] != id_item or "_classificacao" not in r:
                continue
            antes = r["_classificacao"]
            if "modelo_propos" in antes:
                r["_classificacao"] = {
                    "temas": antes["modelo_propos"],
                    "motivo": "" if antes["modelo_propos"] else "nenhum",
                    "por": "modelo",
                    "decidido_em": antes.get("decidido_em", HOJE),
                }
                if antes.get("precisa_de_olho"):
                    r["_classificacao"]["precisa_de_olho"] = antes["precisa_de_olho"]
            else:
                del r["_classificacao"]
            caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
            return True
    return False


PAGINA = r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Classificar por tema</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{font:16px/1.6 system-ui,sans-serif;background:#F7F4F1;color:#141110;padding:26px 20px 90px}
.env{max-width:780px;margin:0 auto}
h1{font-size:1.12rem;margin-bottom:3px}
.sub{color:#6A6259;font-size:.87rem;margin-bottom:18px}
.barra{height:7px;background:#E5E0DA;border-radius:4px;overflow:hidden;margin-bottom:20px}
.barra i{display:block;height:100%;background:#2FB4E4}
.cartao{background:#fff;border:1px solid #E5E0DA;border-radius:9px;padding:20px 22px}
.topo{display:flex;flex-wrap:wrap;gap:9px;align-items:baseline;margin-bottom:13px}
.quem{font-weight:700}
.rot{font-family:ui-monospace,monospace;font-size:.79rem;background:#EDE7E1;padding:3px 8px;border-radius:4px}
.esp{font-size:.75rem;letter-spacing:.05em;color:#6A6259}
.txt{font-size:1.02rem;line-height:1.62;margin-bottom:14px}
.transc{font-size:.9rem;color:#3E3833;background:#F7F4F1;border-left:3px solid #E5E0DA;
  padding:11px 14px;margin-bottom:13px;white-space:pre-wrap}
.idx{font-size:.82rem;color:#3E3833;background:#F0F6FA;border-left:3px solid #2FB4E4;
  padding:10px 13px;margin-bottom:13px}
.idx b{display:block;font-size:.71rem;letter-spacing:.06em;color:#0C6C8F;margin-bottom:3px}
.aut{font-size:.85rem;color:#B02418;margin-bottom:12px}
.ress{font-size:.82rem;color:#6A6259;font-style:italic;margin-bottom:12px}
a.fonte{display:inline-block;font-size:.89rem;color:#0C6C8F;margin-bottom:16px}
.pergunta{font-size:.85rem;color:#6A6259;margin:16px 0 9px;padding-top:14px;border-top:1px solid #E5E0DA}
.temas{display:grid;grid-template-columns:repeat(auto-fill,minmax(228px,1fr));gap:7px}
.temas button{text-align:left;padding:9px 12px;border:1px solid #E5E0DA;background:#fff;
  border-radius:6px;font:inherit;font-size:.88rem;cursor:pointer;display:flex;gap:9px;align-items:center}
.temas button:hover{border-color:#2FB4E4}
.temas button.sug{border-color:#2FB4E4;background:#F0F6FA;font-weight:600}
.temas button kbd{font-family:ui-monospace,monospace;font-size:.72rem;background:#EDE7E1;
  border-radius:3px;padding:1px 5px;min-width:20px;text-align:center}
.outros{display:flex;gap:8px;flex-wrap:wrap;margin-top:13px}
.outros button{padding:9px 14px;border:1px solid #E5E0DA;background:#fff;border-radius:6px;
  font:inherit;font-size:.87rem;cursor:pointer}
.outros button:hover{border-color:#7E756B}
.dica{font-size:.8rem;color:#6A6259;margin-top:15px}
.olho{font-size:.87rem;background:#FBEFD2;border-left:3px solid #7A5200;color:#3E3833;
  padding:11px 14px;margin-bottom:13px;border-radius:0 5px 5px 0}
.olho b{display:block;font-size:.72rem;letter-spacing:.06em;color:#7A5200;margin-bottom:3px}
.minha{font-size:.87rem;background:#F0F6FA;border-left:3px solid #0C6C8F;color:#3E3833;
  padding:11px 14px;margin:14px 0 4px;border-radius:0 5px 5px 0}
.minha b{color:#0C6C8F}
.tipo{font-size:.72rem;letter-spacing:.05em;color:#7A5200;font-weight:700}
.fim{background:#fff;border:1px solid #E5E0DA;border-radius:9px;padding:30px;text-align:center}
#aviso{background:#FBE3E0;border:1px solid #B02418;color:#7a1a12;border-radius:7px;
  padding:13px 16px;margin-bottom:16px;font-size:.9rem;line-height:1.55}
#aviso code{background:#fff;padding:1px 5px;border-radius:3px}
</style></head><body><div class="env">
<h1>Classificar por tema</h1>
<div class="sub" id="sub"></div>
<div class="barra"><i id="prog" style="width:0%"></i></div>
<div id="aviso" hidden></div>
<div id="alvo"></div>
</div>
<script>
var ITENS=[], TEMAS=[], i=0;

function esc(s){var d=document.createElement('div');d.textContent=s==null?'':String(s);return d.innerHTML;}

/* Pendente = ainda nao conferido POR GENTE. Antes era "sem tema", o que parou de
   funcionar quando eu classifiquei os 304: a tela achava que estava tudo feito. */
function pendentes(){return ITENS.filter(function(x){
  return !x.decisao || x.decisao.por!=='humano';});}

function desenhar(){
  var pend=pendentes();
  var feitos=ITENS.length-pend.length;
  var concordou=0, discordou=0;
  for(var q=0;q<ITENS.length;q++){
    var d=ITENS[q].decisao||{};
    if(d.por==='humano'&&typeof d.concordou==='boolean'){ d.concordou?concordou++:discordou++; }
  }
  document.getElementById('sub').textContent=
    feitos+' de '+ITENS.length+' conferidos · restam '+pend.length+
    (concordou+discordou ? ' · você concordou comigo em '+concordou+
       ' de '+(concordou+discordou) : '');
  document.getElementById('prog').style.width=(ITENS.length?feitos/ITENS.length*100:0)+'%';

  if(i>=pend.length) i=0;
  var x=pend[i];
  var alvo=document.getElementById('alvo');
  if(!x){
    alvo.innerHTML='<div class="fim"><h2>Acabou.</h2><p>Os '+ITENS.length+
      ' itens que precisavam do seu olho estão conferidos'+
      (concordou+discordou ? ': você concordou comigo em <strong>'+concordou+' de '+
        (concordou+discordou)+'</strong>' : '')+
      '. Os outros '+(304-ITENS.length)+' seguem marcados como classificados por mim.</p></div>';
    return;
  }

  var h='<div class="cartao"><div class="topo">'+
    '<span class="quem">'+esc(x.candidatura)+'</span>'+
    '<span class="rot">'+esc(x.rotulo)+'</span>'+
    '<span class="esp">'+esc(x.especie)+'</span></div>';

  h+='<p class="txt">'+esc(x.texto)+'</p>';

  if(x.transcricao) h+='<div class="transc">'+esc(x.transcricao)+
    (x.transcricao.length>=690?' […]':'')+'</div>';

  if(x.indexacao) h+='<div class="idx"><b>Indexação da própria casa legislativa</b>'+
    esc(x.indexacao)+'</div>';

  if(x.total_autores&&x.total_autores>1&&x.ordem_autoria)
    h+='<p class="aut">Assinatura '+esc(x.ordem_autoria)+' de '+esc(x.total_autores)+
       '. Em texto com muitos autores, assinar não é propor.</p>';

  if(x.ressalva) h+='<p class="ress">'+esc(x.ressalva)+'</p>';

  if(x.url) h+='<a class="fonte" href="'+esc(x.url)+'" target="_blank" rel="noopener">'+
    'abrir a peça na fonte oficial &rarr;</a>';

  var nomeT=function(id){for(var q=0;q<TEMAS.length;q++)if(TEMAS[q].id===id)return TEMAS[q].nome;return id;};

  if(x.precisa_de_olho)
    h+='<div class="olho"><b>Marquei para você olhar</b>'+esc(x.precisa_de_olho)+'</div>';

  h+='<div class="minha"><b>Eu classifiquei como:</b> '+
     (x.minha&&x.minha.length ? esc(x.minha.map(nomeT).join(' + '))
                              : '<em>nenhum tema — procedimental ou sem objeto declarado</em>')+
     '</div>';

  h+='<div class="pergunta">Confere? <strong>Enter</strong> aceita. '+
     'Se eu errei, escolha o tema certo — é escolha de organização, '+
     'não afirmação sobre a candidatura.</div>';

  h+='<div class="temas">';
  for(var n=0;n<TEMAS.length;n++){
    var t=TEMAS[n];
    var sug=(x.minha||x.sugestao).indexOf(t.id)>=0;
    h+='<button data-t="'+esc(t.id)+'"'+(sug?' class="sug"':'')+'>'+
       '<kbd>'+((n+1)%10)+'</kbd>'+esc(t.nome)+'</button>';
  }
  h+='</div>';

  h+='<div class="outros">'+
     '<button data-x="nenhum">X — não se aplica a nenhum tema</button>'+
     '<button data-x="link">L — o link não abre a peça certa</button>'+
     '<button data-x="pular">Pular &rarr;</button>'+
     '</div>';

  h+='<p class="dica">'+
     (x.precisa_de_olho ? '<span class="tipo">ESCOLHA EDITORIAL</span> — eu escolhi a gaveta '+
                          'menos ruim, e a sua leitura vale mais que a minha aqui.'
                        : '<span class="tipo">AMOSTRA DE AUDITORIA</span> — sorteada para medir '+
                          'se a minha classificação presta. Discordar aqui é o ponto.')+
     '</p>';

  h+='</div>';
  alvo.innerHTML=h;

  var bs=alvo.querySelectorAll('.temas button');
  for(var k=0;k<bs.length;k++)
    bs[k].addEventListener('click',function(){decidir([this.getAttribute('data-t')],'');});
  var os=alvo.querySelectorAll('.outros button');
  for(var k2=0;k2<os.length;k2++)
    os[k2].addEventListener('click',function(){
      var v=this.getAttribute('data-x');
      if(v==='pular'){i++;desenhar();return;}
      decidir([], v);
    });
}

/* O erro TEM de aparecer. Antes, se a gravacao falhasse, a tela avancava do
   mesmo jeito e nao dizia nada: a decisao sumia e o item voltava no proximo
   carregamento. Da tela, isso e indistinguivel de "o botao nao funciona" — e foi
   assim que apareceu no uso. fetch nao lanca excecao em resposta 400, entao engolir
   o resultado era engolir a falha. */
function decidir(temas, motivo){
  var pend=pendentes(); var x=pend[i];
  if(!x) return;
  fetch('/api/classificar',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id:x.id,temas:temas,motivo:motivo})})
   .then(function(r){return r.json().then(function(j){return {http:r.status,corpo:j};});})
   .then(function(res){
     if(res.http!==200||res.corpo.erro||res.corpo.ok!==true){
       falhou((res.corpo&&res.corpo.erro)||('o servidor respondeu '+res.http));
       return;
     }
     x.decisao={temas:temas,motivo:motivo,por:'humano',
                concordou: x.minha ? String(x.minha.slice().sort())===String(temas.slice().sort())
                                   : undefined};
     var b=document.getElementById('aviso'); if(b){b.hidden=true;b.innerHTML='';}
     desenhar();
   })
   .catch(function(e){ falhou('não consegui falar com o servidor: '+e.message); });
}

function falhou(msg){
  var b=document.getElementById('aviso');
  if(!b) return;
  b.innerHTML='<strong>A decisão NÃO foi gravada.</strong> '+esc(msg)+
    '<br>Se o servidor foi iniciado antes da última atualização, pare o '+
    '<code>classificar.py</code> no terminal (ctrl+c) e rode de novo.';
  b.hidden=false;
}

document.addEventListener('keydown',function(e){
  if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA') return;
  var pend=pendentes(); var x=pend[i];
  if(!x) return;
  if(e.key==='Enter'){
    e.preventDefault();
    var m=x.minha||x.sugestao;
    decidir(m, m.length?'':'nenhum');
    return;
  }
  if(e.key==='x'||e.key==='X'){ e.preventDefault(); decidir([],'nenhum'); return; }
  if(e.key==='l'||e.key==='L'){ e.preventDefault(); decidir([],'link'); return; }
  if(e.key==='ArrowRight'){ e.preventDefault(); i++; desenhar(); return; }
  if(/^[0-9]$/.test(e.key)){
    var n=(e.key==='0')?9:(parseInt(e.key,10)-1);
    if(TEMAS[n]){ e.preventDefault(); decidir([TEMAS[n].id],''); }
  }
});

fetch('/api/itens').then(function(r){return r.json();}).then(function(d){
  ITENS=d.itens; TEMAS=d.temas; desenhar();
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
            itens, temas = montar_itens()
            # 'pasta' diz ONDE a gravacao acontece. O teste precisa disso: com
            # sandbox ligado ele conferia o arquivo de verdade, que nao recebe
            # mais a escrita — e passava por coincidencia quando o tema batia.
            return self._envia(json.dumps(
                {"itens": itens, "temas": temas, "pasta": str(DADOS)}, ensure_ascii=False))
        self._envia(json.dumps({"erro": "rota desconhecida"}), status=404)

    def do_POST(self):
        rota = urlparse(self.path).path
        if rota == "/api/limpar-teste":
            # Existe para o teste automatizado desfazer a propria gravacao. Sem
            # isto, rodar o teste deixaria uma decisao de maquina se passando por
            # decisao humana no arquivo — que e a coisa que este projeto nunca faz.
            n = int(self.headers.get("Content-Length", 0))
            c = json.loads(self.rfile.read(n).decode("utf-8"))
            return self._envia(json.dumps({"ok": esquecer(c.get("id"))}))
        if rota != "/api/classificar":
            return self._envia(json.dumps({"erro": "rota desconhecida"}), status=404)
        n = int(self.headers.get("Content-Length", 0))
        try:
            c = json.loads(self.rfile.read(n).decode("utf-8"))
        except ValueError:
            return self._envia(json.dumps({"erro": "pedido malformado"}), status=400)
        temas = c.get("temas") or []
        motivo = c.get("motivo") or ""
        if not temas and motivo not in ("nenhum", "link"):
            return self._envia(json.dumps({"erro": "sem tema e sem motivo"}), status=400)
        ok = gravar(c.get("id"), temas, motivo)
        if not ok:
            # Acontece quando a pagina no navegador e mais velha que os dados:
            # os ids de discurso mudaram quando a hora entrou neles, e uma aba
            # aberta antes disso manda ids que nao existem mais.
            return self._envia(json.dumps({
                "erro": f'nao existe item com id "{c.get("id")}" — a página aberta '
                        'no navegador é mais antiga que os dados'}), status=409)
        self._envia(json.dumps({"ok": True}))

    def log_message(self, *a):
        pass


def conferir_pagina():
    """Recusa subir com JavaScript quebrado, em vez de servir tela em branco.
    Ja aconteceu no revisar.py: PAGINA deixou de ser string crua e o \\n virou
    quebra de linha de verdade dentro de um literal JS."""
    achado = re.search(r"<script>(.*?)</script>", PAGINA, re.S)
    if not achado:
        raise SystemExit("A pagina perdeu o bloco <script>.")
    js = achado.group(1)
    partidas = [n for n, linha in enumerate(js.split("\n"), 1) if linha.count("'") % 2]
    if partidas:
        raise SystemExit("JavaScript quebrado nas linhas " + ", ".join(map(str, partidas[:5])) +
                         '.\nConfira se PAGINA continua sendo string CRUA (r""").')
    for marca in ("/api/classificar", "data-x=\"nenhum\"", "function decidir",
                  "class=\"minha\"", "function falhou", 'id="aviso"'):
        if marca not in PAGINA:
            raise SystemExit(f"A pagina perdeu um elemento essencial: {marca}")


def main():
    conferir_pagina()
    if _SANDBOX:
        print("*** MODO SANDBOX: trabalhando numa copia em " + str(DADOS))
        print("*** os arquivos de verdade nao serao tocados")
        print()
    faltando = [c.name for c in ARQUIVOS.values() if not c.exists()]
    if faltando:
        raise SystemExit("faltam arquivos de coleta: " + ", ".join(faltando) +
                         "\nrode coletar_legislativo.py e coletar_discursos.py antes.")

    itens, _ = montar_itens()
    ed = [x for x in itens if x["precisa_de_olho"]]
    print(f"304 itens coletados, ja classificados por mim.")
    print(f"{len(itens)} precisam do seu olho: {len(ed)} escolhas editoriais "
          f"+ {len(itens) - len(ed)} sorteados para auditoria.")
    print("ordem: os editoriais primeiro, que e onde eu menos confio em mim")
    print(f"\nabra http://localhost:{PORTA}  (ctrl+c aqui para parar)\n")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORTA), Handler) as srv:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORTA}")).start()
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nparado. o que voce classificou ja esta gravado.")


if __name__ == "__main__":
    main()
