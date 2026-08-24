# fontes/ — documentos primários baixados à mão

O TSE bloqueia acesso automatizado desta rede (HTTP 403), mas os arquivos
abrem normalmente no navegador. Esta pasta guarda os PDFs originais e a
extração por tema de cada um.

## Convenção de nomes

- **`.pdf`** — documento original, como saiu do TSE. **Fonte primária.**
- **`--extracao.md`** — minha leitura do documento, organizada por tema.
  **Não é a fonte**, é trabalho derivado. Se houver divergência, o PDF vence.

## O que está aqui

| Arquivo | O que é | Usar para |
|---|---|---|
| `programa-pstu-2026.pdf` | Programa PSTU Eleições 2026, nacional, 32 pág. | Dra Eliana Ferreira (161) e Weller Gonçalves (160) |
| `programa-pstu-2026--extracao.md` | Extração por tema + tabela de contrastes | leitura de trabalho |
| `programa-up-2026-nacional.pdf` | Programa UP / Samara Martins 80, nacional, 2 pág. | Marcio Alves (800) e Maíra de Souza (808) |
| `programa-up-2026--extracao.md` | Extração das 16 propostas | leitura de trabalho |
| `programa-up-2026-ESPIRITO-SANTO--NAO-USAR-PARA-SP.pdf` | Programa UP para o **Espírito Santo**, 23 pág. | ⚠️ **nada em SP** |

Os três estão registrados em `dados/documentos.json` com caminho, tamanho e
hash SHA-256 (16 primeiros caracteres), para dar para conferir depois se o
arquivo é o mesmo que foi lido.

## ⚠️ O arquivo do Espírito Santo

Veio do link `.../arquivo/doc/80017092488`, que eu havia registrado como
"outra versão do programa da UP". **Não é.** É o programa **estadual do
Espírito Santo** — salário-mínimo capixaba de R$ 3.242, Banestes, Cesan,
Escelsa, sistema Transcol, pó preto da Grande Vitória, Rio Doce, Araceli
Cabrera Crespo. Nada disso se aplica a São Paulo.

Está guardado só como registro da correção. O nome do arquivo carrega o
aviso de propósito.

**Pista que ele deixou:** o programa estadual do ES tem 23 páginas contra 2
do nacional, com propostas detalhadas por tema. Se a UP registrou um programa
estadual para **São Paulo**, ele provavelmente tem o mesmo nível de detalhe —
e seria a fonte certa para Marcio Alves e Maíra de Souza, muito melhor que o
nacional. Vale procurar no TSE.

## Ainda faltam aqui

Nenhum. Os três PDFs que estavam pendentes foram baixados em 24/ago/2026.

Se aparecerem novos documentos para baixar, eles serão listados aqui com o
link e o nome de arquivo a usar.
