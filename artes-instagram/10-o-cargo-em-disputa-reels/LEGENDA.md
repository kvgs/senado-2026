# Reels — o cargo em disputa

Vídeo vertical de 40s, 7 cenas, **sem áudio**.
Gerado por `python gerar_reels_senado.py`.

---

## Legenda

**R$ 46.366,19 é quanto um senador recebe de subsídio por mês.**

Vigência em abril de 2026, no demonstrativo do próprio Senado — não em notícia sobre
ele. Quem fixa o valor não é o senador: a Constituição dá isso ao Congresso, e manda que
seja idêntico ao de deputado federal.

E o cargo que esse valor paga: senador representa o estado, e não a população dele; o
mandato é de oito anos, o dobro do de presidente; em 2026 são dois votos, e em 2022 foi
um; e nenhum ministro do STF entra no tribunal, nenhum presidente é julgado por crime de
responsabilidade e nenhuma emenda à Constituição passa sem o Senado.

Cada uma dessas frases aparece no vídeo com o artigo ao lado, e todas foram conferidas
palavra por palavra contra o texto compilado da Constituição publicado pela Câmara dos
Deputados e contra o demonstrativo de remuneração do Senado.

🔗 kvgs.github.io/senado-2026 — 315 candidaturas nos 27 estados, tema por tema.

#eleições2026 #senado #votoconsciente #dadosabertos #transparência #educaçãopolítica #constituição #política #brasil

---

## Antes de postar

**Sem trilha.** A música entra no próprio Instagram, onde é licenciada.

**O carrossel `9-o-cargo-em-disputa/` conta a mesma coisa em 12 imagens**, com a
citação inteira em cada slide. O vídeo prende; o carrossel é onde a frase da
fonte cabe legível e fica no grid para consulta.

## Como as frases são conferidas

Vídeo e carrossel leem o **mesmo** `dados/institucional-senado.json`, e os dois
chamam `institucional.py` antes de desenhar. Ele abre os arquivos de `fontes/`,
confere cada citação palavra por palavra e para com erro se alguma não estiver
lá — distinguindo frase inexistente de frase que só casa sem acento. Mudar um
texto num lugar muda nos dois; não existe versão do vídeo com frase diferente da
do carrossel.

## O que ficou de fora

Verba de gabinete, cota parlamentar e auxílio-moradia: o Senado publica os três,
mas não foram levantados, e a cena do subsídio diz isso na tela. Nada sobre o que
o eleitor sabe ou não sabe. Nenhum adjetivo sobre a importância do cargo — "por
que pesa" está em quatro competências com artigo ao lado.

## As cenas

1. o subsídio — 5.5s
2. quem fixa o valor — 5.0s
3. o que o cargo é — 6.0s
4. o mandato — 5.0s
5. quantos votos — 6.0s
6. as quatro competências — 8.0s
7. o site — 5.0s
