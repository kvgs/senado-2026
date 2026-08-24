# dados/ — camada Silver

Fonte de verdade do projeto. JSON versionado no git, porque curadoria
incremental revisada por humano combina com histórico de commits: dá para
ver quem mudou o quê, quando e por quê — que é o próprio princípio de
procedência do projeto aplicado ao processo de trabalho.

Decisões tomadas em 24/ago/2026 (ver seção 6 de
[../modelo-de-dados.md](../modelo-de-dados.md)):

- **Stack:** arquivos JSON versionados. Fabric/Databricks entram depois, na
  Camada 1 dos deputados estaduais (~1.400 registros de diretório).
- **Temas:** id fixo (`t1`..`t10`). `t10` é eixo próprio de cargo
  legislativo, criado porque senador não administra orçamento.
- **Granularidade:** **uma linha por proposta**, não por célula
  candidato×tema. Um candidato pode ter várias linhas no mesmo tema, cada
  uma com sua própria fonte. Custa mais para popular, e evita reprocessar
  tudo quando o agente da Fase 7 precisar citar fonte por afirmação.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `referencia.json` | temas, partidos, coligações, níveis de fonte, estados de cobertura |
| `candidaturas.json` | pessoa + candidatura + histórico de situação de registro e situação parlamentar |
| `documentos.json` | documentos-fonte, com `acessivel` e `motivo_inacessivel` |
| `posicoes.json` | **tabela central** — uma linha por proposta |
| `registros_legislativos.json` | selo 🔵 — autoria, N:N com candidatura e tema |
| `pesquisas.json` | pesquisas com ficha técnica + pesquisas rejeitadas por falta dela |

Tabelas de lookup pequenas foram agrupadas em `referencia.json`, e os
históricos (`situacao_registro`, `situacao_parlamentar`) ficaram aninhados
dentro de `candidaturas.json` como arrays. Continuam sendo histórico datado,
como o modelo pede — só não geram arquivo próprio enquanto o volume é este.

## Validação

```
python validar.py
```

Exit code 1 se houver erro. As regras que estavam só em prosa nos documentos
agora estão em código:

- **R1** — proposta pertence a candidatura **ou** a partido; estado B exige
  atribuição a partido e `id_candidatura_contexto`
- **R2/D** — estado D exige `busca_realizada_em` e `escopo_da_busca`.
  Sem isso o banco recusa: D é afirmação sobre a nossa busca, não sobre o
  candidato, e sem data e escopo vira acusação de silêncio insustentável
- **R3** — os 5 níveis de fonte, em dois eixos distintos
- **R8** — pesquisa sem `registro_tse` é erro; e
  `constava_no_questionario=false` com percentual preenchido é erro, porque
  ausência do questionário não é 0%
- **R10** — tudo carrega data de referência
- **R11** — CPF não aparece em Silver
- **contexto obrigatório** — contagem de proposições sem
  `situacao_parlamentar` é erro: correta no número, enganosa no sentido
- **curadoria** — `revisado_por_humano: false` aparece como pendência; nada
  é publicável antes da revisão

As regras foram testadas injetando violações de propósito numa cópia — as
três testadas dispararam.

## Estado atual

- **Senado SP 2026:** 15 candidaturas, 56 posições, 25 registros
  legislativos. Completo no que foi levantado.
- **Presidente 2026:** 4 candidatos × 9 temas ainda em markdown
  (`pesquisa-presidente-2026.md`), não migrados.
- **Governador SP:** fontes ainda pendentes.
- **Revisão humana:** 0 de 56 posições revisadas. Nada publicável ainda.

## O que não está aqui

Nenhum CPF, em nenhum arquivo — por princípio, CPF não sai da camada Bronze,
mesmo sendo dado público no TSE.

A camada Bronze (capturas cruas) ainda não foi materializada: hoje as
capturas existem só como URL + data dentro de `documentos.json`.
