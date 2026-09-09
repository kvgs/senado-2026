# O que o acervo do Acre mostra — análise

6 slides: capa com o número principal, três recortes de dados, as
ressalvas do que os números não medem, e o fecho.
Gerado por `python gerar_artes_analise_uf.py --uf AC`.

---

## Legenda — copie daqui até as hashtags, sem mexer

O Acre é o primeiro de dois estados do site conferidos por inteiro — e agora dá para olhar os números.

São 8 candidaturas e 10 temas. As 112 informações publicadas foram lidas uma a uma por uma pessoa. Aqui está o que elas mostram. 👇

▪️ De cada dez informações publicadas, 1,8 são da própria candidatura: 20 de 112. 60 vêm do programa do partido e 32 são temas em que não localizamos nada.

▪️ Nenhum tema tem proposta própria em mais de três das oito candidaturas. Habitação, Tecnologia e Inteligência Artificial não têm nenhuma: o que aparece ali é programa de partido.

▪️ Uma candidatura declarou site ao TSE. Seis tinham. Os outros cinco foram encontrados um a um — e é de onde saíram 19 das 20 propostas próprias do estado. Antes dessa busca o acervo tinha 1.

⚠️ O QUE ESTES NÚMEROS NÃO DIZEM: nenhum gráfico aqui compara candidaturas entre si. Contar propostas por pessoa e ordenar mediria verba de campanha e tamanho de assessoria, não qualidade de candidatura. Por isso todos os recortes são por tema e por origem da informação.

E "sem conteúdo" não quer dizer que a candidatura não tenha proposta: quer dizer que NÓS não localizamos — e cada uma dessas 32 linhas diz, no site, onde procuramos.

🔗 kvgs.github.io/senado-2026 — dados abertos, código público.

#eleições2026 #senado #acre #dadosabertos #votoconsciente #transparência #jornalismodedados #política #brasil

---

## Como os números foram apurados

Todos saem do acervo **na hora de gerar a imagem**, e nenhum foi digitado. Se a
revisão reprovar uma informação, a próxima geração muda o gráfico.

O script **para com erro** se o estado tiver alguma linha sem decisão da revisão.
Gráfico tem cara de fato e não mostra o selo "não revisado" que cada linha
carrega no site.

## Decisões de visualização

- **Nenhum gráfico compara candidaturas.** É a regra que mais restringiu o que
  podia ser desenhado.
- **Uma série por gráfico.** As barras por tema têm uma cor só.
- **Os sites viraram número, não gráfico.** São três valores soltos; barra de
  valor único é pior que o número.
- **Zero é um dado.** Tema sem proposta própria aparece com a trilha da escala e
  o "0" escrito, e não como linha em branco.
- **A escala vai até o total de candidaturas**, e não até o maior valor. Cortar a
  escala faria "3 de 8" parecer muito.
- **A cor é a do estado**: verde, a família de cor da bandeira do Acre; tom escolhido para dar 5,01:1 sobre o papel
