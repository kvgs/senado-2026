# -*- coding: utf-8 -*-
"""Tela local para revisar as 122 posicoes do acervo, uma a uma.

POR QUE UMA TELA E NAO UMA LISTA
Revisar 122 itens num editor de JSON e uma tarefa que se abandona no item 15.
Aqui cada item aparece sozinho, com o link da fonte a um clique e tres botoes.
Cada decisao e gravada na hora em dados/posicoes.json — fechar a janela no meio
nao perde nada.

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
    python revisar.py
    (abre http://localhost:8765 no navegador)
"""
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
DADOS = RAIZ / "dados"
PORTA = 8765

ORDEM_FORCA = {"baixa": 0, "media": 1, "alta": 2}
ORDEM_FONTE = {"secundaria": 0, "declaracao_candidato": 1, "registro_legislativo": 2, "oficial": 3}

O_QUE_CONFERIR = {
    "secundaria": "Abra a fonte e confira duas coisas: a matéria diz isso mesmo, e atribui "
                  "à candidatura certa? Fonte secundária é onde a atribuição se perde.",
    "declaracao_candidato": "Abra o site e confira se o texto ainda está lá. Site de campanha "
                            "muda sem aviso, e a data de referência tem de bater com o que se vê hoje.",
    "registro_legislativo": "Confira o número e o ano da proposição, e se a autoria é mesmo desta "
                            "candidatura — em projeto com muitos autores, ser um deles não é ser o autor.",
    "oficial": "Confira se o trecho está no documento registrado e se ele vale para São Paulo. "
               "Programa nacional cobre a candidatura por atribuição partidária; programa de outro "
               "estado, não.",
}


def carregar():
    pos = json.loads((DADOS / "posicoes.json").read_text(encoding="utf-8"))
    docs = json.loads((DADOS / "documentos.json").read_text(encoding="utf-8"))
    cand = json.loads((DADOS / "candidaturas.json").read_text(encoding="utf-8"))
    ref = json.loads((DADOS / "referencia.json").read_text(encoding="utf-8"))
    return pos, docs, cand, ref


def lista(x, chave):
    return x[chave] if isinstance(x, dict) else x


def montar_itens():
    pos, docs, cand, ref = carregar()
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
        itens.append({
            "id": r["id_posicao"],
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
            "fonte_url": doc.get("url", ""),
            "fonte_local": doc.get("arquivo_local", ""),
            "forca": conf.get("forca", ""),
            "base": conf.get("base", ""),
            "ressalva": conf.get("ressalva", ""),
            "o_que_conferir": O_QUE_CONFERIR.get(r.get("nivel_fonte"), ""),
            "revisado": bool(r.get("revisado_por_humano")),
            "revisao": r.get("revisao") or {},
        })

    itens.sort(key=lambda x: (
        bool(x["revisado"] or x["revisao"]),
        ORDEM_FORCA.get(x["forca"], 9),
        ORDEM_FONTE.get(x["nivel_fonte"], 9),
        x["id"],
    ))
    return itens


def gravar(id_posicao, decisao, nota):
    caminho = DADOS / "posicoes.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    alvo = lista(dados, "posicoes")
    achou = False
    for r in alvo:
        if r["id_posicao"] != id_posicao:
            continue
        achou = True
        r["revisao"] = {"em": date.today().isoformat(), "resultado": decisao, "nota": nota or ""}
        # So "confere" marca como revisado por humano. As outras decisoes sao
        # registro de problema: um item com problema conhecido nao esta revisado,
        # esta condenado.
        r["revisado_por_humano"] = (decisao == "confere")
    if not achou:
        return False
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    return True


PAGINA = """<!doctype html>
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
  var feitos=ITENS.filter(function(x){return x.revisado||x.revisao&&x.revisao.resultado;}).length;
  document.getElementById('progresso').textContent =
    feitos+' de '+ITENS.length+' decididas · restam '+(ITENS.length-feitos);
  document.getElementById('preenche').style.width=(feitos/ITENS.length*100)+'%';
}

function desenhar(){
  progresso();
  var alvo=document.getElementById('alvo');
  var pend=ITENS.filter(function(x){return !(x.revisado||x.revisao&&x.revisao.resultado);});
  if(!pend.length){ alvo.innerHTML='<p class="fim">Tudo decidido. Rode <code>python validar.py</code> e '+
    '<code>python gerar_site.py</code> para publicar.</p>'; return; }
  var it=pend[0];
  alvo.innerHTML='<div class="cartao"><div class="topo">'+
    '<h2>'+esc(it.numero)+' · '+esc(it.candidatura)+'</h2>'+
    '<span class="tag">'+esc(it.tema)+'</span>'+
    '<span class="tag '+esc(it.forca)+'">conferencia '+esc(it.forca)+'</span>'+
    '<span class="tag">'+esc(it.nivel_fonte)+'</span>'+
    (it.de_partido?'<span class="tag">programa do '+esc(it.partido)+'</span>':'')+
    '</div>'+
    (it.citacao?'<blockquote>'+esc(it.citacao)+'</blockquote>':'')+
    (it.texto?'<p class="txt">'+esc(it.texto)+'</p>':'')+
    (it.escopo?'<p class="txt"><strong>Escopo:</strong> '+esc(it.escopo)+'</p>':'')+
    '<div class="meta">'+
      '<span>Fonte: '+(it.fonte_url?'<a href="'+esc(it.fonte_url)+'" target="_blank" rel="noopener">'+
        esc(it.fonte_titulo)+'</a>':esc(it.fonte_titulo))+'</span>'+
      (it.fonte_local?'<span>Arquivo local: '+esc(it.fonte_local)+'</span>':'')+
      '<span>Data de referencia: '+esc(it.data_referencia)+'</span>'+
      (it.base?'<span>Base da conferencia por IA: '+esc(it.base)+'</span>':'')+
      (it.ressalva?'<span><strong>Ressalva anotada:</strong> '+esc(it.ressalva)+'</span>':'')+
    '</div>'+
    '<p class="confira">'+esc(it.o_que_conferir)+'</p>'+
    '<textarea id="nota" rows="2" placeholder="Nota (obrigatoria se houver problema)"></textarea>'+
    '<div class="acoes">'+
      '<button class="ok" data-d="confere">Confere (1)</button>'+
      '<button class="err" data-d="corrigir">Tem erro (2)</button>'+
      '<button data-d="remover">Nao deveria estar aqui (3)</button>'+
      '<button data-d="pular">Pular</button>'+
    '</div>'+
    '<p class="atalho">Teclas 1, 2 e 3. A decisao e gravada na hora em dados/posicoes.json.</p>'+
    '</div>';
}

function decidir(d){
  var pend=ITENS.filter(function(x){return !(x.revisado||x.revisao&&x.revisao.resultado);});
  if(!pend.length) return;
  var it=pend[0];
  if(d==='pular'){ ITENS.splice(ITENS.indexOf(it),1); ITENS.push(it); desenhar(); return; }
  var nota=(document.getElementById('nota')||{}).value||'';
  if(d!=='confere' && !nota.trim()){
    alert('Escreva o que esta errado. Problema sem descricao nao da para consertar depois.');
    document.getElementById('nota').focus(); return;
  }
  fetch('/api/decidir',{method:'POST',headers:{'content-type':'application/json'},
    body:JSON.stringify({id:it.id,decisao:d,nota:nota})})
    .then(function(r){return r.json();})
    .then(function(r){
      if(r.erro){ alert(r.erro); return; }
      it.revisado=(d==='confere'); it.revisao={resultado:d,nota:nota};
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
        ok = gravar(c.get("id"), c["decisao"], c.get("nota", ""))
        self._envia(json.dumps({"ok": ok} if ok else {"erro": "posicao nao encontrada"}))

    def log_message(self, *a):
        pass


def main():
    origem = DADOS / "posicoes.json"
    backup = DADOS / "posicoes.json.antes-da-revisao"
    if not backup.exists():
        shutil.copy2(origem, backup)
        print(f"copia de seguranca: {backup.name}")

    itens = montar_itens()
    pend = [x for x in itens if not (x["revisado"] or x["revisao"])]
    print(f"{len(itens)} posicoes · {len(pend)} ainda sem decisao")
    print("ordem: fonte secundaria e conferencia fraca primeiro")
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
