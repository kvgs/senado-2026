# Como contribuir

Este projeto reúne o que cada candidatura ao Senado defende, com a fonte de cada
informação. O valor dele não está na quantidade: está em **nada ser publicado sem
alguém ter aberto a fonte e conferido**.

Por isso a coisa mais importante deste documento não é como rodar os scripts. É
entender **por que uma informação entra ou não entra** — e por que "confere" é o
botão mais caro do projeto.

---

## Comece por aqui

Antes de tocar em qualquer coisa, leia **[`conhecimento/REGRAS.md`](conhecimento/REGRAS.md)**.
São 23 regras, e quase todas nasceram de um erro que já aconteceu aqui. Elas
dizem o que cada tipo de fonte pode e não pode sustentar.

O caso que resume o projeto: em agosto de 2026 a revisão humana reprovou **15
posições** atribuídas a uma "Base de candidaturas". O documento é um **cadastro**
— lista nome, partido, número, bens. Ele simplesmente não contém proposta
nenhuma. Não foi erro de leitura, foi erro de **origem**: aquela fonte
estruturalmente não podia sustentar aquelas afirmações.

Das 122 posições levantadas para São Paulo, **41 sobreviveram à revisão**. Um
terço. Esse número é a razão de tudo o que está escrito abaixo.

---

## O que você pode fazer

O que está aberto para colaboração é **construir e revisar o acervo de estados
novos**. Hoje existem São Paulo e Pernambuco; faltam 25 unidades da federação.

A moderação do agente de perguntas (o `/admin`, que dispara e-mail para gabinete
em nome do projeto) **não** faz parte disso e segue com a curadoria.

---

## As duas telas, e a diferença entre elas

Elas parecem irmãs e fazem perguntas diferentes. Confundir as duas é o erro mais
provável de quem chega.

### `revisar.py` — "a fonte sustenta o que está escrito?"

```
python revisar.py            # os 27 estados, intercalados
python revisar.py --uf PE    # só um estado
```

Sem `--uf` a fila cobre o acervo inteiro e **alterna estado e candidatura a cada
item**. São duas razões:

- ler quinze linhas seguidas da mesma pessoa cria expectativa, e a décima quinta
  acaba julgada pelo que as catorze anteriores pareciam;
- revisar estado por estado significa dar a São Paulo uma atenção que o Acre
  nunca teria.

A ordem por risco continua valendo: a alternância acontece **dentro** de cada
faixa, nunca entre faixas. Parar na metade ainda deixa revisada a metade que
importa.

Aqui você **afirma sobre uma candidatura**. Abra o link, leia, e decida:

| botão | significa |
|---|---|
| **Confere** | você abriu a fonte e ela diz aquilo, daquela candidatura |
| **Corrigir** | há um problema; escreva qual |
| **Remover** | não deveria estar publicado |

**Só "Confere" marca `revisado_por_humano`.** É a única afirmação do projeto que
vale como verificada por gente. Se você não abriu a fonte, não aperte.

Nada é apagado aqui. Posição reprovada sai do site e **fica nos dados** com o
motivo — erro escondido é erro que volta.

### `classificar.py` — "de que assunto isto trata?"

```
python classificar.py --uf PE
```

Aqui você **não afirma nada sobre ninguém**. A ementa já é literal e já veio da
API oficial da Câmara ou do Senado; a pergunta é só em qual das 10 gavetas o item
aparece. É escolha de organização.

A tela mostra o que o modelo classificou e pede que você confirme ou corrija. Ela
não mostra os 878 itens: mostra os **editoriais** (onde a escolha foi de
enquadramento, não de leitura) e uma **amostra sorteada**, para medir se a
classificação automática presta.

Na primeira vez ela pede um apelido. Ele fica gravado junto de cada decisão e
**é visível no repositório público** — use o seu usuário do GitHub, não o nome
civil, se preferir.

---

## Cinco selos, em dois eixos

Não são cinco níveis numa régua. Três medem **verificação por terceiro**:

🟢 **Oficial** — documento do próprio órgão: TSE, Câmara, Senado, Diário Oficial
🟡 **Verificada** — imprensa com ficha técnica pública e correção sinalizada
🔴 **Secundária** — tudo o mais; é onde a atribuição mais se perde

Os outros dois estão **fora dessa régua**, e é importante:

🟣 **Declaração do candidato** — prova que a pessoa **disse**, nunca que o que
ela disse é verdade
🔵 **Registro legislativo** — proposição ou voto: comportamento registrado, e não
promessa

---

## Ausência tem quatro tipos, e eles nunca se misturam

Esta é a parte que mais se erra, e a que mais importa.

| estado | significa |
|---|---|
| **A** | proposta da própria candidatura |
| **B** | proposta do partido, não da candidatura |
| **C** | a candidatura **não aborda** o tema — e há fonte dizendo isso |
| **D** | **não localizamos** fonte |

O estado **D é uma afirmação sobre a nossa busca**, e não sobre a candidatura.
Por isso ele exige a data da busca e o escopo do que foi procurado. "Não achei" e
"não existe" são coisas diferentes, e o site nunca diz a segunda quando só sabe a
primeira.

---

## O que este projeto nunca faz

Estas não são preferências de estilo. São o desenho.

- **Nunca ranquear.** A ordem é sempre a do número de urna. Nunca por volume de
  conteúdo, nunca por pesquisa.
- **Nunca contador de completude.** Quem tem mais material tem mais verba de
  campanha e mais imprensa — medir isso mediria dinheiro e fama, não candidatura.
- **Nunca comparar de forma avaliativa**, nunca recomendar voto.
- **Nunca contato que não venha de fonte oficial.** Nada de raspar rede social,
  nada de resultado de busca. Contato errado manda o eleitor escrever para um
  estranho.
- **Silêncio não é posição.** Pergunta não respondida por um gabinete registra
  que a pergunta foi feita, e nada mais.
- **CPF e título eleitoral não entram**, mesmo sendo dado público do TSE.

E uma que vale para você tanto quanto para a máquina: **paráfrase escorrega**.
Numa revisão, "controle estatal dos preços" tinha virado "congelamento de
preços", que é outra política. Quando puder, guarde a citação literal.

---

## Antes de abrir um pull request

Rode a suíte. Ela é rápida e pega coisa que passa despercebida:

```
python validar.py --uf SP        # integridade do modelo e as regras mecânicas
python conferir_contraste.py     # WCAG AA medido, nos dois temas
python gerar_site.py --uf SP     # regera a página do estado
python gerar_inicio.py           # regera a página nacional
node checa_js.js                 # sintaxe do JS gerado
node teste-revisar.mjs
node teste-classificar.mjs
python teste-redes.py            # recuperação de contato: o que entra e o que não
```

O site é **gerado** a partir de `dados/`. Não edite `index.html` nem
`sp/index.html` à mão: a próxima geração apaga.

---

## Como acrescentar um estado

```
python cadastrar_uf.py --uf MG            # mostra o que faria
python cadastrar_uf.py --uf MG --gravar   # cadastro, direto da base do TSE
python resolver_mandatos.py --uf MG --gravar
python coletar_legislativo.py --uf MG
python aplicar_classificacao.py --uf MG   # depois de escrever o mapeamento
```

Cada acervo estadual mora em `dados/<uf>/`. Nacional é só `referencia.json`,
`estados.json` e `mapa-uf.json` — um tema não muda de nome por estado.

Duas coisas que o cadastrador vai pedir seu olho:

- **nomes** que a regra de capitalização não resolve sozinha (o TSE grava tudo em
  caixa alta, e grafou "SANT ANNA" sem apóstrofo);
- **ocupações no feminino** que a tabela não cobre.

E marque o estado como `em_construcao` em `dados/estados.json` — a página inicial
lê dali, e um estado que aparece como pronto sem estar pronto promete o que não
existe.

---

## Uma última coisa

Se você encontrar um erro no que já está publicado, isso é uma **contribuição
boa**, não um incômodo. O histórico deste repositório está cheio de correções, e
várias delas são de coisas que o autor de um commit tinha afirmado com confiança
duas horas antes.

Prefira dizer "não sei" a preencher a lacuna com o que parece provável.
