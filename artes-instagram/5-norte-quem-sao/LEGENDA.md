# Conheça as candidaturas do Norte

Nove slides: capa clara, os sete estados em ordem alfabética, e o convite.
A capa e o convite são bege; os estados, brancos — o carrossel tem começo,
corpo e fim sem precisar de palavra dizendo isso.
Foto, número de urna, nome e @ do Instagram — em ordem de número de urna.

---

## Legenda

**Você conhece as 74 pessoas que disputam o Senado pelo Norte?**

São 7 estados, 74 candidaturas — e este ano você vota em duas.

Deslize e veja todas: foto, número de urna, nome e o @ do Instagram, estado por estado. 👉

**Se você ainda não decidiu, comente aqui o que te deixa indeciso.** Um tema que
falta, uma dúvida sobre alguém, uma fonte que você conhece e o site não tem.

Duas coisas sobre como isto é feito:

▪️ A ordem é a do **número de urna**, e só. Este site não ordena candidaturas por
preferência, por pesquisa nem por nada que pareça um ranking.

▪️ As fotos e os **@ do Instagram** vêm do que cada candidatura declarou no
registro no TSE. Nada aqui foi procurado por nós: contato achado em busca manda
o eleitor escrever para um estranho.

▪️ Onde está escrito **"sem Instagram no registro"**, é isso mesmo — a
candidatura não declarou um Instagram utilizável ao TSE. Não é que não
procuramos: é que não há o que buscar na fonte oficial.

No site, cada candidatura tem uma página com **o que já foi levantado**, a fonte
de cada informação e o que ainda não foi encontrado.

🔗 kvgs.github.io/senado-2026 — dados abertos, código público.

#eleições2026 #senado #norte #acre #amapá #amazonas #pará #rondônia #roraima
#tocantins #dadosabertos #votoconsciente #transparência #política #brasil

---

## Notas de produção

- **Um slide por estado**, e não por região: o Nordeste tem 103 candidaturas e
  não caberiam numa grade legível.
- **Cinco colunas** porque as 315 fotos do TSE têm 161×225 pixels. Cinco por
  linha dá 164px cada — o tamanho nativo. Três por linha exigiria ampliar 2,1×,
  e rosto ampliado fica borrado.
- **Nome nunca é cortado.** Se não couber em duas linhas, o corpo diminui.
- Cada slide traz quantas informações daquele estado já estão no site.
- `--sem-capa` gera o carrossel abrindo direto na primeira grade de rostos.
- **O @ nunca é cortado.** O corpo da fonte cede primeiro; se nem no menor
  couber, ele quebra em duas linhas por largura. Handle cortado não serve para
  procurar ninguém, que é a única coisa que ele existe para fazer.
- **"Sem Instagram no registro", e não "não localizado".** Dos 14 do Norte sem
  @, dez não declararam nada ao TSE — não é que a busca falhou, é que não há o
  que buscar. Dois declararam outras redes e dois declararam algo que não vira
  canal. A frase escolhida é verdadeira nos três casos.
- **Os 60 @ do Norte foram auditados um a um:** todos vêm de uma URL de
  instagram.com declarada ao TSE, nenhum é repetido entre candidaturas e nenhum
  é página de partido.

## Nada de promessa

Nem a arte nem a legenda anunciam o próximo post, e nenhuma das duas diz que o
que aparecer nos comentários será atendido. Convidar não obriga a nada, e
calendário anunciado vira dívida.

O que estava escrito antes e saiu: "o que aparecer nos comentários vira trabalho
— eu vou atrás" e "no próximo carrossel começa a outra metade". No lugar, a
caixa aponta para o que o site JA tem hoje.

## Para uso interno

Trocar `--regiao` no comando gera as outras quatro regiões. Ao adaptar a
legenda, os números mudam: Nordeste 103 em 9 estados · Sudeste 59 em 4 ·
Centro-Oeste 44 em 4 · Sul 35 em 3.

Se um dia houver um carrossel de propostas, decidir antes o que fazer com as
candidaturas que ainda não têm nada no acervo — no Norte são 12 das 74.
