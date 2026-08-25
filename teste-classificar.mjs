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

const py = spawn("python", ["classificar.py"], { cwd: process.cwd(), env: { ...process.env, PYTHONIOENCODING: "utf-8", BROWSER: "true" } });
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
      addEventListener() {}, querySelectorAll: (s) => el._achar(s),
      _achar(sel) {
        // basta reconhecer os seletores que a pagina usa
        const m = [...el._html.matchAll(/<button([^>]*)>/g)];
        return m.filter(x => sel.includes(".temas") ? x[1].includes("data-t")
                          : sel.includes(".outros") ? x[1].includes("data-x") : true)
                .map(x => ({ getAttribute: (a) => (x[1].match(new RegExp(a + '="([^"]*)"')) || [])[1],
                             addEventListener() {} }));
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

  const disco = JSON.parse(fs.readFileSync("dados/_coleta_discursos.json", "utf8"))
    .registros.concat(JSON.parse(fs.readFileSync("dados/_coleta_legislativa.json", "utf8")).registros)
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
  const volta = JSON.parse(fs.readFileSync("dados/_coleta_discursos.json", "utf8"))
    .registros.concat(JSON.parse(fs.readFileSync("dados/_coleta_legislativa.json", "utf8")).registros)
    .find(r => r.id_registro === alvoId);
  ok(volta?._classificacao?.por === "modelo",
     "o teste desfaz a propria gravacao E devolve a classificacao do modelo");

  console.log(falhas ? `\n=== ${falhas} falha(s) ===` : "\n=== a tela funciona ===");
  py.kill();
  process.exit(falhas ? 1 : 0);
}

main().catch(e => { console.error(e); console.error(saidaPy); py.kill(); process.exit(1); });
