# Reels — Acre

Vídeo vertical de 27s, 5 cenas, **sem áudio**.
Gerado por `python gerar_reels_uf.py --uf AC`.

---

## Legenda

**8 candidaturas ao Senado pelo Acre. Você sabe o que elas propõem?**

O Acre é o primeiro estado do site conferido por inteiro: 112 informações lidas uma a
uma por uma pessoa, cada uma com a fonte, o trecho citado e a data.

▪️ **De cada dez informações publicadas, 1,8 são da própria candidatura** (20 de 112).
60 vêm do programa do partido e 32 são temas em que não localizamos nada.

▪️ **Uma candidatura declarou site ao TSE. Seis tinham.** Os outros cinco foram
encontrados um a um — e é de onde saíram 19 das 20 propostas próprias do estado.

▪️ **Dois temas não têm proposta própria de ninguém:** Habitação, Tecnologia e
Inteligência Artificial. O que aparece ali vem do programa dos partidos.

**"Sem conteúdo" é sobre a nossa busca, não sobre a candidatura.** Cada uma dessas
linhas diz, no site, onde procuramos e quando.

🔗 kvgs.github.io/senado-2026 — dados abertos, código público.

#eleições2026 #senado #acre #dadosabertos #votoconsciente #transparência #jornalismodedados #política #brasil

---

## Antes de postar

**O vídeo não tem trilha.** Reels toca sem som por padrão e este script não produz
áudio; a música entra no próprio Instagram, onde ela é licenciada. Trilha colada
aqui seria uso não licenciado.

**A área segura foi respeitada.** O Instagram desenha a própria interface por cima
do Reels — perfil no alto, legenda, áudio e botões embaixo. Tudo o que se lê está
entre 230 e 1560 de 1920.

## Como os números foram apurados

Todos saem do acervo na hora de gerar o vídeo, **e as frases também**: "menos de
duas", "seis tinham", "dois temas" são contas, e não redação. O script para com erro
quando a redação não cabe no dado — por exemplo se a própria candidatura deixar de
ser minoria, porque aí a história é outra e o texto precisa ser reescrito à mão.

O roteiro também muda com o acervo: a cena dos sites achados só existe onde houve
site achado, e a dos temas em zero só existe onde há tema em zero. Cena com o número
zero e a frase de outro estado é o defeito que isto evita.

**A trava do carrossel de análise vale aqui, e mais forte:** só roda para estado
100% revisado. Número animado tem ainda mais cara de fato do que número impresso, e
não mostra o selo "não revisado" que cada linha carrega no site.

## O que se vê em cada cena

1. `cena_abre` — 4.0s
2. `cena_contador` — 6.0s
3. `cena_barra` — 7.0s
4. `cena_zero` — 5.0s
5. `cena_fecha` — 5.0s
