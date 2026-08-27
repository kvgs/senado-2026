/* Prova que a tela de revisao DESENHA, com os itens reais.
 *
 * O defeito que motivou este teste nao dava erro em lugar nenhum: o servidor
 * subia, a pagina carregava, e vinha em branco. Conferir sintaxe nao bastou —
 * era preciso executar o desenho e olhar o resultado.
 */
import { execFileSync } from "node:child_process";
import vm from "node:vm";

const RAIZ = "c:/Users/BOC277 - Usuario/Documents/politica";

/* Pega a PAGINA e os itens do proprio revisar.py, como o navegador receberia. */
const saida = execFileSync("python", ["-c", `
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("rev", r"${RAIZ}/revisar.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
sys.stdout.write(json.dumps({"pagina": m.PAGINA, "itens": m.montar_itens()}, ensure_ascii=False))
`], { encoding: "utf8", maxBuffer: 40 * 1024 * 1024,
      /* SENADO_QUEM: o revisar.py passou a registrar QUEM decidiu e recusa subir
         sem apelido. Aqui nao ha ninguem no teclado, entao o teste se identifica,
         e "teste-automatizado" no dado deixa obvio que nao foi gente. */
      env: { ...process.env, PYTHONIOENCODING: "utf-8", SENADO_QUEM: "teste-automatizado" } });

const { pagina, itens } = JSON.parse(saida);
const js = pagina.match(/<script>([\s\S]*?)<\/script>/)[1];

/* DOM de mentira com escape de verdade: o esc() da pagina usa textContent. */
const els = new Map();
const novo = (id) => {
  const el = {
    id, innerHTML: "", value: "", disabled: false, style: {}, dataset: {},
    addEventListener(){}, focus(){}, querySelector(){ return null; },
    querySelectorAll(){ return []; }, closest(){ return null; },
  };
  let txt = "";
  Object.defineProperty(el, "textContent", {
    get: () => txt,
    set: (v) => { txt = v == null ? "" : String(v);
                  el.innerHTML = txt.replace(/&/g, "&amp;").replace(/</g, "&lt;"); },
  });
  return el;
};
const doc = {
  getElementById(i){ if (!els.has(i)) els.set(i, novo(i)); return els.get(i); },
  createElement: novo, addEventListener(){}, querySelector: () => null,
};

let pedido = null;
const ctx = {
  document: doc, console, alert: (m) => { pedido = m; }, setTimeout,
  fetch: async (url, opcoes) => {
    if (url === "/api/itens") return { json: async () => ({ itens }) };
    pedido = JSON.parse(opcoes.body);
    return { json: async () => ({ ok: true }) };
  },
};
ctx.window = ctx; ctx.globalThis = ctx;
vm.createContext(ctx);
new vm.Script(js, { filename: "revisar.js" }).runInContext(ctx);

await new Promise((r) => setTimeout(r, 60));   // deixa o fetch inicial resolver

const alvo = doc.getElementById("alvo").innerHTML;
const progresso = doc.getElementById("progresso").textContent;

let falhas = 0;
const checa = (ok, rotulo) => {
  if (!ok) falhas++;
  console.log(`${ok ? "OK   " : "FALHA"} ${rotulo}`);
};

/* A tela tem DOIS estados legitimos: com item pendente e com a revisao
   concluida. O teste antigo presumia o primeiro e acusou sete falhas no dia em
   que a revisao acabou — teste que so vale num estado do mundo mede o estado,
   nao o programa, e acusa falha no momento de sucesso. */
const pendentes = itens.filter((x) => !(x.revisado || (x.revisao && x.revisao.resultado)));

console.log(`=== ${pendentes.length} pendente(s) de ${itens.length} ===`);

if (!pendentes.length) {
  console.log("=== revisao concluida: a tela avisa? ===");
  checa(alvo.length > 40, `mensagem de conclusao renderizada (${alvo.length} chars)`);
  checa(/Tudo decidido|Nenhuma pergunta pendente|validar/.test(alvo),
        "diz o que fazer em seguida");
  checa(!alvo.includes(String.fromCharCode(100) + 'ata-d="confere"'),
        "nao oferece botao de decisao sem item para decidir");
  checa(progresso.includes("restam 0"), `progresso confere: "${progresso}"`);
} else {
  console.log("=== a tela desenhou? ===");
  checa(alvo.length > 400, `cartao renderizado (${alvo.length} chars)`);
  checa(progresso.includes("de"), `barra de progresso: "${progresso}"`);
  checa(alvo.includes('data-d="confere"'), "botao Confere presente");
  checa(alvo.includes('id="cit"'), "campo de citacao presente");
  checa(alvo.includes("o_que_conferir") === false, "sem placeholder cru vazando");

  if (!pendentes[0].citacao.trim()) {
    checa(alvo.includes("Cole a frase da fonte"), "pede a frase (item sem citacao)");
    console.log("");
    console.log("=== a trava da citacao funciona? ===");
    ctx.decidir("confere");
    await new Promise((r) => setTimeout(r, 20));
    checa(typeof pedido === "string" && pedido.includes("Cole a frase"),
          "confirmar sem a frase e recusado");
    doc.getElementById("cit").value = "Trecho colado da fonte para o teste.";
    pedido = null;
    ctx.decidir("confere");
    await new Promise((r) => setTimeout(r, 40));
    checa(pedido && pedido.citacao && pedido.citacao.startsWith("Trecho colado"),
          "com a frase, envia citacao para o servidor");
    checa(pedido && pedido.decisao === "confere", "decisao enviada corretamente");
  } else {
    console.log("");
    console.log("=== item ja tem citacao: campo e opcional ===");
    pedido = null;
    ctx.decidir("confere");
    await new Promise((r) => setTimeout(r, 40));
    checa(pedido && pedido.decisao === "confere", "confirma sem exigir frase nova");
  }
}

console.log(`\n=== ${falhas ? falhas + " FALHA(S)" : "a tela funciona"} ===`);
process.exit(falhas ? 1 : 0);
