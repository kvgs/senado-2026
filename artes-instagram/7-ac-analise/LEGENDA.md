# O que o acervo do Acre mostra — análise

6 slides: capa com o número principal, três recortes de dados, as ressalvas do que
os números não medem, e o fecho.
Gerado por `python gerar_artes_analise_uf.py --uf AC`.

---

## Legenda

**O Acre é o primeiro estado do site conferido por inteiro — e agora dá para olhar
os números.**

São 8 candidaturas e 10 temas. As 112 informações publicadas foram lidas uma a uma
por uma pessoa. Aqui está o que elas mostram. 👇

▪️ **De cada 10 informações, menos de 2 são da própria candidatura.** 20 são
proposta de quem disputa; 60 vêm do programa do partido; 32 são temas em que não
localizamos nada.

▪️ **Nenhum tema tem proposta própria em mais de 3 das 8 candidaturas.** Habitação
e Tecnologia não têm nenhuma: o que aparece ali é programa de partido.

▪️ **Uma candidatura declarou site ao TSE. Seis tinham.** Os outros cinco foram
encontrados um a um — e é de onde saíram 19 das 20 propostas próprias do estado.
Antes dessa busca, o acervo tinha uma.

**O que estes números NÃO dizem:** nenhum gráfico aqui compara candidaturas entre
si. Contar propostas por pessoa e ordenar mediria verba de campanha e tamanho de
assessoria, não qualidade de candidatura. Por isso todos os recortes são por tema
e por origem da informação.

E "sem conteúdo" não quer dizer que a candidatura não tenha proposta: quer dizer
que **nós** não localizamos — e cada uma dessas 32 linhas diz, no site, onde
procuramos.

🔗 kvgs.github.io/senado-2026 — dados abertos, código público.

#eleições2026 #senado #acre #dadosabertos #votoconsciente #transparência #jornalismodedados #política #brasil

---

## Como os números foram apurados

Todos saem do acervo **na hora de gerar a imagem**, e nenhum foi digitado. Se a
revisão reprovar uma informação, a próxima geração muda o gráfico. Número digitado
à mão numa arte de Instagram envelhece calado, e lá não dá para corrigir depois.

O script **para com erro** se o estado tiver alguma linha sem decisão da revisão.
Gráfico tem cara de fato e não mostra o selo "não revisado" que cada linha carrega
no site; publicar número de acervo por revisar seria dar força de medição ao que
ainda é rascunho.

## Decisões de visualização

- **Nenhum gráfico compara candidaturas.** É a regra que mais restringiu o que
  podia ser desenhado. Os recortes são por tema, por origem da informação e sobre
  a nossa própria busca.
- **Uma série por gráfico.** As barras por tema têm uma cor só. Colorir cada barra
  mais escura conforme o valor seria duplicar o comprimento na cor sem acrescentar
  informação.
- **Os sites viraram número, não gráfico.** São três valores soltos; barra de valor
  único é pior que o número.
- **Zero é um dado.** Habitação e Tecnologia aparecem com a trilha da escala e o
  "0" escrito, e não como linha em branco.
- **A escala vai até 8**, que é o total de candidaturas, e não até o maior valor.
  Cortar a escala em 3 faria "3 de 8" parecer muito.

## Cores medidas, não escolhidas no olho

Verde do Acre `#0B5D2A` (7,3:1 sobre o papel) para o que é da candidatura, cinza
médio `#8C8279` (3,4:1) para o que é do partido, cinza claro para a ausência —
sempre com o número escrito dentro.

O primeiro par testado foi descartado por medição: verde `#007A2E` com cinza
`#6B6560` dá **1,05:1 entre si**, ou seja, a mesma barra para quem não distingue
cor. O que separa os segmentos aqui é **luminância** e rótulo direto, que
sobrevivem a daltonismo e a impressão em preto e branco.

O rótulo "60" também foi refeito: em texto claro sobre o cinza médio dava 3,12:1 e
reprovava no mínimo de 4,5:1 para texto. Em tinta escura dá 5,00:1.

## Um erro que a conferência pegou antes de publicar

A primeira versão do slide dos sites dizia que **o acervo tinha 0 proposta própria
no Acre antes da busca**. Era falso: uma candidatura declarou o site ao TSE, e a
proposta dela o coletor acharia de qualquer jeito. O número certo é 1. A conta
somava todas as propostas vindas de site, em vez de separar site declarado de site
achado.
