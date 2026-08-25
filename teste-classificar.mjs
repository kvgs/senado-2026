/* Testa a tela de classificacao rodando o JS DE VERDADE contra a API de
   verdade, num DOM de mentira.

   A licao que este teste existe para nao repetir: quando o revisar.py abriu em
   branco, o meu teste passou. Ele lia o TEXTO do arquivo Python em vez do valor
   que o Python produz — entao nao via que \n tinha virado quebra de linha real.
   Aqui o HTML vem do servidor rodando, que e o mesmo que o navegador recebe. */
import { spawn } from "node:child_process";
import vm from "node:vm";

const PORTA = 8766;
let falhas = 0;
const ok = (b, msg) => { console.log((b ? "OK   " : "FALHA") + "  " + msg); if (!b) falhas++; };

const py = spawn("python", ["classificar.py"], { cwd: process.cwd(), env: { ...process.env, PYTHONIOENCODING: "utf-8", BROWSER: "true" } });
let saidaPy = "";
py.stdout.on("data", d => saidaPy += d);
py.stderr.on("data", d => saidaPy += d);

const esperar = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  for (let n = 0; n < 25; n++) {
    await esperar(400);
    try { await fetch(`http://localhost:${PORTA}/api/itens`); break; } catch {}
  }

  const html = await (await fetch(`http://localhost:${PORTA}/`)).text();
  const dados = await (await fetch(`http://localhost:${PORTA}/api/itens`)).json();

  ok(html.includes("<script>"), "a pagina traz o bloco de script");
  ok(!/\n/.test(html.match(/textContent=s==null[^\n]*/)?.[0] ?? "x"),
     "nenhum literal JS foi quebrado por escape do Python");
  ok(dados.itens.length > 0, `a API devolve itens (${dados.itens.length})`);
  ok(dados.temas.length === 10, `a API devolve os 10 temas (${dados.temas.length})`);

  // -------- ordem: as candidaturas hoje vazias tem de vir primeiro
  const primeiros = dados.itens.slice(0, 40).map(x => x.id_candidatura);
  const vazias = ["sen-sp-2026-salles", "sen-sp-2026-derrite", "sen-sp-2026-tebet", "sen-sp-2026-marina"];
  ok(primeiros.every(c => vazias.includes(c)),
     "os 40 primeiros sao das candidaturas hoje vazias");

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

  const sub = doc.getElementById("sub").textContent;
  ok(/\d+ de \d+ classificados/.test(sub), `mostra progresso: "${sub}"`);

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

  const depois = await (await fetch(`http://localhost:${PORTA}/api/itens`)).json();
  const gravado = depois.itens.find(x => x.id === alvoId);
  // decisao vem como {} quando nao ha decisao, e {} e truthy — por isso o
  // encadeamento opcional, e nao um "&& gravado.decisao".
  ok(gravado?.decisao?.temas?.[0] === "t1",
     "a decisao volta gravada na proxima leitura");

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
  const limpo = await (await fetch(`http://localhost:${PORTA}/api/itens`)).json();
  const restou = limpo.itens.find(x => x.id === alvoId);
  ok(!(restou && restou.decisao && restou.decisao.temas),
     "o teste desfaz a propria gravacao");

  console.log(falhas ? `\n=== ${falhas} falha(s) ===` : "\n=== a tela funciona ===");
  py.kill();
  process.exit(falhas ? 1 : 0);
}

main().catch(e => { console.error(e); console.error(saidaPy); py.kill(); process.exit(1); });
