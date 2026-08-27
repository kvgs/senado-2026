# Candidaturas ao Senado — Eleições 2026

Site de consulta às candidaturas ao Senado Federal, com as propostas organizadas
por tema e a fonte de cada informação. A primeira página traz a escolha do
estado; cada estado tem a sua.

**https://kvgs.github.io/senado-2026/**

## Onde está cada estado

São **317 candidaturas ao Senado em 27 unidades da federação**. O acervo é
construído estado a estado, e a página inicial diz de qual já começamos.

| estado | situação |
|---|---|
| **São Paulo** | 15 candidaturas · 41 posições publicadas, todas conferidas contra a fonte |
| **Pernambuco** | 12 candidaturas · cadastro do TSE e 878 registros legislativos aguardando revisão |
| os outros 25 | ainda não começamos |

**⚠️ Trabalho em curso.** Em São Paulo, das 122 posições levantadas, **41
passaram na revisão humana** e são as únicas publicadas — as outras 81 ficam nos
dados abertos, com o motivo da reprovação. Em Pernambuco nenhuma posição foi
revisada ainda. Não use como referência única para decidir voto.

---

## O que este projeto tenta fazer diferente

Comparar candidaturas é fácil de fazer mal. Três problemas aparecem sempre, e
o projeto foi desenhado em torno deles.

### 1. Toda informação mostra de onde veio

Não há afirmação sem fonte, link e data de referência. E não há uma escala
única de confiança, porque as fontes não são todas da mesma natureza:

| Selo | O que é |
|---|---|
| 🟢 **Oficial** | Extraído do documento registrado no TSE. |
| 🔵 **Registro legislativo** | Voto ou autoria, dos dados abertos da Câmara, do Senado ou da ALESP. Comportamento registrado, não promessa. |
| 🟣 **Declaração do candidato** | Site oficial, entrevista, programa partidário. Vem direto da fonte; ninguém conferiu. |
| 🟡 **Verificada** | Reportagem que conferiu o texto contra o documento oficial. |
| 🔴 **Secundária** | Terceiro resumindo, não conferido. |

🟢/🟡/🔴 medem **verificação por terceiro**. 🟣 e 🔵 estão fora desse eixo:
🟣 é fonte direta não verificada, 🔵 é comportamento já registrado. Não é uma
régua linear e o site não a apresenta como se fosse.

Nota sobre este cargo: candidatura ao Senado **não é obrigada** a registrar
plano de governo no TSE. O nível 🟢 aqui chega pela via do **programa do
partido**, quando ele existe e está registrado.

### 2. Ausência de proposta é informação — e tem quatro tipos diferentes

Célula vazia não é tudo a mesma coisa. Colapsar os quatro casos num só vazio
faz o site afirmar coisas que ele não pode sustentar:

- **Proposta própria** — posição documentada e atribuível à candidatura.
- **Proposta do partido** — o conteúdo existe, mas pertence ao programa
  partidário, não à pessoa. É como funciona a maior parte das candidaturas de
  partido pequeno; aparece sempre rotulado como do partido, nunca do
  candidato.
- **Não aborda o tema** — a candidatura tem material publicado e aquele
  material não trata disto. Afirmação sobre a candidatura.
- **Não localizamos fonte** — *nós* procuramos e não encontramos. Afirmação
  sobre a nossa busca, não sobre a candidatura, e vem sempre com a data e o
  escopo do que foi procurado.

### 3. Não existe pontuação, nota nem ranking

Nenhum contador de temas preenchidos, barra de progresso por candidatura ou
ordenação por volume de conteúdo. Um placar desses seria um ranking na
prática — e o que ele mediria não é qualidade de candidatura, e sim **verba de
campanha e cobertura de imprensa**. Candidatura com assessoria ocupa mais
espaço que candidatura de sindicalista de partido pequeno, por razões que nada
têm a ver com o que o eleitor está avaliando.

A ordem é a do **número de urna**, que não opina. Quando há mais de uma
proposta no mesmo tema, as de citação literal vêm primeiro — regra mecânica,
não escolha editorial de quais seriam "as principais".

Pesquisa de intenção de voto aparece **só na aba própria**, com ficha técnica
completa, e nunca ao lado de cada candidatura — repetir a porcentagem em todo
cartão transformaria a lista num ranking.

---

## Como está organizado

```
index.html              escolha do estado (mapa + lista), página nacional
sp/index.html           a página de São Paulo
pe/index.html           a página de Pernambuco
gerar_inicio.py         gera a página nacional
gerar_site.py --uf SP   gera a página de um estado
_template_inicio.html   template da página nacional
_template_site.html     template da página de estado
acervo.py               diz onde cada arquivo mora
validar.py --uf SP      valida a integridade de um acervo estadual
conhecimento/REGRAS.md  as 23 regras da curadoria, e o erro que gerou cada uma
modelo-de-dados.md      o desenho do modelo e o caso real que forçou cada decisão

dados/referencia.json   temas, partidos, selos — vale para os 27 estados
dados/estados.json      as 27 unidades, com a contagem do TSE
dados/mapa-uf.json      malha do IBGE, simplificada
dados/sp/  dados/pe/    o acervo de cada estado
fontes/                 documentos primários e extrações
```

Fontes, fotos e o mapa ficam na raiz e são **compartilhados** pelos estados — não
copiados 27 vezes.

O site é **gerado**, nunca escrito à mão. Isso é deliberado: se a página é
gerada do modelo, ela não pode divergir dele.

```bash
python validar.py --uf SP        # verifica integridade; exit 1 se houver erro
python gerar_site.py --uf SP     # regenera a página do estado
python gerar_inicio.py           # regenera a página nacional
python conferir_contraste.py     # WCAG AA medido, nos dois temas
```

Toda ferramenta aceita `--uf`; sem ele, usa o estado padrão de
`dados/referencia.json`. Sem dependências além da biblioteca padrão do Python 3,
exceto `pypdf` para ler PDF.

**Quer contribuir?** Leia [`CONTRIBUINDO.md`](CONTRIBUINDO.md) — ele explica por
que uma informação entra ou não entra, que é a parte que importa.

## Regras que o validador impõe em código

Algumas regras não podem ficar só na documentação, porque documentação não é
executada:

- Estado "não localizamos fonte" **exige** data e escopo da busca. Sem isso a
  linha é rejeitada — é uma afirmação sobre a nossa busca, e sem registrar
  quando e onde procuramos ela viraria uma acusação de silêncio contra uma
  pessoa real.
- Proposta atribuída a partido **exige** a candidatura de contexto.
- Pesquisa sem número de registro no TSE é erro.
- `constava_no_questionario: false` com percentual preenchido é erro — ausência
  do questionário **não é 0%**.
- Contagem de proposições sem a situação parlamentar ao lado é erro: quem
  esteve licenciado para ocupar cargo executivo tem produção menor por
  ausência formal, não por inatividade.
- Registro de autoria com mais de um autor **exige** a ordem na lista. No
  Senado uma PEC precisa de 27 assinaturas, então "autor" ali frequentemente
  significa apoiador — sem a ordem, os números não são comparáveis.

## Acessibilidade

Alvo WCAG 2.1 nível AA.

- Contraste medido, não estimado: as 64 combinações de texto e fundo foram
  calculadas nos temas claro e escuro. A menor razão é 4,8:1, acima do mínimo
  de 4,5:1 para texto normal.
- Abas seguem o padrão WAI-ARIA, com navegação por setas, Home e End.
- Áreas que trocam de conteúdo são `aria-live`, então leitor de tela anuncia a
  mudança.
- Link de pular navegação, foco visível de 3px, `prefers-reduced-motion`
  respeitado.
- Nenhuma informação depende só de cor: todo selo vem com o nome escrito.
- Tabela de pesquisa com `caption` e `scope`; a barra visual é
  `aria-hidden` porque o número já está no texto.

**Ainda não testado com leitor de tela real** (NVDA, VoiceOver). Contraste e
semântica foram conferidos; a experiência de uso, não.

## Limites conhecidos

- **Revisão humana: 0 de 119.** É o que separa este rascunho de algo
  publicável.
- **Sem fotos.** O dataset oficial de fotos de candidatos do TSE bloqueia
  acesso automatizado. Até obtê-las de lá, cada candidatura aparece com as
  iniciais do nome de urna — e não com imagem de outra origem, para não haver
  risco de trocar o retrato de alguém.
- **Situação do registro muda** por decisão da Justiça Eleitoral até a
  eleição. Cada candidatura mostra a situação com a data em que foi observada.
- **Votação nominal é escassa** na base pública do período, e por isso
  contagem de votos não é usada como medida de atividade parlamentar.
- Parte das linhas de "não aborda o tema" é **inferência** a partir da ausência
  de menção, não de leitura de documento completo. Onde é o caso, a ressalva
  está escrita na própria informação.
- **O TSE bloqueia parte do acesso automatizado.** A base de candidatos em
  massa é baixável e é dela que sai o cadastro de cada estado; já o
  DivulgaCandContas responde HTTP 403 a script, e os documentos anexados a cada
  candidatura precisam ser baixados pelo navegador. Cada arquivo em `fontes/`
  tem tamanho e hash SHA-256 registrados no acervo.

## Encontrou um erro?

Abra uma issue — inclusive se o erro estiver no que já foi publicado. Correção é
contribuição, e o histórico deste repositório está cheio delas. Se você é candidato, assessoria de campanha ou partido e
identificou informação incorreta ou desatualizada sobre a sua candidatura,
abra uma issue com a fonte correta — correção de dado factual não depende de
concordância editorial.

## Fontes

Registro de candidaturas: TSE. Programas partidários: documentos registrados
no TSE, arquivados em `fontes/` com hash. Registro legislativo: dados abertos
da Câmara dos Deputados, do Senado Federal e da ALESP. Pesquisa: instituto
identificado com número de registro no TSE. O link de cada fonte está na
própria informação, no site.

**Data de referência dos dados: 24 de agosto de 2026.**
Eleição: 4 de outubro de 2026.
