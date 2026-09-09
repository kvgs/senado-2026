# O que o acervo do Amapá mostra — análise

6 slides: capa com o número principal, três recortes de dados, as
ressalvas do que os números não medem, e o fecho.
Gerado por `python gerar_artes_analise_uf.py --uf AP`.

---

## Legenda — copie daqui até as hashtags, sem mexer

O Amapá é o segundo de dois estados do site conferidos por inteiro — e agora dá para olhar os números.

São 9 candidaturas e 10 temas. As 122 informações publicadas foram lidas uma a uma por uma pessoa. Aqui está o que elas mostram. 👇

▪️ De cada dez informações publicadas, 0,7 são da própria candidatura: 9 de 122. 100 vêm do programa do partido e 13 são temas em que não localizamos nada.

▪️ Nenhum tema tem proposta própria em mais de duas das nove candidaturas. Educação, Infraestrutura e Mobilidade Urbana, Habitação, Tecnologia e Inteligência Artificial não têm nenhuma: o que aparece ali é programa de partido.

▪️ Três candidaturas declararam site ao TSE. Seis tinham. Os outros três foram encontrados um a um — e é de onde saíram 5 das 9 propostas próprias do estado. Antes dessa busca o acervo tinha 4.

⚠️ O QUE ESTES NÚMEROS NÃO DIZEM: nenhum gráfico aqui compara candidaturas entre si. Contar propostas por pessoa e ordenar mediria verba de campanha e tamanho de assessoria, não qualidade de candidatura. Por isso todos os recortes são por tema e por origem da informação.

E "sem conteúdo" não quer dizer que a candidatura não tenha proposta: quer dizer que NÓS não localizamos — e cada uma dessas 13 linhas diz, no site, onde procuramos.

🔗 kvgs.github.io/senado-2026 — dados abertos, código público.

#eleições2026 #senado #amapá #dadosabertos #votoconsciente #transparência #jornalismodedados #política #brasil

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
  escala faria "2 de 9" parecer muito.
- **A cor é a do estado**: azul, uma das cores da bandeira do Amapá; tom escolhido para dar 7,24:1 sobre o papel. Azul e não verde para o estado não se confundir com o Acre no feed
