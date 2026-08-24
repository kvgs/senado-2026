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

## Ainda faltam aqui — 2 documentos localizados, pendentes de download

Mesma rotina de antes: abrir no navegador, salvar, colocar nesta pasta com o
nome indicado.

| # | Link para abrir no navegador | Salvar como | Efeito |
|---|---|---|---|
| 1 | https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/doc/280017002789 | `programa-missao-2026.pdf` | Guto Schiavetto (144) sai de 🟣 para 🟢 |
| 2 | https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/doc/280017107286 | `programa-pcb-2026.pdf` | Petter Maahs (211) sai de 🟣 para 🟢 |

**O 1 é o "Livro Amarelo" do MISSÃO** — a versão condensada de 51 páginas
registrada no TSE, em 3 partes e 14 temas. O original tem cerca de 500
páginas, e uma versão de 360 não pôde ser protocolada por limite do TSE. Hoje
as propostas de Schiavetto vêm da página web da campanha; com este PDF passam
a vir do documento registrado.

**O 2 é o programa do PCB** registrado no TSE, que substitui a página do
pcb.org.br como fonte de Petter Maahs.

## Ainda por localizar — 3 documentos que provavelmente existem

Não achei a URL destes, mas há razão concreta para acreditar que existem:

1. **Programa estadual do PSTU para São Paulo.** Existe um registrado para o
   **Rio de Janeiro** (`doc/190016929078`), o que mostra que o partido
   registra programa por unidade federativa. A candidata do PSTU ao governo de
   SP é Vera Lúcia. Cobriria Dra Eliana Ferreira (161) e Weller Gonçalves (160)
   com fonte estadual, muito melhor que o programa nacional.
2. **Programa estadual da UP para São Paulo.** O programa estadual da UP para
   o Espírito Santo tem 23 páginas contra 2 do nacional. A candidata da UP ao
   governo de SP é **Vivian Mendes**, com propostas especificamente paulistas
   já divulgadas: reestatização da Sabesp, retomada da CPTM, salário mínimo
   paulista. Cobriria Marcio Alves (800) e Maíra de Souza (808).
3. **Programa do PCO registrado no TSE.** O PCO tem candidatura própria à
   Presidência (Rui Costa Pimenta), então deve haver documento registrado.
   Hoje a fonte de Ednelson Cesaretti (290) é cobertura de imprensa.

Se aparecerem novos documentos, eles entram nesta lista com link e nome de
arquivo.
