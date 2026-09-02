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
| `7-<uf>-analise/` | 6 | `gerar_artes_analise_uf.py --uf AC` |
| `8-<uf>-reels/` | 1 vídeo | `gerar_reels_uf.py --uf AC` |
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
  da página inicial usa) mais uma cor na **família de cor** da bandeira. O tom é
  escolha nossa, calibrada para passar 4,5:1 sobre o papel — não é o hex oficial
  da bandeira, e o `PALETA` diz isso. Estado sem cor definida faz o script parar.
- **A cor também separa os estados.** O Amapá entrou no azul da bandeira dele, e
  não no verde: verde ao lado do verde do Acre faria dois estados parecerem o
  mesmo post no feed.

São 12 imagens por candidatura. O Acre inteiro dá 96 imagens e 6,8 MB.

## O carrossel de análise

A série `7-` é a única com **gráficos**, e por isso tem duas travas próprias:

- **Só existe para estado 100% revisado.** O script para com erro se houver linha
  sem decisão da revisão. Gráfico tem cara de fato e não mostra o selo "não
  revisado" que cada linha carrega no site.
- **Nenhum gráfico compara candidaturas entre si.** Contar propostas por pessoa e
  ordenar mediria verba de campanha e tamanho de assessoria, não qualidade de
  candidatura — é o mesmo alerta que o `validar.py` dá. Os recortes são por tema,
  por origem da informação e sobre a nossa própria busca.

As cores foram medidas em contraste, não escolhidas no olho, e o `LEGENDA.md` da
pasta registra o que foi descartado e por quê.

## O Reels

A série `8-` é a única que não é imagem: um MP4 vertical de 1080×1920, cinco cenas,
27 segundos. Os quadros são desenhados com o mesmo Pillow, a mesma tipografia e a
mesma paleta das artes estáticas; o ffmpeg só junta.

- **Não tem áudio, e isso é deliberado.** Reels toca sem som por padrão e este
  projeto não licencia trilha. A música entra no próprio Instagram, onde ela é
  licenciada — colar uma faixa aqui seria uso não licenciado.
- **A área segura é menor que a tela.** O Instagram desenha a interface dele por
  cima do vídeo: perfil no alto, legenda, áudio e botões embaixo. Tudo o que se lê
  fica entre 230 e 1560 de 1920. A primeira versão tinha o rodapé em `ALT-150`,
  atrás dos botões: o endereço do site, que é a razão de o vídeo existir, ficava
  invisível.
- **O tempo é contado em segundos, não em fração da cena.** Com fração o título da
  cena da barra levava 3,5s para acabar de entrar, e no meio disso cada linha
  ficava num alpha diferente — no telefone lia como degradê cinza com a última
  linha apagada. A regra em segundos: texto de Reels tem de estar legível em menos
  de 1s.
- **As frases são contas.** "Menos de duas", "seis tinham", "dois temas" saem do
  acervo na geração, com a concordância resolvida. Onde a redação não cabe no dado
  o script para com erro, em vez de publicar a frase de outro estado.
- **O roteiro muda com o acervo.** A cena dos sites achados só existe onde houve
  site achado; a dos temas em zero, só onde há tema em zero.
- **A trava do estado 100% revisado vale aqui e é mais forte** que na série `7-`:
  número animado tem ainda mais cara de fato do que número impresso.

`--so-quadros` escreve uma amostra de PNG em `_quadros/` (fora do Git) para
conferir a arte sem esperar o encode.

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
