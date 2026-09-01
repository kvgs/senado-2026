# Artes do Instagram

Uma pasta por post. **O número do arquivo é a ordem do slide no carrossel** —
poste na ordem em que o explorador de arquivos mostra.

| pasta | slides | gerado por |
|---|---|---|
| `1-o-site/` | 6 | `gerar_artes.py` |
| `2-de-que-falam/` | 3 | `gerar_artes_temas.py` |
| `3-quem-se-candidata/` | 4 | `gerar_artes_perfil.py` |
| `4-dois-votos/` | 4 | `gerar_artes_dois_votos.py` |
| `5-norte-quem-sao/` | 9 | `gerar_artes_regiao.py --regiao Norte` |
| `5-nordeste-quem-sao/` | 12 | `gerar_artes_regiao.py --regiao Nordeste` |
| `5-centro-oeste-quem-sao/` | 6 | `gerar_artes_regiao.py --regiao Centro-Oeste` |
| `5-sudeste-quem-sao/` | 8 | `gerar_artes_regiao.py --regiao Sudeste` |
| `5-sul-quem-sao/` | 5 | `gerar_artes_regiao.py --regiao Sul` |
| `6-<uf>-<numero>-<nome>/` | 12 | `gerar_artes_candidatura.py --uf AC --todos` |
| `perfil-da-conta/` | — | `gerar_avatar.py` |

O número da **pasta** é a ordem em que os carrosséis foram feitos, e não uma
afirmação sobre o que já foi publicado. Renumere se postar fora de ordem.

Cada pasta tem um `LEGENDA.md` com o texto do post.

O carrossel por região sai para as cinco regiões com o mesmo comando, trocando
`--regiao`: Norte, Nordeste, Centro-Oeste, Sudeste, Sul. O `LEGENDA.md` também é
gerado — os números dele saem do acervo na mesma passada, e não da cópia da
legenda de outra região.

**As cinco regiões não têm o mesmo número de slides.** Um estado com mais de 15
candidaturas ocupa dois slides: Piauí (20), Minas Gerais (17) e Rio de Janeiro
(16). Por isso o Nordeste tem 12 slides e o Sudeste, 8. O Instagram aceita até 20
por carrossel, então todos cabem.

## Um carrossel por candidatura

A série `6-` é **uma pasta por candidatura**, com um slide por tema. É a única
que mostra uma pessoa sozinha, e por isso é a que mais precisa de cuidado:

- **Os cinco rótulos são os do site**, e não três. Proposta própria, proposta do
  partido, não aborda o tema, não localizamos fonte, ainda não trabalhado.
  Juntar os três últimos num "não achamos" faria a arte mentir sobre nós mesmos.
- **O placar da capa compara a candidatura com ela mesma**, nunca com outra. E
  vem com a ressalva impressa: os números são sobre o nosso levantamento.
- **Quando o programa do partido não entrou no acervo, a capa diz o motivo**,
  lido de `dados/programas-recusados.json`. Sem isso, "0 do partido" leria como
  afirmação sobre a pessoa.
- **A identidade do estado é a silhueta dele** (da mesma malha do IBGE que o mapa
  da página inicial usa) mais uma cor tirada da bandeira, escurecida até passar
  4,5:1 sobre o papel. Estado sem cor definida faz o script parar.

São 12 imagens por candidatura. O Acre inteiro dá 96 imagens e 6,8 MB.

## Nada aqui é editado à mão

Todas as artes são **geradas**. Rode o script da tabela e o PNG é reescrito no
lugar certo, no tamanho certo (1080×1440, o retrato 4:5 do feed).

Isso importa por um motivo específico: os números das artes 2, 3 e 4 **saem do
acervo na hora da geração**. Se a revisão humana reprovar uma posição, a próxima
geração muda o gráfico. Número digitado à mão numa arte que vai para o Instagram
envelhece calado, e lá não dá para corrigir depois.

As três fontes do site são `.woff2`, que o Pillow não abre. Elas são convertidas
para `fontes-ttf/` (derivado, fora do Git). Se faltar, o `gerar_artes.py` diz o
comando na mensagem de erro.
