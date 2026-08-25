/**
 * Página privada de moderação da fila de perguntas.
 *
 * Servida pelo próprio worker, e não pelo GitHub Pages, por um motivo: assim o
 * token de acesso nunca precisa existir no repositório público do site.
 *
 * O que ela faz: mostra as perguntas que os visitantes deixaram sem resposta,
 * agrupadas por candidatura e tema, e monta UMA mensagem formal representando
 * todas as perguntas selecionadas. Quem envia é a curadoria, do próprio e-mail.
 * Nada sai daqui sozinho.
 *
 * O JavaScript de dentro da página usa concatenação e evita template literals
 * de propósito: o arquivo inteiro já é um template literal, e aninhar os dois
 * vira um campo minado de escapes.
 */
export const PAGINA_ADMIN = `<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Moderação da fila — Senado SP 2026</title>
<style>
  :root{
    --ground:#F7F8F7; --surface:#FFFFFF; --surface-2:#EDEFED;
    --ink:#16181A; --ink-2:#33383C; --muted:#5C6469;
    --rule:#D9DEDA; --rule-forte:#A9B2AC;
    --acento:#1F5C46; --alerta:#8A2F1F; --alerta-bg:#FBF0EE;
  }
  @media (prefers-color-scheme: dark){
    :root{
      --ground:#141715; --surface:#1C201E; --surface-2:#252A27;
      --ink:#EEF1EF; --ink-2:#C8CFCA; --muted:#98A29B;
      --rule:#333A36; --rule-forte:#4E5852;
      --acento:#6FC091; --alerta:#F0897C; --alerta-bg:#2A1C19;
    }
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--ground);color:var(--ink);
    font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;padding:24px 18px 80px}
  main{max-width:900px;margin:0 auto}
  h1{font-size:1.4rem;margin:0 0 4px}
  .sub{color:var(--muted);font-size:.9rem;margin:0 0 24px}
  fieldset{border:1px solid var(--rule);border-radius:6px;padding:16px;margin:0 0 20px;
    background:var(--surface)}
  legend{padding:0 8px;font-weight:600;font-size:.95rem}
  label{display:block;font-size:.88rem;color:var(--ink-2);margin-bottom:6px}
  input[type=password],input[type=text],textarea{width:100%;font:inherit;padding:10px 12px;
    border:1px solid var(--rule-forte);border-radius:4px;background:var(--surface);color:var(--ink)}
  textarea{font-size:.9rem;line-height:1.55;resize:vertical}
  button{font:inherit;font-weight:600;padding:9px 15px;border-radius:4px;cursor:pointer;
    border:1px solid var(--acento);background:var(--acento);color:var(--ground)}
  button.sec{background:transparent;color:var(--ink);border-color:var(--rule-forte)}
  button:disabled{opacity:.5;cursor:not-allowed}
  button:focus-visible,input:focus-visible,textarea:focus-visible,
  a:focus-visible,summary:focus-visible{outline:3px solid var(--acento);outline-offset:2px}
  .barra{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:14px}
  .grupo{background:var(--surface);border:1px solid var(--rule);border-radius:6px;
    margin-bottom:16px;overflow:hidden}
  .grupo > h2{margin:0;padding:13px 16px;background:var(--surface-2);
    border-bottom:1px solid var(--rule);font-size:1rem;
    display:flex;flex-wrap:wrap;gap:10px;align-items:baseline}
  .num{font-variant-numeric:tabular-nums;font-weight:400;color:var(--muted);font-size:.85rem}
  .corpo{padding:14px 16px}
  .sem-contato{background:var(--alerta-bg);border:1px solid var(--alerta);color:var(--ink-2);
    border-radius:4px;padding:10px 13px;font-size:.86rem;margin-bottom:12px}
  .sem-contato b{color:var(--alerta)}
  .tema{margin-top:14px}
  .tema:first-child{margin-top:0}
  .tema > h3{font-size:.86rem;text-transform:uppercase;letter-spacing:.06em;
    color:var(--muted);margin:0 0 8px}
  .q{display:flex;gap:10px;align-items:flex-start;padding:9px 0;border-top:1px solid var(--rule)}
  .q:first-of-type{border-top:0}
  .q input{margin-top:5px;width:17px;height:17px;flex:0 0 auto;accent-color:var(--acento)}
  .q .txt{flex:1;font-size:.94rem}
  .q .quando{display:block;color:var(--muted);font-size:.78rem;font-variant-numeric:tabular-nums;
    margin-top:3px}
  .vazio{color:var(--muted);padding:26px 0;text-align:center}
  .erro{background:var(--alerta-bg);border:1px solid var(--alerta);border-radius:4px;
    padding:11px 14px;color:var(--ink-2);margin-top:12px}
  .oculto{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
  details{margin-top:18px}
  summary{cursor:pointer;font-weight:600;font-size:.92rem}
  .hist{font-size:.86rem;color:var(--muted);margin-top:10px}
  .hist li{margin-top:5px}
  .form-resp{margin-top:16px;padding:14px 16px;background:var(--surface-2);
    border:1px solid var(--rule-forte);border-radius:5px}
  .form-resp h3{margin:0 0 4px;font-size:.96rem}
  .form-resp .dica{font-size:.84rem;color:var(--muted);margin:0 0 12px}
  .form-resp .campo{margin-top:10px}
  .form-resp select,.form-resp input[type=date]{width:100%;font:inherit;padding:9px 11px;
    border:1px solid var(--rule-forte);border-radius:4px;background:var(--surface);color:var(--ink)}
  .form-resp .par{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
  .q .achar{font:inherit;font-size:.78rem;font-weight:600;padding:3px 9px;flex:0 0 auto;
    border:1px solid var(--rule-forte);background:transparent;color:var(--ink-2);border-radius:3px}
  .fontes{margin:8px 0 4px 27px;padding:12px 14px;background:var(--surface-2);
    border:1px solid var(--rule);border-radius:5px;font-size:.9rem}
  .fontes > p.cabeca{margin:0 0 10px;font-size:.83rem;color:var(--muted)}
  .fontes ol{margin:0;padding-left:20px}
  .fontes li{margin-top:11px}
  .fontes li:first-child{margin-top:0}
  .fontes .meta{display:block;font-size:.79rem;color:var(--muted);margin-top:2px}
  .fontes .trecho{display:block;margin-top:4px}
  .fontes .porque{display:block;margin-top:4px;font-size:.83rem;color:var(--muted)}
  .fontes .tipo{display:inline-block;font-size:.72rem;font-weight:700;letter-spacing:.05em;
    text-transform:uppercase;padding:1px 6px;border-radius:3px;border:1px solid var(--rule-forte)}
  /* Fonte cujo TIPO nao sustenta o que foi perguntado tem de PARECER insuficiente:
     era esse o erro original — cadastro apresentado como se fosse fonte de proposta. */
  .fontes li.insuf{opacity:.72}
  .fontes .insuf .tipo{border-color:var(--erro);color:var(--erro)}
  .fontes .aviso-tipo{display:block;margin-top:4px;font-size:.82rem;color:var(--erro);
    font-weight:600}
</style>
</head>
<body>
<main>
  <h1>Moderação da fila</h1>
  <p class="sub">Perguntas que os visitantes deixaram porque o acervo não respondeu.
     Nada sai daqui sozinho: você escolhe, monta a mensagem e envia do seu próprio e-mail.</p>

  <fieldset id="caixa-token">
    <legend>Acesso</legend>
    <label for="tok">Token de moderação</label>
    <input type="password" id="tok" autocomplete="current-password">
    <div class="barra"><button type="button" id="entrar">Entrar</button></div>
    <div id="erro-token"></div>
  </fieldset>

  <div id="painel" hidden>
    <div class="barra" style="margin:0 0 18px">
      <button type="button" class="sec" id="recarregar">Recarregar</button>
      <span class="num" id="resumo-fila"></span>
    </div>
    <div id="lista" aria-live="polite"></div>
    <details id="historico" hidden>
      <summary>Já decididas</summary>
      <ul class="hist" id="lista-hist"></ul>
    </details>
  </div>
</main>

<script>
(function(){
  "use strict";
  var TOKEN = "";
  var DADOS = null;

  function esc(s){
    return String(s == null ? "" : s).replace(/[&<>"']/g, function(c){
      return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];
    });
  }
  function quando(iso){
    var d = new Date(iso);
    if (isNaN(d)) return iso || "";
    var p = function(n){ return String(n).padStart(2,"0"); };
    return p(d.getDate())+"/"+p(d.getMonth()+1)+"/"+d.getFullYear()+" "+p(d.getHours())+"h"+p(d.getMinutes());
  }
  function api(caminho, opcoes){
    opcoes = opcoes || {};
    opcoes.headers = Object.assign({"x-token": TOKEN}, opcoes.headers || {});
    return fetch(caminho, opcoes).then(function(r){ return r.json(); });
  }

  document.getElementById("entrar").addEventListener("click", entrar);
  document.getElementById("tok").addEventListener("keydown", function(e){
    if (e.key === "Enter") entrar();
  });
  document.getElementById("recarregar").addEventListener("click", carregar);

  function entrar(){
    TOKEN = document.getElementById("tok").value.trim();
    if (!TOKEN) return;
    carregar();
  }

  function carregar(){
    var alvoErro = document.getElementById("erro-token");
    alvoErro.innerHTML = "";
    api("/fila").then(function(d){
      if (d.erro){
        alvoErro.innerHTML = '<div class="erro">' + esc(d.erro) + "</div>";
        return;
      }
      try { sessionStorage.setItem("tok_mod", TOKEN); } catch(e){}
      DADOS = d;
      document.getElementById("caixa-token").hidden = true;
      document.getElementById("painel").hidden = false;
      desenhar();
    }).catch(function(){
      alvoErro.innerHTML = '<div class="erro">Não consegui falar com o servidor.</div>';
    });
  }

  function nomeCand(id){
    var c = DADOS.catalogo.candidaturas.filter(function(x){ return x.id === id; })[0];
    return c ? c : { id: id, nome: id, partido: "", numero: "", email: null };
  }
  function nomeTema(id){
    var t = DADOS.catalogo.temas.filter(function(x){ return x.id === id; })[0];
    return t ? t.nome : "Sem tema identificado";
  }

  function desenhar(){
    var pend = DADOS.perguntas.filter(function(p){ return p.estado === "pendente"; });
    var feitas = DADOS.perguntas.filter(function(p){ return p.estado !== "pendente"; });

    document.getElementById("resumo-fila").textContent =
      pend.length + " pendente(s) · " + feitas.length + " já decidida(s)";

    var lista = document.getElementById("lista");
    if (!pend.length){
      lista.innerHTML = '<p class="vazio">Nenhuma pergunta pendente.</p>';
    } else {
      /* Agrupa por candidatura e, dentro dela, por tema. A contagem por grupo e
         o ponto todo: uma pergunta e ignoravel, quinze nao sao. */
      var porCand = {};
      pend.forEach(function(p){
        (porCand[p.id_candidatura] = porCand[p.id_candidatura] || []).push(p);
      });
      var ordem = Object.keys(porCand).sort(function(a,b){
        return porCand[b].length - porCand[a].length;
      });

      lista.innerHTML = ordem.map(function(cid){
        var c = nomeCand(cid), itens = porCand[cid];
        var porTema = {};
        itens.forEach(function(p){ (porTema[p.id_tema || ""] = porTema[p.id_tema || ""] || []).push(p); });

        /* Instagram e atalho manual, nao envio. A API so deixa responder quem
           escreveu nas ultimas 24h; automatizar conta pessoal por fora viola os
           termos. Entao o maximo honesto e abrir a conversa com o texto copiado. */
        var ig = c.instagram
          ? '<p style="font-size:.86rem;color:var(--muted);margin:0 0 12px">Instagram: ' +
            '<a href="https://ig.me/m/' + esc(c.instagram.replace(/^@/, "")) + '" ' +
            'target="_blank" rel="noopener">abrir conversa com @' +
            esc(c.instagram.replace(/^@/, "")) + '</a> — abre a DM; o texto você cola. ' +
            'Não dá para enviar automaticamente: a API do Instagram só permite responder ' +
            'quem escreveu nas últimas 24h.</p>'
          : "";

        var aviso = c.email ? "" :
          '<div class="sem-contato"><b>Sem contato oficial registrado.</b> ' +
          'Dá para moderar e agrupar, mas ainda não dá para enviar: só temos e-mail ' +
          'das candidaturas com mandato. O dataset de redes sociais do TSE, que os ' +
          'próprios candidatos preenchem no registro, está pendente de download.</div>';

        var blocos = Object.keys(porTema).map(function(tid){
          return '<div class="tema"><h3>' + esc(nomeTema(tid)) + " · " + porTema[tid].length +
            " pergunta(s)</h3>" +
            porTema[tid].map(function(p){
              return '<div class="q"><input type="checkbox" id="c-' + esc(p.id) + '" value="' +
                esc(p.id) + '" data-cand="' + esc(cid) + '" checked>' +
                '<label class="txt" for="c-' + esc(p.id) + '">' + esc(p.pergunta) +
                '<span class="quando">recebida em ' + esc(quando(p.criada_em)) + "</span></label>" +
                '<button type="button" class="achar" data-achar="' + esc(p.id) +
                '" data-cand="' + esc(cid) + '">Buscar fontes</button></div>' +
                '<div data-fontes="' + esc(p.id) + '"></div>';
            }).join("") + "</div>";
        }).join("");

        return '<section class="grupo"><h2>' + esc(c.nome) +
          ' <span class="num">' + esc(c.partido) + " · " + esc(c.numero) + "</span>" +
          '<span class="num">' + itens.length + " pergunta(s) na fila</span></h2>" +
          '<div class="corpo">' + aviso + ig + blocos +
          '<div class="barra">' +
            '<button type="button" data-montar="' + esc(cid) + '"' + (c.email ? "" : " disabled") +
              ">Montar mensagem</button>" +
            '<button type="button" class="sec" data-marcar="enviada" data-cand="' + esc(cid) + '">Marcar como enviadas</button>' +
            '<button type="button" class="sec" data-marcar="descartada" data-cand="' + esc(cid) + '">Descartar</button>' +
            (c.instagram
              ? '<button type="button" class="sec" data-dm="' + esc(cid) + '">Montar mensagem para Instagram</button>'
              : "") +
            '<button type="button" class="sec" data-resposta="' + esc(cid) + '">Registrar resposta recebida</button>' +
          "</div>" +
          '<div data-saida="' + esc(cid) + '"></div>' +
          "</div></section>";
      }).join("");
    }

    /* Sempre visivel, com contagem no proprio titulo: secao que aparece e
       desaparece deixa a pessoa sem saber se existe. */
    var ROTULO = { enviada: "enviada ao gabinete", descartada: "descartada",
                   respondida: "respondida", pendente: "pendente" };
    var hist = document.getElementById("historico");
    hist.hidden = false;
    hist.querySelector("summary").textContent =
      feitas.length ? "Já decididas (" + feitas.length + ")" : "Já decididas (nenhuma ainda)";
    document.getElementById("lista-hist").innerHTML = feitas.length
      ? feitas.slice(0, 300).map(function(p){
          return "<li><strong>" + esc(ROTULO[p.estado] || p.estado) + "</strong> · " +
            esc(nomeCand(p.id_candidatura).nome) + " · " + esc(p.pergunta) +
            (p.decidida_em ? ' <span class="num">em ' + esc(quando(p.decidida_em)) + "</span>" : "") +
            (p.nota ? "<br><em>" + esc(p.nota) + "</em>" : "") + "</li>";
        }).join("")
      : "<li>Nenhuma pergunta foi enviada, descartada ou respondida até agora.</li>";
  }

  function selecionadas(cid){
    return Array.prototype.slice.call(
      document.querySelectorAll('input[type=checkbox][data-cand="' + cid + '"]:checked')
    ).map(function(i){ return i.value; });
  }

  function montarMensagem(cid){
    var c = nomeCand(cid);
    var ids = selecionadas(cid);
    var itens = DADOS.perguntas.filter(function(p){ return ids.indexOf(p.id) >= 0; });
    if (!itens.length) return null;

    var porTema = {};
    itens.forEach(function(p){ (porTema[p.id_tema || ""] = porTema[p.id_tema || ""] || []).push(p); });

    var n = itens.length;
    var corpo =
      "Prezada assessoria de " + c.nome + ",\\n\\n" +
      "Escrevo em nome do projeto Senado por São Paulo 2026 " +
      "(https://kvgs.github.io/senado-sp-2026/), um site independente e sem fins " +
      "lucrativos que reúne as propostas das candidaturas ao Senado por São Paulo, " +
      "sempre com a fonte oficial de cada informação.\\n\\n" +
      "Procuramos nas fontes públicas disponíveis e não localizamos posição registrada " +
      "sobre os pontos abaixo. " +
      (n === 1
        ? "Um eleitor nos perguntou o seguinte:"
        : n + " eleitores nos perguntaram sobre estes pontos:") + "\\n\\n";

    Object.keys(porTema).forEach(function(tid){
      corpo += nomeTema(tid).toUpperCase() + "\\n";
      porTema[tid].forEach(function(p){ corpo += "  - " + p.pergunta + "\\n"; });
      corpo += "\\n";
    });

    corpo +=
      "Qualquer resposta será publicada na íntegra, identificada como declaração da " +
      "candidatura e com a data em que foi recebida. Se a candidatura preferir não " +
      "responder, registraremos apenas que a pergunta foi feita, sem interpretar o " +
      "silêncio.\\n\\n" +
      "Se preferirem indicar um documento público que já trate do assunto, também " +
      "serve — e é a forma que preferimos, porque podemos citar a fonte original.\\n\\n" +
      "Agradeço a atenção.\\n";

    var assunto = "Pergunta de eleitores sobre a candidatura ao Senado por SP" +
      (n > 1 ? " (" + n + " perguntas)" : "");

    return { para: c.email, assunto: assunto, corpo: corpo, ids: ids, cand: c };
  }

  /* Versao curta, para mensagem direta. Nao e o e-mail encurtado: DM com tom de
     oficio nao e lida. Mantem o unico compromisso que nao pode sair — publicar
     a resposta na integra e nao interpretar silencio. */
  function montarDM(cid){
    var c = nomeCand(cid);
    var ids = selecionadas(cid);
    var itens = DADOS.perguntas.filter(function(p){ return ids.indexOf(p.id) >= 0; });
    if (!itens.length) return null;

    var n = itens.length;
    var txt = "Olá! Escrevo do projeto Senado por São Paulo 2026 " +
      "(kvgs.github.io/senado-sp-2026), um site independente e sem fins lucrativos que reúne " +
      "as propostas das candidaturas ao Senado por SP, sempre com a fonte de cada informação.\\n\\n" +
      "Procuramos nas fontes públicas e não localizamos posição registrada sobre " +
      (n === 1 ? "este ponto:" : "estes pontos:") + "\\n\\n";
    itens.forEach(function(p){ txt += "• " + p.pergunta + "\\n"; });
    txt += "\\n" + (n === 1 ? "Um eleitor perguntou" : n + " eleitores perguntaram") +
      " isso pelo site. Se puderem responder, publicamos na íntegra, identificado como " +
      "declaração da candidatura e com a data. Se preferirem indicar um documento público " +
      "que já trate do assunto, melhor ainda.\\n\\nObrigada!";

    return { arroba: c.instagram.replace(/^@/, ""), texto: txt, ids: ids, cand: c };
  }

  document.addEventListener("click", function(e){
    var b = e.target.closest ? e.target.closest("button") : null;
    if (!b) return;

    if (b.dataset.montar){
      var cid = b.dataset.montar;
      var m = montarMensagem(cid);
      var saida = document.querySelector('[data-saida="' + cid + '"]');
      if (!m){ saida.innerHTML = '<div class="erro">Nenhuma pergunta selecionada.</div>'; return; }

      /* Campo copiavel ALEM do link mailto: cliente de e-mail engasga com corpo
         longo, e link que morre em silencio e pior que link nenhum. */
      var href = "mailto:" + encodeURIComponent(m.para) +
        "?subject=" + encodeURIComponent(m.assunto) +
        "&body=" + encodeURIComponent(m.corpo);

      saida.innerHTML =
        '<div style="margin-top:16px">' +
        '<p style="font-size:.86rem;color:var(--muted)">Para: <strong>' + esc(m.para) + "</strong>" +
        ' · fonte do contato: ' + esc(m.cand.email_fonte || "não registrada") + "</p>" +
        '<label for="msg-' + esc(cid) + '">Mensagem (' + m.ids.length + " pergunta(s))</label>" +
        '<textarea id="msg-' + esc(cid) + '" rows="16" readonly></textarea>' +
        '<div class="barra">' +
          '<a href="' + esc(href) + '"><button type="button">Abrir no cliente de e-mail</button></a>' +
          '<button type="button" class="sec" data-copiar="' + esc(cid) + '">Copiar mensagem</button>' +
        "</div></div>";

      var ta = document.getElementById("msg-" + cid);
      ta.value = "Assunto: " + m.assunto + "\\n\\n" + m.corpo;
      ta.focus(); ta.select();
      return;
    }

    if (b.dataset.dm){
      var cidD = b.dataset.dm;
      var m = montarDM(cidD);
      var saidaD = document.querySelector('[data-saida="' + cidD + '"]');
      if (!m){ saidaD.innerHTML = '<div class="erro">Nenhuma pergunta selecionada.</div>'; return; }

      saidaD.innerHTML =
        '<div class="form-resp"><h3>Mensagem para @' + esc(m.arroba) + "</h3>" +
        '<p class="dica">O Instagram não permite enviar por fora do aplicativo: o link abre a ' +
        'conversa, e o texto você cola. Não é limitação nossa — a API só deixa responder quem ' +
        'escreveu nas últimas 24h.</p>' +
        '<label for="dm-' + esc(cidD) + '">Texto (' + m.ids.length + " pergunta(s)) · " +
        m.texto.length + " caracteres</label>" +
        '<textarea id="dm-' + esc(cidD) + '" rows="12" readonly></textarea>' +
        '<div class="barra">' +
          '<button type="button" data-copiar="dm-' + esc(cidD) + '">Copiar texto</button>' +
          '<a href="https://ig.me/m/' + esc(m.arroba) + '" target="_blank" rel="noopener">' +
          '<button type="button" class="sec">Abrir conversa no Instagram</button></a>' +
        "</div></div>";

      var ta = document.getElementById("dm-" + cidD);
      ta.value = m.texto; ta.focus(); ta.select();
      return;
    }

    if (b.dataset.achar){
      var pid = b.dataset.achar;
      var pergObj = DADOS.perguntas.filter(function(x){ return x.id === pid; })[0];
      var caixa = document.querySelector('[data-fontes="' + pid + '"]');
      if (!pergObj || !caixa) return;

      b.disabled = true; b.textContent = "Buscando…";
      caixa.innerHTML = '<div class="fontes"><p class="cabeca">Procurando fontes públicas…</p></div>';

      api("/pesquisar", {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify({ pergunta: pergObj.pergunta, id_candidatura: b.dataset.cand })
      }).then(function(r){
        b.disabled = false; b.textContent = "Buscar de novo";
        if (r.erro){ caixa.innerHTML = '<div class="erro">' + esc(r.erro) + "</div>"; return; }

        if (r.nada || !r.fontes || !r.fontes.length){
          caixa.innerHTML = '<div class="fontes"><p class="cabeca">Nada encontrado.</p><p>' +
            esc(r.nota || r.bruto || "A busca não localizou material sobre este assunto.") +
            '</p><p class="porque" style="margin-top:8px">Isso não significa que a candidatura ' +
            'não tenha posição — significa que não localizamos fonte pública. Continua valendo ' +
            'perguntar ao gabinete.</p></div>';
          return;
        }

        caixa.innerHTML = '<div class="fontes">' +
          '<p class="cabeca"><strong>' + r.fontes.length + ' fonte(s) para você conferir.</strong> ' +
          'Nada disto entrou no acervo. Abra cada link e decida — o modelo achou as páginas, ' +
          'mas quem lê e julga é você.</p><ol>' +
          r.fontes.map(function(f){
            return '<li' + (f.suficiente === false ? ' class="insuf"' : '') + '>' +
              '<a href="' + esc(f.url) + '" target="_blank" rel="noopener">' +
              esc(f.titulo || f.url) + "</a>" +
              '<span class="meta">' + (f.tipo ? '<span class="tipo">' + esc(f.tipo) + "</span> " : "") +
              esc(f.veiculo || "veículo não identificado") + " · " +
              esc(f.data || "data não identificada") + "</span>" +
              (f.trecho ? '<span class="trecho">' + esc(f.trecho) + "</span>" : "") +
              (f.suficiente === false
                ? '<span class="aviso-tipo">Este tipo de fonte não sustenta o que foi ' +
                  'perguntado — serve de pista, não de fonte.</span>'
                : "") +
              (f.porque ? '<span class="porque">' + esc(f.porque) + "</span>" : "") +
              "</li>";
          }).join("") + "</ol></div>";
      }).catch(function(){
        b.disabled = false; b.textContent = "Buscar fontes";
        caixa.innerHTML = '<div class="erro">Não consegui falar com o servidor.</div>';
      });
      return;
    }

    if (b.dataset.resposta){
      var cidR = b.dataset.resposta;
      var cR = nomeCand(cidR);
      var selR = selecionadas(cidR);
      var saidaR = document.querySelector('[data-saida="' + cidR + '"]');
      var hoje = new Date().toISOString().slice(0, 10);

      var temas = DADOS.catalogo.temas.map(function(x){
        return '<option value="' + esc(x.id) + '">' + esc(x.nome) + "</option>";
      }).join("");

      saidaR.innerHTML =
        '<div class="form-resp"><h3>Resposta de ' + esc(cR.nome) + "</h3>" +
        '<p class="dica">Cole o texto exatamente como veio, sem editar nem resumir — ' +
        'prometemos publicar na íntegra. Não inclua telefone nem dado pessoal de assessor: ' +
        'isso não vai para o site.</p>' +
        '<div class="par">' +
          '<div><label for="r-data-' + esc(cidR) + '">Data que consta no e-mail</label>' +
          '<input type="date" id="r-data-' + esc(cidR) + '" value="' + hoje + '"></div>' +
          '<div><label for="r-canal-' + esc(cidR) + '">Chegou por onde</label>' +
          '<select id="r-canal-' + esc(cidR) + '"><option value="email">E-mail</option>' +
          '<option value="instagram">Instagram</option><option value="outro">Outro</option></select></div>' +
        "</div>" +
        '<div class="campo"><label for="r-de-' + esc(cidR) + '">De qual endereço veio</label>' +
        '<input type="text" id="r-de-' + esc(cidR) + '" placeholder="assessoria@exemplo.leg.br"></div>' +
        '<div class="campo"><label for="r-tema-' + esc(cidR) + '">Tema (opcional)</label>' +
        '<select id="r-tema-' + esc(cidR) + '"><option value="">Não classificar agora</option>' +
        temas + "</select></div>" +
        '<div class="campo"><label for="r-txt-' + esc(cidR) + '">Texto da resposta, na íntegra</label>' +
        '<textarea id="r-txt-' + esc(cidR) + '" rows="10"></textarea></div>' +
        '<p class="dica" style="margin:10px 0 0">' +
        (selR.length
          ? "As " + selR.length + " pergunta(s) marcadas acima serão registradas como respondidas."
          : "Nenhuma pergunta marcada acima: a resposta fica registrada sem ligar a nenhuma pergunta da fila.") +
        "</p>" +
        '<div class="barra"><button type="button" data-salvar-resp="' + esc(cidR) + '">Registrar resposta</button>' +
        '<button type="button" class="sec" data-cancelar-resp="' + esc(cidR) + '">Cancelar</button></div>' +
        '<div data-msg-resp="' + esc(cidR) + '"></div></div>';
      document.getElementById("r-de-" + cidR).focus();
      return;
    }

    if (b.dataset.cancelarResp){
      document.querySelector('[data-saida="' + b.dataset.cancelarResp + '"]').innerHTML = "";
      return;
    }

    if (b.dataset.salvarResp){
      var cidS = b.dataset.salvarResp;
      var msg = document.querySelector('[data-msg-resp="' + cidS + '"]');
      var corpo = {
        id_candidatura: cidS,
        recebida_em: document.getElementById("r-data-" + cidS).value,
        canal: document.getElementById("r-canal-" + cidS).value,
        remetente: document.getElementById("r-de-" + cidS).value.trim(),
        id_tema: document.getElementById("r-tema-" + cidS).value,
        texto: document.getElementById("r-txt-" + cidS).value,
        perguntas_ids: selecionadas(cidS)
      };
      b.disabled = true;
      api("/responder", {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify(corpo)
      }).then(function(r){
        b.disabled = false;
        if (r.erro){ msg.innerHTML = '<div class="erro">' + esc(r.erro) + "</div>"; return; }
        msg.innerHTML = '<div class="erro" style="background:var(--surface);border-color:var(--acento)">' +
          "Resposta registrada. " + r.perguntas_marcadas + " pergunta(s) marcadas como respondidas. " +
          "Para publicar no site, rode <code>python promover.py</code> na pasta agente." + "</div>";
        setTimeout(carregar, 1800);
      });
      return;
    }

    if (b.dataset.copiar){
      /* Aceita tanto "msg-<cid>" (e-mail) quanto "dm-<cid>" (Instagram). */
      var alvoId = b.dataset.copiar;
      var ta2 = document.getElementById(alvoId) || document.getElementById("msg-" + alvoId);
      ta2.focus(); ta2.select();
      try { document.execCommand("copy"); b.textContent = "Copiada"; } catch(err){}
      if (navigator.clipboard) navigator.clipboard.writeText(ta2.value).catch(function(){});
      return;
    }

    if (b.dataset.marcar){
      var cid2 = b.dataset.cand, estado = b.dataset.marcar;
      var ids2 = selecionadas(cid2);
      var saida2 = document.querySelector('[data-saida="' + cid2 + '"]');
      if (!ids2.length){ saida2.innerHTML = '<div class="erro">Nenhuma pergunta selecionada.</div>'; return; }
      if (estado === "descartada" &&
          !confirm("Descartar " + ids2.length + " pergunta(s)? Elas saem da fila.")) return;

      b.disabled = true;
      api("/decidir", {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify({ids: ids2, estado: estado})
      }).then(function(r){
        b.disabled = false;
        if (r.erro){ saida2.innerHTML = '<div class="erro">' + esc(r.erro) + "</div>"; return; }
        carregar();
      });
    }
  });

  /* Token guardado na aba, nao no disco: fechou a aba, some. */
  try {
    var guardado = sessionStorage.getItem("tok_mod");
    if (guardado){ TOKEN = guardado; document.getElementById("tok").value = guardado; carregar(); }
  } catch(e){}
})();
</script>
</body>
</html>`;
