# Backend do agente

Este diretório existe por um motivo único: **a chave da API não pode ficar no
navegador**. O site é estático (GitHub Pages), e tudo que ele carrega o visitante
consegue ler. Uma chave no JavaScript é uma chave publicada.

Enquanto o arquivo `agente-endpoint.txt` não existir na raiz do projeto, este
backend fica desligado e o site funciona exatamente como antes — a aba Perguntar
continua respondendo só com a recuperação determinística.

## O que o agente faz, e o que ele não faz

A ordem importa, porque é ela que segura a coisa:

1. O visitante pergunta. O site faz a recuperação **determinística**, como já fazia,
   e mostra as informações com fonte, selo e data.
2. Se a recuperação vier **vazia**, acabou: a resposta é "não encontrei nada no
   acervo", escrita pelo site. **O modelo não é chamado.** Ele nunca preenche vazio.
3. Se houver proposta recuperada, aparece um botão opcional. Só se a pessoa clicar
   é que o modelo entra — e ele recebe **apenas as linhas que já estão na tela**.
   Não recebe o acervo, não tem busca, não tem internet.
4. O texto que ele devolve aparece **abaixo** das fontes, com a ressalva de que
   nada foi revisado por humano. Essa ressalva é escrita pelo site, não pelo
   modelo: avisar sobre a própria falibilidade não pode depender de quem erra.

### A trava de procedência

Cada linha que chega ao backend tem o hash do seu texto conferido contra
`acervo-hashes.json`, gerado por `gerar_site.py` a partir de `dados/posicoes.json`.

Sem isso, qualquer pessoa poderia mandar texto inventado e receber de volta uma
versão fluente dele — com a conta indo para a sua chave, e com aparência de ter
saído do acervo. Confiar no que o navegador manda é confiar em código que está na
mão do visitante.

**Consequência prática:** sempre que você editar `dados/posicoes.json` ou
`dados/candidaturas.json`, rode `python gerar_site.py` e faça deploy do worker de
novo. O gerador reescreve `acervo-hashes.json` e `catalogo.json`, e o worker leva
os dois embutidos: se ficarem para trás, o agente recusa as linhas novas e a fila
recusa as candidaturas novas.

O CORS restrito à origem do site reduz uso acidental por outra página, mas não é
defesa: CORS é regra de navegador, e `curl` não é navegador. As defesas reais são
o hash acima e o teto de gasto no console da Anthropic.

## Deploy, passo a passo

Tudo isto roda dentro de `agente/`.

**1. Conta na Cloudflare** — grátis. https://dash.cloudflare.com/sign-up

**2. Chave da API da Anthropic** — https://console.anthropic.com → API Keys.
Guarde num lugar seguro; ela só aparece uma vez.

**3. Teto de gasto** — no mesmo console, em *Billing → Limits*, defina um limite
mensal. Este é o único mecanismo que realmente limita o prejuízo se algo der
errado. Comece baixo, US$ 5 resolve para testar.

**4. Instalar as dependências**

```
cd agente
npm install
```

**5. Entrar na Cloudflare**

```
npx wrangler login
```

**6. Gravar a chave como segredo** — ela vai para a Cloudflare, não para o
repositório:

```
npx wrangler secret put ANTHROPIC_API_KEY
```

Cole a chave quando pedir.

**7. Publicar**

```
npx wrangler deploy
```

No fim ele imprime a URL, algo como
`https://agente-senado-sp-2026.SEU-SUBDOMINIO.workers.dev`.

**8. Ligar no site** — na raiz do projeto, crie o arquivo `agente-endpoint.txt`
com essa URL dentro, e regenere:

```
cd ..
python gerar_site.py
```

**9. Publicar o site**

```
git add -A && git commit -m "liga a camada de LLM na aba Perguntar" && git push
```

## A fila de perguntas

Quando o acervo não responde, o visitante pode deixar a pergunta numa fila. O
site **não envia nada sozinho**.

O ciclo é: o visitante escolhe a candidatura e escreve a pergunta → ela entra no
banco D1 → você abre a página de moderação, vê quantas pessoas perguntaram a
mesma coisa para a mesma candidatura → seleciona, monta uma mensagem formal que
representa todas → envia do **seu próprio e-mail** → marca como enviadas.

A agregação é o ponto. Uma pergunta de um eleitor é fácil de ignorar; quinze
eleitores perguntando a mesma coisa é outra conversa. É isso que torna o pedido
respondível.

**Privacidade:** a fila guarda a pergunta, a candidatura e a data. Não guarda IP,
cookie, login nem qualquer identificador de visitante. Pergunta política diz
muito sobre quem pergunta, e o projeto não tem motivo para saber quem foi.

**Limite real hoje:** só 4 das 15 candidaturas têm e-mail oficial registrado —
as que têm mandato, com endereço institucional de gabinete. As outras dependem
do dataset *Redes sociais de candidatos* do TSE, preenchido pelos próprios
candidatos no registro, que continua pendente de download manual. A fila aceita
perguntas para todas as 15; o envio, por enquanto, só funciona para as 4. A
página de moderação diz isso explicitamente em cada grupo.

### Página de moderação

Fica em `SUA-URL-DO-WORKER/admin`, servida pelo próprio worker — não pelo
GitHub Pages — para que o token nunca precise existir no repositório público.
Ela é `noindex` e não mostra nada sem o token.

Para definir o token:

```
cd agente
npx wrangler secret put TOKEN_ADMIN
```

Use uma senha longa e aleatória, gerada por um gerenciador de senhas. Ela é a
única coisa entre a fila e a internet.

### Banco de dados

D1, `perguntas-senado-sp`. O esquema está em `migracoes/0001_fila.sql`. Para
aplicar num banco novo:

```
npx wrangler d1 execute perguntas-senado-sp --remote --file=migracoes/0001_fila.sql
```

Para olhar a fila pela linha de comando, sem a página:

```
npx wrangler d1 execute perguntas-senado-sp --remote   --command "SELECT criada_em, id_candidatura, pergunta FROM perguntas WHERE estado='pendente'"
```

### Enviar do seu próprio e-mail

A página de moderação abre o cliente de e-mail (`mailto:`). Se você preferir
enviar por comando, sem clicar em nada, use `enviar.py` — ele roda **na sua
máquina** e manda pelo seu Gmail:

```
cd agente
python enviar.py --listar
python enviar.py --simular sen-sp-2026-marina
python enviar.py --enviar  sen-sp-2026-marina
```

O `--simular` monta a mensagem e mostra na tela sem enviar nada. O `--enviar`
mostra a mensagem, pede que você digite `ENVIAR` para confirmar, manda, e marca
as perguntas como enviadas na fila. Não existe modo "manda tudo sem olhar", de
propósito.

Credenciais por variável de ambiente — o que faltar, ele pergunta sem ecoar:

| Variável | O que é |
|---|---|
| `AGENTE_TOKEN` | o mesmo `TOKEN_ADMIN` da Cloudflare |
| `GMAIL_USUARIO` | seu endereço |
| `GMAIL_SENHA` | **senha de app** do Gmail, não a senha da conta |

A senha de app sai de `myaccount.google.com/apppasswords` e exige verificação em
duas etapas ligada. A senha normal da conta não funciona em SMTP e o Gmail
devolve erro de autenticação.

Para conferir a montagem da mensagem sem rede e sem credenciais:

```
python enviar.py --autoteste
```

**Por que não pelo worker:** a Cloudflare não abre SMTP com facilidade, e todo
serviço de envio por HTTP exige domínio próprio verificado — o e-mail sairia de
um domínio novo, com cara de robô, e não do seu endereço. Rodando na sua máquina
ele sai da sua conta de verdade: fica na sua caixa de Enviados, e a resposta do
gabinete cai na sua caixa de entrada.

**Vale pensar antes:** o endereço que você usar fica conhecido pelas assessorias
de campanha. Uma conta dedicada ao projeto separa isso do seu e-mail pessoal.

### Instagram

Não dá para enviar automaticamente, e não é limitação nossa: a API do Instagram
só permite mandar mensagem para quem escreveu para a sua conta nas últimas 24h.
Não existe caminho oficial para abrir uma DM fria com um candidato, nem pela sua
própria conta. O que existe é automação de navegador fingindo ser você, que
viola os termos e derruba a conta — não está implementado e não deve estar.

O que a página de moderação faz é o máximo honesto: quando há @ registrado, ela
mostra um link `ig.me` que **abre a conversa** com aquela conta, e você cola o
texto. Hoje nenhuma das 15 candidaturas tem Instagram no acervo — depende do
mesmo dataset do TSE que está pendente.

## Rotas do worker

| Rota | Método | O que faz | Protegida por |
|---|---|---|---|
| `/` | POST | Redige o resumo a partir das linhas recuperadas | origem + hash do acervo |
| `/perguntar` | POST | Põe uma pergunta na fila | origem + limitador |
| `/admin` | GET | Página de moderação | o token, pedido na própria página |
| `/fila` | GET | Lista a fila em JSON | `x-token` |
| `/decidir` | POST | Marca perguntas como enviadas ou descartadas | `x-token` |

## Custo

Cada resumo usa mais ou menos 2 mil tokens de entrada e algumas centenas de
saída, no `claude-opus-5`. Dá algo entre **2 e 4 centavos de dólar por resumo**.
Cem resumos por mês ficam abaixo de US$ 4.

Se quiser barato de verdade, troque `model: "claude-opus-5"` por
`model: "claude-haiku-4-5"` no `worker.js` — cinco vezes mais barato. Para uma
tarefa de reescrever fielmente o que já foi entregue, é uma troca defensável;
o risco é que modelos menores seguem instruções longas com menos disciplina, e
aqui as instruções longas são justamente as travas de neutralidade e atribuição.

## Limitador de uso

O `wrangler.toml` traz um limitador de 6 pedidos por minuto por IP. Ele é
opcional: se o deploy reclamar da seção `[[unsafe.bindings]]`, apague as cinco
linhas e publique de novo — o worker detecta a ausência e segue funcionando.

## Conferir as travas sem gastar nada

```
cd agente
node teste-travas.mjs
```

Roda o worker offline, com a chamada à API dublada, e verifica as portas que
precisam estar fechadas: recuperação vazia não chega ao modelo, texto que não
confere com o acervo é recusado, origem estranha é barrada, e a pergunta do
visitante entra como dado e nunca como instrução de sistema. Não usa rede nem
chave, então pode rodar sempre. **Rode depois de mexer em `dados/posicoes.json`
e regenerar o site** — é o jeito de descobrir que os hashes ficaram para trás
antes que o agente comece a recusar linhas legítimas em produção.

## Testar sem publicar o site

```
cd agente
npx wrangler dev
```

e, na raiz, sirva o site em `http://localhost:8000`:

```
python -m http.server 8000
```

Essa origem já está autorizada no `worker.js`. Abrir o `index.html` direto pelo
Explorer (`file://`) **não** funciona: o navegador manda origem nula e o backend
recusa.

## Se quiser desligar

Apague `agente-endpoint.txt`, rode `python gerar_site.py`, e publique. O botão
some e o site volta ao comportamento anterior. Nada mais depende disto.
