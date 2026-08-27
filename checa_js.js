/* Extrai os blocos <script> do index.html gerado e passa cada um pelo parser.
 * Erro de sintaxe num site estatico nao aparece em teste nenhum: a pagina abre,
 * o JS morre inteiro, e as abas simplesmente nao respondem.
 */
const fs = require("fs");
const vm = require("vm");

// Confere a raiz (escolha do estado) e TODA pagina de estado. A lista era
// escrita a mao ("index.html", "sp/index.html") e ficou para tras assim que o
// site passou de dois estados: 25 paginas geradas nunca tiveram o JS conferido.
// Descobrir sozinho e a unica forma de a checagem nao envelhecer de novo.
const RAIZ = "c:/Users/BOC277 - Usuario/Documents/politica/";
const paginasDeEstado = () =>
  fs.readdirSync(RAIZ, { withFileTypes: true })
    .filter((d) => d.isDirectory() && /^[a-z]{2}$/.test(d.name))
    .filter((d) => fs.existsSync(`${RAIZ}${d.name}/index.html`))
    .map((d) => `${d.name}/index.html`)
    .sort();
const alvos = process.argv.slice(2).length ? process.argv.slice(2)
                                           : ["index.html", ...paginasDeEstado()];
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
