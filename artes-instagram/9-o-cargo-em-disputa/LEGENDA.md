# O cargo em disputa — 12 slides

Gerado por `python gerar_artes_senado.py`.
Abre no valor do subsídio, que é o gancho, e fecha no site.

---

## Legenda

**R$ 46.366,19 é quanto um senador recebe de subsídio por mês.**

Valor com vigência em abr/2026, no demonstrativo do próprio Senado — não em notícia
sobre ele. Quem fixa o valor não é o senador: a Constituição dá isso ao Congresso, e
manda que seja idêntico ao de deputado federal (art. 49, VII).

E o cargo que esse valor paga, ponto por ponto — cada um com o artigo ao lado. 👇

▪️ **Quem fixa não é ele** — O valor é fixado pelo Congresso, e é idêntico ao de
deputado federal. (Constituição, art. 49, VII)
▪️ **O que ele faz?** — Deputado representa o povo. Senador representa o estado.
(Constituição, arts. 45 e 46)
▪️ **8 anos** — É o dobro do mandato de presidente, governador e deputado.
(Constituição, art. 46, §1º)
▪️ **2 ou 1** — Em 2026 são dois votos para senador. Em 2022 foi um. (Constituição, art.
46, §2º)
▪️ **+2 nomes** — Cada senador é eleito com dois suplentes. (Constituição, art. 46, §3º)
▪️ **Por que pesa** — Nenhum ministro do STF chega ao tribunal sem passar pelo Senado.
(Constituição, art. 101, parágrafo único)
▪️ **Julga o presidente** — Processar e julgar o presidente por crime de
responsabilidade é competência privativa do Senado. (Constituição, art. 52, I)
▪️ **3/5, dois turnos** — Nenhuma emenda à Constituição passa sem três quintos do
Senado, em dois turnos. (Constituição, art. 60, §2º)
▪️ **Suspende lei** — Depois de o STF declarar uma lei inconstitucional, é o Senado que
suspende a execução dela. (Constituição, art. 52, X)
▪️ **35 anos** — É a idade mínima para o Senado — a mesma da Presidência da República.
(Constituição, art. 14, §3º, VI, "a")

Todas as citações destes slides foram conferidas palavra por palavra contra o texto
compilado da Constituição publicado pela Câmara dos Deputados e contra o demonstrativo
de remuneração do Senado. Os dois arquivos estão no repositório, com hash.

🔗 kvgs.github.io/senado-2026 — dados abertos, código público.

#eleições2026 #senado #votoconsciente #dadosabertos #transparência #educaçãopolítica #constituição #política #brasil

---

## O que ficou de fora, e por quê

**Verba de gabinete, cota parlamentar (CEAPS) e auxílio-moradia.** O Senado
publica os três, mas eles não foram levantados aqui. Cada um tem regra própria e
teto que varia por estado — é onde o número circula errado. O slide do subsídio
diz, escrito, que não os inclui.

**Qualquer frase sobre o que o eleitor sabe ou não sabe.** Seria afirmação sobre
pessoas que não foram medidas. É a mesma regra do carrossel dos dois votos.

**Adjetivo sobre a importância do cargo.** "Por que pesa" está respondido em
quatro competências com artigo ao lado: aprovar ministro do STF, julgar o
presidente por crime de responsabilidade, os três quintos de qualquer emenda, e
suspender lei declarada inconstitucional. Isso é conferível; "o Senado é
poderoso" não é.

## Uma citação que teria saído errada

A frase sobre o STF ia citar o **art. 52, III, "a"**, que diz apenas
"magistrados, nos casos estabelecidos nesta Constituição" — não menciona o
Supremo. A citação certa é o **art. 101, parágrafo único**. Artigo errado no pé
de uma arte é o mesmo defeito do link que apontava para a página errada do DOU.

## Como as citações são conferidas

`python institucional.py` abre os arquivos de `fontes/`, confere cada citação
palavra por palavra e **para com erro** se alguma não estiver lá. Ele distingue
dois casos: frase que não existe na fonte, e frase que só casa sem acento — que
são problemas diferentes. O gerador chama o conferidor antes de desenhar, então
não existe arte com citação não conferida.
