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
