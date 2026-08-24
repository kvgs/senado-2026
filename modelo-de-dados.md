# Fase 4 — Modelo de dados

**Rascunho para revisão.** Data: 24/ago/2026.
Nada foi implementado ainda — este documento é a proposta de estrutura.

Base empírica: Presidente (4 candidatos × 9 temas) e Senado SP (15 × 9),
já levantados. O modelo abaixo foi desenhado **a partir dos casos difíceis
que apareceram de verdade**, não de um desenho abstrato — cada requisito da
próxima seção nasceu de um caso concreto, e está nomeado.

---

## 1. Requisitos, e o caso real que forçou cada um

| # | Requisito | Caso que forçou |
|---|---|---|
| R1 | Uma proposta pode pertencer a **candidato OU a partido/chapa** | Guto Schiavetto não tem programa próprio — as propostas dele são do MISSÃO. Vale para **7 dos 15** senadores |
| R2 | Célula sem conteúdo tem **4 estados distintos**, não um vazio | Soninha "tem material e não trata de educação" (C) ≠ William Teixeira "não achamos fonte nenhuma" (D) |
| R3 | A escala de fonte tem **5 níveis**, não 3 | Site oficial de campanha não é 🟡 (ninguém conferiu) nem 🔴 (não é terceiro) → criado 🟣. E voto registrado não é promessa → 🔵 |
| R4 | A posição precisa registrar **o escopo dentro do tema** | Tebet e Marina têm posição em Segurança, mas só sobre violência doméstica. Sem escopo, a célula finge cobrir o tema inteiro |
| R5 | Separar **promessa** de **resultado já entregue** | Meio ambiente do Lula mistura meta do plano com queda de 41% no desmatamento já ocorrida |
| R6 | Documento oficial tem **versões** | Tarcísio: plano preliminar de 9 páginas substituído por versão final de 68 |
| R7 | **Situação do registro muda no tempo** | 14 dos 15 senadores em "aguardando julgamento", 1 deferido — e isso muda até outubro |
| R8 | Pesquisa exige **ficha técnica** e precisa registrar **quem não estava no questionário** | Schiavetto e William Teixeira ausentes da Paraná Pesquisas. Ausência ≠ 0% |
| R9 | Registro legislativo é **N:N** com candidatura e com tema | `PEC 8/2026` é coautoria de Derrite **e** Salles, e toca Segurança |
| R10 | **Tudo** carrega data de referência | Candidatura pode ser indeferida depois da extração |
| R11 | **CPF nunca sai da Bronze** | Princípio de privacidade da seção 4 do contexto |
| R12 | Fonte inacessível é **estado registrável**, não erro silencioso | TSE dá 403; sabemos a URL, não temos o arquivo |

---

## 2. Camadas

Usando a arquitetura que você já usa profissionalmente, e que a seção 8 do
contexto já previa para a Camada 1 dos deputados estaduais.

**Bronze — captura crua, imutável.**
Um registro por captura: o HTML, o PDF, a resposta da API, como vieram.
Guarda `url`, `capturado_em`, `http_status`, `hash_conteudo`,
`caminho_arquivo`. É aqui que fica o CPF, e é daqui que ele não sai (R11).
Registra também **captura que falhou** (R12): o 403 do TSE vira linha, com
a URL preservada, para quando o acesso for resolvido.

**Silver — entidades normalizadas.**
As tabelas da seção 3. Uma linha por fato, deduplicada, tipada, com
proveniência apontando para Bronze.

**Gold — o que o site e o agente consomem.**
Duas visões principais: `comparativo_por_tema` (a página de comparação) e
`perfil_candidatura` (a página de perfil). O agente de perguntas (Fase 7) lê
Gold e **só** Gold — é isso que garante o grounding "só no que foi
validado".

---

## 3. Tabelas — Silver

### `pessoa`
`id_pessoa` · `nome_urna` · `nome_completo` · `data_nascimento` ·
`escolaridade` · `ocupacao_declarada`

> `nome_urna` é o identificador de exibição — é o que o eleitor vê na urna.
> `nome_completo` fica guardado mas não é o rótulo. Essa distinção resolveu
> a divergência entre veículos: o InfoMoney grafava "Marcio Santos" usando
> fragmento do nome completo (Marcio Alves **dos Santos**), os outros usavam
> o nome de urna.

### `partido`
`id_partido` · `sigla` · `nome`

### `coligacao`
`id_coligacao` · `nome` · `ano` · `uf` · `cargo` · `composicao` (texto)

> Ex.: "Desperta São Paulo" (PDT/PSB/FE Brasil/PSOL-Rede), que lança **duas**
> candidaturas ao Senado. Por isso coligação é entidade, não campo.

### `candidatura`
`id_candidatura` · `id_pessoa` · `id_partido` · `id_coligacao` ·
`cargo` · `uf` · `ano` · `numero_urna` · `sequencial_tse` ·
`bens_declarados` · `suplentes`

> `sequencial_tse` é a chave natural do registro oficial. Guardei o dos 15
> senadores de propósito: quando o acesso ao TSE for resolvido, dá para
> puxar o registro oficial sem refazer pesquisa.

### `situacao_registro` — **historizada** (R7, R10)
`id_candidatura` · `situacao` · `observado_em` · `id_captura_bronze`

> Tabela separada, não campo. "Aguardando julgamento" em 24/ago pode virar
> "deferido" ou "indeferido" antes de 4/out, e o site precisa mostrar a
> situação **com a data em que foi observada**.

### `tema`
`id_tema` · `nome` · `ordem` · `aplicavel_a_cargos`

> `aplicavel_a_cargos` porque a mesma lista de 9 temas funciona como
> *proposta de execução* para cargo executivo e como *posicionamento* para
> cargo legislativo.

### `documento_fonte`
`id_documento` · `titulo` · `tipo` (plano_tse, programa_partidario,
site_oficial, entrevista, reportagem, api_dados_abertos) ·
`url` · `id_captura_bronze` · `data_publicacao` · `acessivel` (bool) ·
`motivo_inacessivel`

> `acessivel = false` + URL preservada é o caso dos PDFs de programa do PSTU
> e da UP no TSE (R12): sabemos exatamente onde estão, só não conseguimos
> baixar daqui.

### `versao_documento` (R6)
`id_documento` · `versao` · `data` · `paginas` · `substitui_versao`

### `posicao` — **a tabela central**
| Campo | Tipo | Observação |
|---|---|---|
| `id_posicao` | pk | |
| `id_tema` | fk | |
| **`atribuido_a_tipo`** | enum | **`candidatura` \| `partido`** — R1 |
| **`atribuido_a_id`** | fk | aponta para um ou outro |
| `id_candidatura_contexto` | fk | quando é do partido, qual candidatura ela cobre |
| **`estado_cobertura`** | enum | **A / B / C / D** — R2 |
| **`escopo`** | texto | R4. Ex.: "apenas violência doméstica" |
| **`natureza`** | enum | **`promessa` \| `resultado_entregue`** — R5 |
| `texto` | texto | o conteúdo |
| `citacao_literal` | texto | quando há trecho textual |
| `id_documento` | fk | de onde veio |
| **`nivel_fonte`** | enum | `oficial` \| `verificada` \| `secundaria` \| `declaracao_candidato` \| `registro_legislativo` — R3 |
| `data_referencia` | data | R10 |
| `revisado_por_humano` | bool | a curadoria incremental |

**Para `estado_cobertura = 'D'`, dois campos são obrigatórios:**
`busca_realizada_em` e `escopo_da_busca`.

> Isto é regra de integridade, não convenção. D é uma afirmação sobre a
> nossa busca, não sobre o candidato — sem data e escopo registrados, vira
> uma acusação de silêncio que não podemos sustentar. O banco deve recusar
> uma linha D sem esses dois campos.

### `registro_legislativo` (R9)
`id_registro` · `casa` (camara / senado / alesp / camara_municipal) ·
`tipo` (PL, PEC, PLP, PDL, voto) · `numero` · `ano` · `ementa` ·
`url_oficial` · `data`

### `registro_autoria` — N:N
`id_registro` · `id_candidatura` · `papel` (autor / coautor / relator)

### `registro_tema` — N:N
`id_registro` · `id_tema`

### `situacao_parlamentar` — o contexto sem o qual a contagem engana
`id_candidatura` · `situacao` · `desde` · `motivo_afastamento`

> Marina Silva em exercício só desde 01/abr/2026 (licenciada como ministra)
> e Derrite desde 02/dez/2025 (licenciado na Secretaria de Segurança).
> **Exibir contagem de proposições sem isto ao lado seria factualmente
> correto e materialmente enganoso.** Por isso é tabela, e a Gold deve
> recusar montar o card de produção legislativa sem ela.

### `pesquisa` e `pesquisa_resultado` (R8)
`pesquisa`: `id_pesquisa` · `instituto` · `contratante` ·
**`registro_tse`** · `campo_inicio` · `campo_fim` · `entrevistados` ·
`margem_erro` · `nivel_confianca` · `cenario`

`pesquisa_resultado`: `id_pesquisa` · `id_candidatura` · `percentual` ·
**`constava_no_questionario`** (bool)

> O booleano existe por causa de Schiavetto e William Teixeira, ausentes da
> Paraná Pesquisas porque o campo foi antes das candidaturas entrarem nas
> listas. Sem ele, a tabela do site mostraria os dois como 0% — que é
> mentira. Regra: **nenhuma pesquisa entra sem `registro_tse` preenchido.**

---

## 4. Regras que o modelo impõe à camada Gold

1. **Proibido contador de completude por candidatura.** Sem "9 de 9 temas",
   sem barra de progresso, sem ordenação por volume de conteúdo. É ranking
   disfarçado, e mede verba de campanha e cobertura de imprensa. Isto é
   restrição de modelagem, não sugestão de layout: a Gold **não expõe** o
   agregado que permitiria construí-lo.
2. **Toda célula exibida carrega fonte e data.** Sem exceção.
3. **`atribuido_a_tipo = 'partido'` sempre aparece rotulado como tal.**
   "Proposta do PCB", nunca "proposta de Petter Maahs".
4. **`natureza = 'resultado_entregue'` é visualmente separado de
   `promessa`.** Vem do caso do Lula em meio ambiente.
5. **CPF não existe em Silver nem em Gold.**
6. **A escala tem duas dimensões, não uma.** 🟢/🟡/🔴 medem *verificação por
   terceiro*; 🟣 e 🔵 estão fora desse eixo — 🟣 é fonte direta não
   verificada, 🔵 é comportamento registrado. Para cargo legislativo a
   evidência mais forte é 🔵, não 🟢. A UI não deve renderizar os cinco como
   uma régua linear.

---

## 5. Três exemplos preenchidos

**Caso R1 — proposta que é do partido:**
```
posicao: tema=Habitação · atribuido_a_tipo=partido · atribuido_a_id=MISSÃO
  id_candidatura_contexto=Guto Schiavetto/Senado-SP
  estado_cobertura=B · natureza=promessa · nivel_fonte=declaracao_candidato
  citacao_literal="Transformar as 12.348 favelas do país em bairros formais
    em 10 anos, com título de propriedade..."
  data_referencia=2026-08-24
```

**Caso R4 — posição que cobre só um recorte do tema:**
```
posicao: tema=Segurança Pública · atribuido_a_tipo=candidatura
  atribuido_a_id=Marina Silva/Senado-SP
  estado_cobertura=A · escopo="apenas enfrentamento à violência doméstica"
  nivel_fonte=declaracao_candidato · data_referencia=2026-08-24
```

**Caso R2/D — ausência que é sobre nós, não sobre ele:**
```
posicao: tema=(todos os 9) · atribuido_a_id=William Teixeira/Senado-SP
  estado_cobertura=D
  busca_realizada_em=2026-08-24
  escopo_da_busca="busca web por nome de urna, nome completo, partido e
    número; sem material de campanha nem programa do AGIR localizados"
```

---

## 6. Decisões que preciso de você

1. **Stack.** O volume é pequeno (Presidente + Governador + Senado cabem em
   poucos milhares de linhas; deputado estadual são ~1.400 registros de
   diretório, sem curadoria). Isso comporta desde SQLite/Parquet + arquivos
   versionados no git até algo em Fabric. Minha inclinação: **arquivos
   versionados** (JSON ou Parquet) como fonte de verdade, porque curadoria
   incremental revisada por humano combina com histórico de commits — dá
   para ver quem mudou o quê e quando, que é o próprio princípio de
   procedência do projeto. Fabric entraria depois, na Camada 1 dos deputados.

2. **`tema` fixo ou versionado?** Se a lista de 9 mudar, as posições já
   catalogadas precisam ser remapeadas. Fixar agora é mais simples; versionar
   é mais seguro.

3. **Granularidade de `posicao`.** Uma linha por *proposta* (vários registros
   por candidato/tema) ou uma linha por *célula* candidato×tema com texto
   corrido? A primeira é melhor para o agente da Fase 7 e para citar fonte
   por afirmação; a segunda é mais rápida de popular a partir do que já
   temos em markdown. Minha inclinação: **uma linha por proposta** — o
   trabalho extra agora evita reprocessar tudo quando o agente entrar.

---

## 7. O que este modelo ainda não resolve

- **Deputado estadual (Camada 1).** Diretório de ~1.400 nomes é outro
  fluxo — sem curadoria, alimentado por dataset do TSE. Encaixa em
  `pessoa` + `candidatura`, mas não gera `posicao`. E depende do acesso ao
  TSE, hoje bloqueado.
- **Histórico de votação nominal.** `registro_legislativo` prevê
  `tipo='voto'`, mas o desenho fino (como amarrar voto a proposição de
  terceiro, e como resumir posição a partir de votos) ainda não foi feito.
  Fica para quando extrairmos as votações.
- **Governador de SP** ainda tem fontes pendentes — o modelo comporta, mas
  os dados não estão levantados.
