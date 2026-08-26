/* Testa a tela de classificacao rodando o JS DE VERDADE contra a API de
   verdade, num DOM de mentira.

   A licao que este teste existe para nao repetir: quando o revisar.py abriu em
   branco, o meu teste passou. Ele lia o TEXTO do arquivo Python em vez do valor
   que o Python produz — entao nao via que \n tinha virado quebra de linha real.
   Aqui o HTML vem do servidor rodando, que e o mesmo que o navegador recebe. */
import { spawn } from "node:child_process";
import vm from "node:vm";
import net from "node:net";
import fs from "node:fs";

const PORTA = 8766;
let falhas = 0;
const ok = (b, msg) => { console.log((b ? "OK   " : "FALHA") + "  " + msg); if (!b) falhas++; };

/* --sandbox: a tela trabalha numa COPIA dos arquivos. Antes o teste gravava no
   arquivo de verdade e limpava no fim — e as execucoes que morriam antes da
   limpeza deixaram SETE itens de SP marcados como decididos por gente, com tema
   errado, sem que ninguem os tivesse decidido. Limpeza depende de o teste chegar
   ao fim; copia nao depende de nada. */
const py = spawn("python", ["classificar.py", "--sandbox"], { cwd: process.cwd(), env: { ...process.env, PYTHONIOENCODING: "utf-8", BROWSER: "true" } });
let saidaPy = "";
py.stdout.on("data", d => saidaPy += d);
py.stderr.on("data", d => saidaPy += d);

const esperar = ms => new Promise(r => setTimeout(r, ms));

const portaOcupada = () => new Promise(resolve => {
  const s = net.connect(PORTA, "127.0.0.1");
  const fim = (v) => { s.destroy(); resolve(v); };
  s.on("connect", () => fim(true));
  s.on("error", () => fim(false));
  setTimeout(() => fim(false), 1500);
});

async function main() {
  // Recusa falar com servidor que nao e o nosso. Ja aconteceu: um classificar.py
  // de execucao anterior ficou segurando a porta, o teste conversou com o codigo
  // ANTIGO e reprovou mudanca que estava certa.
  // Conexao TCP crua, e nao fetch: fetch abortado deixa o undici estourando
  // uma assercao interna e derruba o processo antes de qualquer conferencia.
  if (await portaOcupada()) {
    console.log(`FALHA  ja havia algo escutando na porta ${PORTA} antes do teste subir.`);
    console.log(`       mate o processo antigo — o teste falaria com o codigo dele.`);
    py.kill(); process.exit(1);
  }

  // Espera por conexao TCP, e nao por fetch. fetch recusado (ECONNREFUSED)
  // estoura uma assercao interna do undici no Node 24 e derruba o processo
  // inteiro antes de qualquer conferencia rodar — o teste morria sem dizer nada.
  let subiu = false;
  for (let n = 0; n < 30; n++) {
    await esperar(400);
    if (await portaOcupada()) { subiu = true; break; }
  }
  if (!subiu) { console.log("FALHA  o servidor nao subiu"); console.log(saidaPy); py.kill(); process.exit(1); }

  const html = await (await fetch(`http://localhost:${PORTA}/`)).text();
  const dados = await (await fetch(`http://localhost:${PORTA}/api/itens`)).json();

  ok(html.includes("<script>"), "a pagina traz o bloco de script");
  ok(!/\n/.test(html.match(/textContent=s==null[^\n]*/)?.[0] ?? "x"),
     "nenhum literal JS foi quebrado por escape do Python");
  ok(dados.itens.length > 0 && dados.itens.length < 100,
     `a API devolve so o que precisa do olho humano (${dados.itens.length} de 304)`);
  ok(dados.itens.every(x => x.minha !== null),
     "todo item da fila ja traz a classificacao que o modelo propos");
  ok(dados.itens.some(x => x.precisa_de_olho),
     "a fila inclui as escolhas editoriais");
  // Onde a gravacao acontece de fato. Com --sandbox e uma copia temporaria;
  // conferir no arquivo de verdade faria o teste passar por coincidencia.
  const PASTA = dados.pasta;
  ok(!!PASTA && /sandbox/i.test(PASTA), `a tela grava numa copia (${PASTA})`);
  ok(dados.temas.length === 10, `a API devolve os 10 temas (${dados.temas.length})`);

  // -------- ordem: as candidaturas hoje vazias tem de vir primeiro
  const comOlho = dados.itens.filter(x => x.precisa_de_olho).length;
  ok(dados.itens.slice(0, comOlho).every(x => x.precisa_de_olho),
     `os editoriais vem primeiro (${comOlho} deles)`);

  // -------- roda o JS num DOM de mentira
  const els = new Map();
  const novo = (id) => {
    const el = {
      id, _html: "", style: {}, tagName: "DIV",
      // addEventListener GUARDA o ouvinte, e querySelectorAll devolve SEMPRE o
      // mesmo objeto para o mesmo DOM. Com stub vazio e elemento descartavel,
      // os botoes nunca eram exercidos — e um botao quebrado passava no teste.
      _ouvintes: {},
      addEventListener(ev, fn) { (el._ouvintes[ev] = el._ouvintes[ev] || []).push(fn); },
      disparar(ev) { for (const fn of (el._ouvintes[ev] || [])) fn.call(el, { preventDefault() {} }); },
      querySelectorAll(s) {
        el._cache = el._cache || {};
        const k = s + "|" + el._html.length;
        if (!el._cache[k]) el._cache[k] = el._achar(s);
        return el._cache[k];
      },
      _achar(sel) {
        // basta reconhecer os seletores que a pagina usa
        const m = [...el._html.matchAll(/<button([^>]*)>/g)];
        return m.filter(x => sel.includes(".temas") ? x[1].includes("data-t")
                          : sel.includes(".outros") ? x[1].includes("data-x") : true)
                .map(x => {
                  const b = { _ouvintes: {},
                    getAttribute: (a) => (x[1].match(new RegExp(a + '="([^"]*)"')) || [])[1] ?? null,
                    addEventListener(ev, fn) { (b._ouvintes[ev] = b._ouvintes[ev] || []).push(fn); },
                    disparar(ev) { for (const fn of (b._ouvintes[ev] || [])) fn.call(b, { preventDefault() {} }); } };
                  return b;
                });
      },
      setAttribute() {}, getAttribute() { return null; },
    };
    let txt = "";
    Object.defineProperty(el, "textContent", {
      get: () => txt,
      set: v => { txt = v == null ? "" : String(v);
                  el._html = txt.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); },
    });
    Object.defineProperty(el, "innerHTML", { get: () => el._html, set: v => { el._html = v; } });
    return el;
  };
  const doc = {
    getElementById(i) { if (!els.has(i)) els.set(i, novo(i)); return els.get(i); },
    createElement: novo, addEventListener() {},
  };
  const chamadas = [];
  const ctx = {
    document: doc, console, JSON, RegExp, parseInt, setTimeout,
    fetch: async (u, opc) => {
      chamadas.push({ u, opc });
      if (String(u).endsWith("/api/itens")) return { json: async () => dados };
      return { json: async () => ({ ok: true }) };
    },
  };
  ctx.window = ctx; vm.createContext(ctx);
  const js = html.match(/<script>([\s\S]*?)<\/script>/)[1];
  try { new vm.Script(js).runInContext(ctx); } catch (e) { ok(false, "o script roda sem erro: " + e.message); }
  await esperar(120);

  const alvo = doc.getElementById("alvo")._html;
  ok(alvo.includes("<div class=\"cartao\">"), "desenha o cartao do primeiro item");
  ok((alvo.match(/data-t="/g) || []).length === 10, "oferece os 10 temas como botao");
  ok(alvo.includes("data-x=\"nenhum\""), 'oferece "nao se aplica"');
  ok(alvo.includes("abrir a peça na fonte oficial"), "mostra o link da fonte");
  ok(alvo.includes('class="minha"'), "mostra o que o modelo classificou");

  // -------- o clique tem de sair do botao e virar POST. Foi aqui que passou o
  //           defeito que apareceu no uso real da tela.
  const postsJS = [];
  ctx.fetch = async (u, opc) => {
    if (String(u).endsWith("/api/itens")) return { status: 200, json: async () => dados };
    postsJS.push(JSON.parse(opc.body));
    return { status: 200, json: async () => ({ ok: true }) };
  };
  const outros = doc.getElementById("alvo").querySelectorAll(".outros button");
  const semTema = outros.find(b => b.getAttribute("data-x") === "nenhum");
  ok(!!semTema, 'existe o botao "nao se aplica"');
  ok((semTema?._ouvintes?.click || []).length === 1,
     "o botao tem ouvinte de clique ligado");
  semTema?.disparar("click");
  await esperar(80);
  ok(postsJS.length === 1 && postsJS[0].motivo === "nenhum" && postsJS[0].temas.length === 0,
     `clicar em "nao se aplica" manda a decisao (${JSON.stringify(postsJS[0] || null)})`);

  const sub = doc.getElementById("sub").textContent;
  ok(/\d+ de \d+ conferidos/.test(sub), `mostra progresso: "${sub}"`);

  // -------- nao pode existir botao de confirmar em lote
  ok(!/confirmar todos|aceitar todos|em lote/i.test(html),
     "nao oferece confirmar em lote (cada item leva um olhar)");

  // -------- gravar de verdade e um item so
  const alvoId = dados.itens[0].id;
  const r = await fetch(`http://localhost:${PORTA}/api/classificar`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: alvoId, temas: ["t1"], motivo: "" }),
  });
  const jr = await r.json();
  ok(jr.ok === true, `grava a decisao de um item (${alvoId})`);

  // O item DECIDIDO sai da fila — e o comportamento certo, entao nao da para
  // confirmar a gravacao pela API. Confere no arquivo, que e onde ela mora.
  const depois = await (await fetch(`http://localhost:${PORTA}/api/itens`)).json();
  ok(!depois.itens.find(x => x.id === alvoId),
     "o item decidido sai da fila");

  const disco = JSON.parse(fs.readFileSync(PASTA + "/_coleta_discursos.json", "utf8"))
    .registros.concat(JSON.parse(fs.readFileSync(PASTA + "/_coleta_legislativa.json", "utf8")).registros)
    .find(r => r.id_registro === alvoId);
  ok(disco?._classificacao?.temas?.[0] === "t1", "a decisao fica gravada no arquivo");
  ok(disco?._classificacao?.por === "humano", "a decisao gravada fica marcada como humana");
  ok(typeof disco?._classificacao?.concordou === "boolean",
     "a gravacao registra se a pessoa concordou com o modelo");
  ok(Array.isArray(disco?._classificacao?.modelo_propos),
     "a gravacao guarda o que o modelo tinha proposto");

  // -------- recusa decisao vazia sem motivo
  const r2 = await fetch(`http://localhost:${PORTA}/api/classificar`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: alvoId, temas: [], motivo: "" }),
  });
  ok(r2.status === 400, "recusa decisao sem tema e sem motivo");

  // O teste gravou num arquivo de verdade. Desfaz. Decisao de teste nao pode
  // ficar valendo como decisao humana: e a unica coisa que este projeto trata
  // como definitiva, e um arquivo sujo de teste corromperia justamente isso.
  await fetch(`http://localhost:${PORTA}/api/limpar-teste`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: alvoId }),
  }).catch(() => {});
  const volta = JSON.parse(fs.readFileSync(PASTA + "/_coleta_discursos.json", "utf8"))
    .registros.concat(JSON.parse(fs.readFileSync(PASTA + "/_coleta_legislativa.json", "utf8")).registros)
    .find(r => r.id_registro === alvoId);
  ok(volta?._classificacao?.por === "modelo",
     "o teste desfaz a propria gravacao E devolve a classificacao do modelo");

  console.log(falhas ? `\n=== ${falhas} falha(s) ===` : "\n=== a tela funciona ===");
  await encerrar();
  process.exit(falhas ? 1 : 0);
}

/* Encerramento em duas etapas. process.exit() logo depois de py.kill() estoura
   uma assercao interna do libuv no Windows (UV_HANDLE_CLOSING): o processo sai
   enquanto o descritor do filho ainda esta fechando.

   Isso nao era so feio: ESCONDIA O ERRO DE VERDADE. Quando a migracao para
   dados/sp/ quebrou os caminhos deste teste, o ENOENT caiu aqui, o exit(1)
   estourou o libuv, e a saida mostrava so a assercao — nada sobre arquivo nao
   encontrado. Passei vinte minutos tratando como teste intermitente uma falha
   reproduzivel que a propria saida escondia. */
async function encerrar() {
  if (py.exitCode !== null || py.signalCode !== null) return;
  await new Promise(resolve => {
    py.once("close", resolve);
    py.kill();
    setTimeout(resolve, 2000);   // nao pendura se o filho travar
  });
  await esperar(60);
}

main().catch(async (e) => {
  console.error("ERRO NO TESTE:", e && e.message ? e.message : e);
  if (e && e.stack) console.error(e.stack.split("\n").slice(1, 4).join("\n"));
  if (saidaPy.trim()) console.error("--- saida do classificar.py ---\n" + saidaPy);
  await encerrar();
  process.exit(1);
});
