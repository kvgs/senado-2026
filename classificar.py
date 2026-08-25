# -*- coding: utf-8 -*-
"""Tela local para dar tema aos 304 itens coletados, um a um.

E IRMA DO revisar.py, MAS A PERGUNTA E OUTRA
No revisar.py a pergunta e "a fonte sustenta o que esta escrito?" — e uma
conferencia de verdade. Aqui a ementa ja e literal e ja veio da API oficial: nao
ha o que conferir no texto. A pergunta e "de que assunto isto trata?", que e
escolha nossa de organizacao, e nao afirmacao sobre a candidatura.

Por isso esta tela nao escreve revisado_por_humano em lugar nenhum. Ela decide
onde o item aparece, e nao se ele e verdade.

A ORDEM E POR IMPACTO
Primeiro as candidaturas que hoje aparecem vazias no site — Salles, Derrite,
Tebet, Marina. Dentro de cada uma, primeiro os de sugestao confiante, que sao
os rapidos. Se voce parar no meio, terá preenchido os perfis que estao vazios.

NAO EXISTE "CONFIRMAR TODOS"
Seria o botao mais tentador da tela e o mais caro: a revisao das 122 posicoes
achou 34% de acerto na maquina. Cada item leva um olhar. O que da para acelerar
e o teclado, e nao o lote.

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
import json
import pathlib
import re
import socketserver
import threading
import webbrowser
from datetime import date
from urllib.parse import urlparse

RAIZ = pathlib.Path(__file__).resolve().parent
DADOS = RAIZ / "dados"
PORTA = 8766
HOJE = date.today().isoformat()

ARQUIVOS = {
    "proposicao": DADOS / "_coleta_legislativa.json",
    "discurso": DADOS / "_coleta_discursos.json",
}

# Candidaturas que hoje nao tem NENHUMA proposta no site. Sao o motivo de tudo
# isto existir, entao vem primeiro.
PRIORIDADE = ["sen-sp-2026-salles", "sen-sp-2026-derrite",
              "sen-sp-2026-tebet", "sen-sp-2026-marina"]

ORDEM_CONF = {"boa": 0, "ambigua": 1, "fraca": 2, "nenhuma": 3}


def carregar():
    ref = json.loads((DADOS / "referencia.json").read_text(encoding="utf-8"))
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
            })

    itens.sort(key=lambda x: (
        bool(x["decisao"]),
        PRIORIDADE.index(x["id_candidatura"]) if x["id_candidatura"] in PRIORIDADE else 9,
        ORDEM_CONF.get(x["confianca"], 9),
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
            r["_classificacao"] = {"temas": temas, "motivo": motivo, "decidido_em": HOJE}
            caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
            return True
    return False


def esquecer(id_item):
    """Apaga a classificacao de um item. So o teste usa."""
    for caminho in ARQUIVOS.values():
        if not caminho.exists():
            continue
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        for r in dados["registros"]:
            if r["id_registro"] == id_item and "_classificacao" in r:
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
.fim{background:#fff;border:1px solid #E5E0DA;border-radius:9px;padding:30px;text-align:center}
</style></head><body><div class="env">
<h1>Classificar por tema</h1>
<div class="sub" id="sub"></div>
<div class="barra"><i id="prog" style="width:0%"></i></div>
<div id="alvo"></div>
</div>
<script>
var ITENS=[], TEMAS=[], i=0;

function esc(s){var d=document.createElement('div');d.textContent=s==null?'':String(s);return d.innerHTML;}

function pendentes(){return ITENS.filter(function(x){return !x.decisao||!x.decisao.temas;});}

function desenhar(){
  var pend=pendentes();
  var feitos=ITENS.length-pend.length;
  document.getElementById('sub').textContent=
    feitos+' de '+ITENS.length+' classificados · restam '+pend.length;
  document.getElementById('prog').style.width=(ITENS.length?feitos/ITENS.length*100:0)+'%';

  if(i>=pend.length) i=0;
  var x=pend[i];
  var alvo=document.getElementById('alvo');
  if(!x){
    alvo.innerHTML='<div class="fim"><h2>Acabou.</h2><p>Todos os '+ITENS.length+
      ' itens tem tema decidido. Os arquivos de coleta ja estao gravados.</p></div>';
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

  h+='<div class="pergunta">De que assunto isto trata? '+
     '<em>É escolha de organização, não afirmação sobre a candidatura.</em></div>';

  h+='<div class="temas">';
  for(var n=0;n<TEMAS.length;n++){
    var t=TEMAS[n];
    var sug=x.sugestao.indexOf(t.id)>=0;
    h+='<button data-t="'+esc(t.id)+'"'+(sug?' class="sug"':'')+'>'+
       '<kbd>'+((n+1)%10)+'</kbd>'+esc(t.nome)+'</button>';
  }
  h+='</div>';

  h+='<div class="outros">'+
     '<button data-x="nenhum">X — não se aplica a nenhum tema</button>'+
     '<button data-x="link">L — o link não abre a peça certa</button>'+
     '<button data-x="pular">Pular &rarr;</button>'+
     '</div>';

  h+='<p class="dica">Sugestão do coletor: <strong>'+
     (x.sugestao.length?esc(x.sugestao.join(', ')):'nenhuma')+
     '</strong> (confiança '+esc(x.confianca)+'). Enter aceita.</p>';

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

function decidir(temas, motivo){
  var pend=pendentes(); var x=pend[i];
  if(!x) return;
  fetch('/api/classificar',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id:x.id,temas:temas,motivo:motivo})})
   .then(function(r){return r.json();})
   .then(function(){
     x.decisao={temas:temas,motivo:motivo};
     desenhar();
   });
}

document.addEventListener('keydown',function(e){
  if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA') return;
  var pend=pendentes(); var x=pend[i];
  if(!x) return;
  if(e.key==='Enter'){ if(x.sugestao.length){e.preventDefault();decidir(x.sugestao,'');} return; }
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
            return self._envia(json.dumps({"itens": itens, "temas": temas}, ensure_ascii=False))
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
        self._envia(json.dumps({"ok": ok} if ok else {"erro": "item nao encontrado"}))

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
    for marca in ("/api/classificar", "data-x=\"nenhum\"", "function decidir"):
        if marca not in PAGINA:
            raise SystemExit(f"A pagina perdeu um elemento essencial: {marca}")


def main():
    conferir_pagina()
    faltando = [c.name for c in ARQUIVOS.values() if not c.exists()]
    if faltando:
        raise SystemExit("faltam arquivos de coleta: " + ", ".join(faltando) +
                         "\nrode coletar_legislativo.py e coletar_discursos.py antes.")

    itens, _ = montar_itens()
    pend = [x for x in itens if not x["decisao"]]
    print(f"{len(itens)} itens coletados · {len(pend)} ainda sem tema")
    print("ordem: candidaturas hoje vazias primeiro (Salles, Derrite, Tebet, Marina)")
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
