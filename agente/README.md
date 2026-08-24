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

**Consequência prática:** sempre que você editar `dados/posicoes.json`, rode
`python gerar_site.py` e faça deploy do worker de novo. Se os hashes ficarem para
trás, o agente vai recusar as linhas novas.

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
