/* Prepara uma copia do worker com a chamada a API dublada.
 *
 * O worker importa o SDK da Anthropic e um JSON. Nenhum dos dois carrega no
 * Node puro do jeito que o wrangler empacota, e chamar a API de verdade num
 * teste custa dinheiro e depende de rede. Entao a copia troca os dois imports
 * e o teste roda offline, de graca, contra a MESMA logica de travas.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const TMP = path.join(AQUI, ".teste-tmp");

export const ENVIADO = [];

export async function carregarWorker() {
  fs.mkdirSync(TMP, { recursive: true });
  fs.copyFileSync(path.join(AQUI, "acervo-hashes.json"), path.join(TMP, "acervo-hashes.json"));

  fs.writeFileSync(path.join(TMP, "stub-anthropic.mjs"), `
export const ENVIADO = [];
export default class Anthropic {
  constructor(o){ this.o = o; }
  messages = { create: async (p) => {
    ENVIADO.push(p);
    return { model: p.model, stop_reason: "end_turn",
             content: [{ type: "text", text: "Resumo simulado para o teste [1]." }] };
  }};
}
`, "utf8");

  const src = fs.readFileSync(path.join(AQUI, "worker.js"), "utf8")
    .replace('import Anthropic from "@anthropic-ai/sdk";', 'import Anthropic from "./stub-anthropic.mjs";')
    .replace('import ACERVO from "./acervo-hashes.json";',
             'import ACERVO from "./acervo-hashes.json" with { type: "json" };');
  fs.writeFileSync(path.join(TMP, "worker.mjs"), src, "utf8");

  /* No Windows, import() so aceita URL file:// — caminho absoluto vira erro de esquema. */
  const worker = (await import(pathToFileURL(path.join(TMP, "worker.mjs")).href)).default;
  const stub = await import(pathToFileURL(path.join(TMP, "stub-anthropic.mjs")).href);
  return { worker, ENVIADO: stub.ENVIADO };
}
