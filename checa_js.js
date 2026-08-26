/* Extrai os blocos <script> do index.html gerado e passa cada um pelo parser.
 * Erro de sintaxe num site estatico nao aparece em teste nenhum: a pagina abre,
 * o JS morre inteiro, e as abas simplesmente nao respondem.
 */
const fs = require("fs");
const vm = require("vm");

// Confere as DUAS paginas: a raiz (escolha do estado) e a do estado. Apontar
// so para a raiz passaria por vacuidade — ela tem 700 bytes de JS.
const RAIZ = "c:/Users/BOC277 - Usuario/Documents/politica/";
const alvos = process.argv.slice(2).length ? process.argv.slice(2)
                                           : ["index.html", "sp/index.html"];
let falhas = 0;
for (const alvo of alvos) {
  const html = fs.readFileSync(RAIZ + alvo, "utf8");
  const blocos = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)]
    .map((m) => m[1]);
  console.log(`${alvo}: ${blocos.length} bloco(s) de script`);
  if (!blocos.length) { falhas++; console.log("  FALHA: nenhum script — pagina sem comportamento?"); }
  blocos.forEach((src, n) => {
    try {
      new vm.Script(src, { filename: `${alvo}#${n}` });
      console.log(`  bloco ${n}: OK (${src.length} chars)`);
    } catch (e) {
      falhas++;
      console.log(`  bloco ${n}: ERRO DE SINTAXE — ${e.message}`);
    }
  });
}
process.exit(falhas ? 1 : 0);
