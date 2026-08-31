# Conheça as candidaturas do Nordeste

12 slides: capa clara, 9 estados em ordem alfabética, e o convite.
A capa e o convite são bege; os estados, brancos — o carrossel tem começo,
corpo e fim sem precisar de palavra dizendo isso.
Foto, número de urna, nome e @ do Instagram — em ordem de número de urna.

---

## Legenda

**Você conhece as 103 pessoas que disputam o Senado pelo Nordeste?**

São 9 estados, 103 candidaturas — e este ano você vota em duas.

Deslize e veja todas: foto, número de urna, nome e o @ do Instagram, estado por estado. 👉

**Se você ainda não decidiu, comente aqui o que te deixa indeciso.** Um tema que
falta, uma dúvida sobre alguém, uma fonte que você conhece e o site não tem.

Três coisas sobre como isto é feito:

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

#eleições2026 #senado #nordeste #alagoas #bahia #ceará #maranhão #paraíba #pernambuco #piauí #riograndedonorte #sergipe #dadosabertos #votoconsciente #transparência #política #brasil

---

## Números desta região

- 103 candidaturas em 9 estados
- 74 com @ declarado ao TSE, 29 sem
- dos 29 sem @: 19 não declararam nenhuma rede ao TSE, 5 declararam outras redes e 5 declararam só o site do partido
- 18 ainda não têm nenhuma informação no acervo

**Os 74 @ do Nordeste foram conferidos um a um:** todos saem de uma URL
de instagram.com declarada ao TSE, nenhum se repete entre candidaturas e nenhum
é página de partido.

## Notas de produção

- **Um slide por estado**, e não por região: o Nordeste tem 103 candidaturas e
  não caberiam numa grade legível.
- **Estado com mais de 15 candidaturas vira dois slides.** Com cinco colunas
  cabem três fileiras; forçar a quarta fez a última passar por cima do rodapé.
  Encolher a foto não resolve — com a célula mais estreita o nome quebra em mais
  linhas e a fileira fica *mais alta*. Hoje o gerador para com erro em vez de
  desenhar por cima do rodapé, porque isso já foi publicado uma vez sem ninguém ver.
- **Cinco colunas** porque as 315 fotos do TSE têm 161×225 pixels. Cinco por
  linha dá 164px cada — o tamanho nativo. Três por linha exigiria ampliar 2,1×,
  e rosto ampliado fica borrado.
- **Nome nunca é cortado.** Se não couber em duas linhas, o corpo diminui.
- **O @ nunca é cortado.** O corpo da fonte cede primeiro; se nem no menor
  couber, ele quebra em duas linhas por largura. Handle cortado não serve para
  procurar ninguém, que é a única coisa que ele existe para fazer.
- **"Sem Instagram no registro", e não "não localizado".** A frase precisa ser
  verdadeira nos três casos acima — quem não declarou nada, quem declarou outra
  rede e quem declarou só o site do partido. "Não localizado" diria que a nossa
  busca falhou, e não houve busca nenhuma: por regra, contato só entra de fonte
  oficial.
- Cada slide traz quantas informações daquele estado já estão no site.
- `--sem-capa` gera o carrossel abrindo direto na primeira grade de rostos.
- Gerado por `python gerar_artes_regiao.py --regiao Nordeste`.

## Nada de promessa

Nem a arte nem a legenda anunciam o próximo post, e nenhuma das duas diz que o
que aparecer nos comentários será atendido. Convidar não obriga a nada, e
calendário anunciado vira dívida.

O que estava escrito antes e saiu: "o que aparecer nos comentários vira trabalho
— eu vou atrás" e "no próximo carrossel começa a outra metade". No lugar, a
caixa aponta para o que o site JÁ tem hoje.
