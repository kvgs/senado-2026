# Candidaturas ao Senado — Eleições 2026

Site de consulta às candidaturas ao Senado Federal, com as propostas organizadas
por tema e a fonte de cada informação. A primeira página traz a escolha do
estado; cada estado tem a sua.

**https://kvgs.github.io/senado-2026/**

## Onde o acervo está

O TSE registra **317 candidaturas ao Senado nas 27 unidades da federação** — que
são **315 pessoas**, porque duas aparecem com registro duplicado. Todas as 27
têm página, e todas as 315 têm cadastro, foto e os canais que declararam ao TSE.

| | |
|---|---|
| Candidaturas cadastradas | **315**, direto da base do TSE |
| Com foto de registro | **315** |
| Posições publicadas | **692** |
| **Conferidas por uma pessoa** | **41** |
| Candidaturas com alguma posição | **114 de 315** |

**⚠️ A maior parte ainda não passou por revisão humana.** Das 692 posições
publicadas, 41 foram lidas por uma pessoa contra a fonte original; as outras 651
aparecem **marcadas como "não revisado", uma a uma, com o link da fonte ao
lado**. A marcação não é rodapé: está em cada informação.

**E 618 das 692 são programa de partido, não da candidatura** — o site escreve
"Proposta do partido, não da candidatura" em cada uma. Só **71** são posição
própria, atribuída a uma pessoa. A desproporção é real e está na tela.

Isto não é um produto pronto. É um acervo em construção que mostra o próprio
estado, inclusive quando ele é ruim.

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
sp/  pe/  ac/  ...       uma pasta por estado, com a página gerada
_template_inicio.html   template da página nacional
_template_site.html     template da página de estado
acervo.py               diz onde cada arquivo mora
conhecimento/REGRAS.md  as 23 regras da curadoria, e o erro que gerou cada uma
modelo-de-dados.md      o desenho do modelo e o caso real que forçou cada decisão

dados/referencia.json   temas, partidos, selos, contato — vale para os 27 estados
dados/estados.json      as 27 unidades, com a contagem do TSE
dados/mapa-uf.json      malha do IBGE, simplificada
dados/<uf>/             o acervo de cada estado
fontes/                 documentos primários e extrações
```

Os scripts ficam na raiz, e se separam em cinco etapas — que são as etapas pelas
quais uma informação passa antes de chegar à tela:

| etapa | scripts |
|---|---|
| **cadastrar** | `cadastrar_uf`, `cadastrar_redes`, `resolver_mandatos`, `baixar_fotos` |
| **coletar** | `coletar_sites`, `coletar_legislativo`, `coletar_discursos`, `coletar_imprensa` |
| **extrair** | `extrair_posicoes`, `extrair_programa_partido`, `classificar_modelo`, `aplicar_classificacao` |
| **revisar** | `revisar` e `classificar` — as duas telas, e a única etapa que é humana |
| **publicar** | `promover_sites`, `promover_legislativo`, `gerar_site`, `gerar_inicio`, `validar` |

A separação entre **extrair** e **publicar** é o coração do desenho: extrair
guarda no acervo, publicar leva à tela, e entre as duas existe uma trava que
depende de gente. `promover_legislativo.py` recusa publicar enquanto a amostra
de classificação não tiver sido revisada e batido 80% de concordância.

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
`dados/referencia.json`. O site e o acervo não dependem de nada além da
biblioteca padrão do Python 3, exceto `pypdf` para ler PDF de programa
partidário. As peças gráficas do Instagram (`gerar_avatar.py`, `gerar_artes.py`)
usam `Pillow` e `fontTools` — mas nada do site depende delas.

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

- Contraste medido, não estimado: todas as combinações de texto e fundo são
  calculadas nos dois temas a cada geração, e `conferir_contraste.py` falha se
  alguma cair. O pior par hoje é 4,51:1, acima do mínimo de 4,5:1 — e o mapa da
  página inicial entrou nessa checagem depois de um erro em que ele ficou
  invisível no tema escuro, com 1,09:1.
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

- **Revisão humana: 41 de 692.** É o limite que mais pesa. O que não passou
  aparece marcado, com o link da fonte, mas marcado não é conferido.
- **618 das 692 posições são do partido, não da candidatura.** O site rotula
  cada uma, mas o desequilíbrio é grande: a maioria das candidaturas não tem
  material próprio publicado em lugar nenhum, e programa de partido é igual para
  todas as candidaturas daquele partido no país inteiro.
- **1.182 registros legislativos coletados e não publicados.** Câmara e Senado
  respondem bem, e o material está no acervo — mas a classificação temática
  ainda não foi medida contra revisão humana, e `promover_legislativo.py`
  bloqueia a publicação até que seja.
- **Sete sites declarados ao TSE não abrem.** São páginas montadas por
  JavaScript cujo conteúdo vem de uma API em tempo de execução; o coletor lê
  HTML e bundle, e nesses casos nenhum dos dois basta. A célula vazia diz isso.
- **Nove endereços declarados ao TSE não existem.** Conferido no DNS, um a um.
  É fato sobre a declaração, não sobre a pessoa: pode ser site tirado do ar ou
  endereço digitado errado.
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

Escreva para **contato.candidaturasenado@gmail.com**, fale pelo Instagram
[@candidaturasenado](https://www.instagram.com/candidaturasenado/), ou abra uma
issue — inclusive se o erro estiver no que já foi publicado. Correção é
contribuição, e o histórico deste repositório está cheio delas. Se você é candidato, assessoria de campanha ou partido e
identificou informação incorreta ou desatualizada sobre a sua candidatura,
abra uma issue com a fonte correta — correção de dado factual não depende de
concordância editorial.

## Fontes

Registro de candidaturas, fotos e canais declarados: TSE. Programas
partidários: documentos registrados no TSE e programas nacionais publicados
pelos próprios partidos — cada um com a data e o âmbito anotados, porque
documento de 2014 ou de uma candidatura estadual não vale para 2026 nem para o
país. Sites de candidatura: o endereço que a própria candidatura declarou ao
TSE, lido com `robots.txt` respeitado e User-Agent identificado. Registro
legislativo: dados abertos da Câmara, do Senado e da ALESP. Pesquisa: instituto
identificado com número de registro no TSE. O link de cada fonte está na própria
informação, no site.

**Data de referência dos dados: 28 de agosto de 2026.**
Eleição: 4 de outubro de 2026.
