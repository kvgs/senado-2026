# Base de conhecimento da curadoria

> **Arquivo gerado.** Não edite aqui — edite `conhecimento/regras.json` e rode
> `python gerar_conhecimento.py`. As regras marcadas como mecânicas são cobradas
> por `validar.py`, que recusa o arquivo em vez de avisar.

Base de conhecimento do projeto: o que cada tipo de fonte pode e nao pode sustentar, e as regras de curadoria que ja foram violadas uma vez. Existe porque regra que mora na cabeca de quem pesquisa e violada na proxima sessao. Aqui ela e consultavel antes de escrever, cobravel pelo validador, e publicavel para o leitor conferir.

*Ideia tomada do AgentSpec (github.com/luanmorenommaciel/agentspec): raciocinio KB-first, consultar a base local antes de agir, com o porque de cada regra registrado. Adaptado de engenharia de dados para curadoria de acervo civico.*

## O que cada tipo de fonte pode sustentar

A pergunta não é se a fonte é boa. É se ela é do **tipo** que sustenta
aquela **espécie** de afirmação. Um cadastro de candidaturas é fonte
excelente para saber o partido de alguém, e imprestável para saber o que
essa pessoa propõe.

### `cadastro` — Cadastro de candidaturas

Base que lista quem se registrou: nome, partido, numero, bens declarados, escolaridade, suplentes. Espelho do registro eleitoral.

**Sustenta:** dados_cadastrais, situacao_de_registro, coligacao, bens_declarados

**Não sustenta:** proposta, posicao_tematica, enfase_de_campanha, cargo_executivo_anterior

**Estados de cobertura permitidos:** nenhum — não sustenta proposta

**Por quê:** Em 24/08/2026 a revisao humana reprovou 15 posicoes atribuidas a 'Base de candidaturas 2026 — SP'. O documento e um cadastro: nao contem proposta nenhuma. Nao foi erro de leitura, foi erro de ORIGEM — a fonte estruturalmente nao podia sustentar aquelas afirmacoes. O tipo dela no acervo era 'reportagem', e nada distinguia um cadastro de uma materia.

### `plano_tse` — Plano ou programa registrado no TSE

Documento que o partido ou a candidatura protocolou na Justica Eleitoral.

**Sustenta:** proposta_do_partido, posicao_tematica

**Não sustenta:** proposta_propria_da_candidatura

**Estados de cobertura permitidos:** B

**Por quê:** Programa partidario cobre a candidatura por atribuicao ao PARTIDO, nunca como proposta pessoal — estado B, jamais A. Confundir os dois poe na boca da pessoa o que esta no programa da sigla.

**Cuidado:** Candidatura ao Senado NAO precisa registrar plano de governo: a Lei 9.504/1997, art. 11, §1º, IX exige proposta so de Presidente, Governador e Prefeito. Todo plano no acervo e do partido, nao do candidato a senador.

### `programa_partidario` — Programa partidario nao registrado

Material programatico publicado pelo partido fora do protocolo eleitoral.

**Sustenta:** proposta_do_partido

**Não sustenta:** proposta_propria_da_candidatura

**Estados de cobertura permitidos:** B

**Por quê:** Material de campanha e documento protocolado na Justica Eleitoral nao valem o mesmo. As propostas mais radicais do MISSAO — extinguir a Justica do Trabalho, reserva de Bitcoin, expulsar ONGs internacionais — NAO estao no documento de 51 paginas registrado no TSE. Registrar sem essa distincao seria imputar ao registro o que so existe no material.

### `site_oficial` — Site oficial da candidatura

Pagina publicada pela propria campanha.

**Sustenta:** declaracao_da_candidatura, posicao_tematica

**Não sustenta:** fato_verificado_por_terceiro

**Estados de cobertura permitidos:** A

**Por quê:** E fonte direta e NAO verificada: diz o que a candidatura afirma, nao o que se comprovou. Exige data de acesso, porque site de campanha muda sem aviso — na revisao de 24/08/2026, 12 de 18 posicoes de site oficial foram reprovadas, varias com a nota 'nao esta no site'.

### `api_dados_abertos` — Dados abertos de casa legislativa

API da Camara, do Senado ou da Assembleia, com proposicoes, autorias, ementas e votos.

**Sustenta:** autoria_legislativa, ementa, voto_nominal, mandato

**Não sustenta:** proposta_de_campanha, enfase_de_campanha, cargo_executivo_anterior

**Estados de cobertura permitidos:** A

**Por quê:** A posicao p077 afirmava enfase de campanha e cargo ministerial citando a API da Camara, que traz atividade legislativa e nao sustenta nem uma coisa nem outra. Atividade legislativa e comportamento registrado; campanha e outra categoria.

**Cuidado:** O link tem de ser da PROPOSICAO, nunca a raiz da API. Apontar para a raiz de um servico parece procedencia sem ser.

### `reportagem` — Materia jornalistica

Texto de veiculo de imprensa sobre a candidatura.

**Sustenta:** declaracao_relatada, fato_com_ressalva

**Não sustenta:** proposta_registrada, citacao_literal_de_documento

**Estados de cobertura permitidos:** A, B, C

**Por quê:** Foi a classe que mais falhou: 7 de 32 conferem, 22%. O modo de falhar mais grave e a TROCA DE CANDIDATO — as posicoes p058, p060 e p062 atribuiam ao Andre do Prado conteudo de uma materia sobre o Geraldo Rufino. Materia menciona varios candidatos no mesmo paragrafo, e a atribuicao se perde.

**Exige:** citacao_literal, conferencia_do_nome_do_candidato_na_materia

### `entrevista` — Entrevista ou sabatina

Declaracao falada, publicada por terceiro.

**Sustenta:** declaracao_da_candidatura

**Não sustenta:** proposta_registrada

**Estados de cobertura permitidos:** A

**Por quê:** A sabatina da TMC com Soninha Francine teve 0 de 7 posicoes confirmadas. Resumo de cobertura de sabatina nao e a sabatina: a paráfrase do veiculo entra como se fosse fala da candidata.

**Exige:** citacao_literal

### `dataset_oficial` — Dataset oficial do TSE

Arquivo de dados abertos publicado pela Justica Eleitoral.

**Sustenta:** dados_cadastrais, contato_declarado, rede_social_declarada, prestacao_de_contas

**Não sustenta:** proposta, posicao_tematica

**Estados de cobertura permitidos:** nenhum — não sustenta proposta

**Por quê:** Mesma natureza do cadastro: e registro, nao programa. Serve para contato e ficha, nunca para posicao.

## Regras

16 regras têm código que as impede, 4 dependem de julgamento na revisão, e 1 ainda não têm cobrança nenhuma.
Cada uma existe porque foi violada uma vez — o campo *por quê* guarda o caso real.

### Impedidas por código

**R-FONTE-01 — Cadastro nao sustenta proposta**

Posicao com estado A ou B nao pode ter como documento uma fonte de tipo cadastro ou dataset_oficial.

*Por quê:* 15 posicoes reprovadas em 24/08/2026 por atribuir politica publica a um cadastro de candidaturas.

*Onde é cobrada:* `validar.py`

**R-FONTE-02 — Programa de partido e estado B, nunca A**

Posicao cujo documento e plano_tse ou programa_partidario tem de ter estado B e atribuicao ao partido.

*Por quê:* Programa da sigla apresentado como proposta pessoal poe na boca da pessoa o que ela nao disse.

*Onde é cobrada:* `validar.py`

**R-ESCOPO-01 — Documento de outro estado nao vale para SP**

Documento com aplicavel_a_sp falso nao pode sustentar posicao nenhuma.

*Por quê:* O terceiro PDF da UP era do ESPIRITO SANTO, e quase entrou como se fosse de SP. Programas partidarios sao registrados por UF.

*Onde é cobrada:* `validar.py`

**R-REDACAO-01 — Parafrase sem citacao literal deriva**

Posicao de fonte oficial sem citacao_literal exige conferencia palavra a palavra na revisao.

*Por quê:* Numa posicao do programa da UP, 'controle estatal dos precos dos alimentos' virou 'congelamento do preco dos alimentos com controle da cadeia produtiva' — outra politica, e 'cadeia produtiva' nao aparece no documento. Era a unica das seis amostradas sem citacao literal.

*Onde é cobrada:* `validar.py (aviso) e revisar.py`

**R-AUTORIA-01 — Ser um dos autores nao e ser o autor**

Autoria com total_autores maior que 1 exige ordem_autoria registrada.

*Por quê:* Das 148 materias de Simone Tebet, as PECs tem em media 33,8 autores e ela e primeira em 1. PEC no Senado exige 27 assinaturas: coautoria nao e iniciativa.

*Onde é cobrada:* `validar.py`

**R-AUSENCIA-01 — Ausencia tem quatro tipos e nunca se colapsam**

A = proposta propria, B = proposta do partido, C = nao aborda o tema, D = nao localizamos fonte. D e afirmacao sobre a NOSSA busca e exige data e escopo.

*Por quê:* Dizer 'nao tem proposta' quando a verdade e 'nao encontramos' transfere para a candidatura uma falha nossa.

*Onde é cobrada:* `validar.py`

**R-PRIVACIDADE-01 — CPF e titulo eleitoral nunca saem**

Nenhum arquivo do repositorio publico contem CPF ou titulo eleitoral, mesmo sendo dado publico no TSE.

*Por quê:* Publico na origem nao autoriza republicacao: a agregacao e o que facilita o mau uso. Em 24/08/2026 um zip com 1.188 CPFs de doadores foi commitado por engano e precisou de reescrita de historico.

*Onde é cobrada:* `validar.py e .gitignore`

**R-PRIVACIDADE-03 — Remetente de resposta so e publicado se ja era publico**

Endereco de quem responde publica-se apenas quando coincide com o contato oficial registrado; nos demais casos, so o dominio.

*Por quê:* Assessor que responde do e-mail proprio nao vira dado publicado por efeito colateral de ter respondido.

*Onde é cobrada:* `agente/promover.py`

**R-NEUTRALIDADE-01 — Sem placar, sem ranking, sem contador de completude**

A camada publica nao expoe contagem de propostas por candidatura, barra de progresso nem ordenacao por quantidade de conteudo.

*Por quê:* Mediria verba de campanha e cobertura de imprensa, nao qualidade de candidatura. Candidatura com assessoria ocupa mais espaco por razoes alheias ao que o eleitor avalia. Uma tabela que mostra o que existe e informacao; um numero que ordena candidatos e veredito nosso vestido de medicao.

*Onde é cobrada:* `validar.py (aviso) e gerar_site.py`

**R-NEUTRALIDADE-02 — Ordem sempre por numero de urna**

Toda listagem de candidaturas sai em ordem de numero de urna, e o site diz que a ordem nao expressa relevancia.

*Por quê:* Qualquer outra ordem e uma opiniao disfarçada de criterio.

*Onde é cobrada:* `gerar_site.py`

**R-IA-01 — Recuperacao vazia nao chama o modelo**

Quando a busca no acervo nao retorna nada, o resumo por IA nao e gerado. A resposta e 'nao ha no acervo', escrita pelo site.

*Por quê:* E onde um chatbot inventaria: modelo de linguagem odeia dizer 'nao sei'.

*Onde é cobrada:* `_template_site.html e agente/worker.js`

**R-IA-02 — Resumo e auditado antes de aparecer**

Todo resumo passa por conferencia mecanica (citacoes existem, nenhum nome fora do lote) e por auditoria de um segundo modelo contra as linhas de origem. Reprovado nao chega na tela.

*Por quê:* Proibir no prompt nao e impedir, e trocar de quem e a proposta e erro que o leitor nao tem como perceber.

*Onde é cobrada:* `agente/worker.js, testada em agente/teste-travas.mjs`

**R-IA-03 — Pesquisa na internet e para curadoria, nunca para o leitor**

A busca web devolve FONTES COM LINK para a autora conferir, e nunca texto redigido para o visitante.

*Por quê:* Contra vinte reportagens onde cinco candidatos aparecem no mesmo paragrafo, trocar de quem e a proposta deixa de ser risco e vira o modo normal de falhar. E a auditoria, que funciona comparando com linhas limpas, fica sem contra o que comparar.

*Onde é cobrada:* `agente/worker.js (rota protegida por token)`

**R-REVISAO-01 — So pessoa marca revisado**

O campo revisado_por_humano so e escrito pela autora, na tela de revisao, ao confirmar contra a fonte. Conferencia automatica vive em campo separado.

*Por quê:* Marcar como revisado o que a IA conferiu faria o dado mentir sobre si mesmo.

*Onde é cobrada:* `revisar.py`

**R-REVISAO-02 — Reprovado sai do site e fica no acervo**

Posicao reprovada na revisao e excluida da publicacao e mantida em posicoes.json com a nota de quem reprovou.

*Por quê:* Erro apagado e erro que volta. Sai a publicacao, nao o registro.

*Onde é cobrada:* `gerar_site.py`

**R-FONTE-05 — Autoria legislativa nao vira posicao em prosa**

Autoria de proposicao vive em registros_legislativos, um registro por proposicao, cada um com o link da propria ficha. Nao entra como posicao que empacota varias proposicoes num texto so.

*Por quê:* Doze posicoes empacotavam de 2 a 4 proposicoes num paragrafo e apontavam para a raiz da API da Camara, porque nao existe URL que abra quatro fichas. Onze foram reprovadas na revisao de 25/08/2026, todas com a mesma nota: 'o link da fonte nao procede'. Nao era link errado, era modelo que nao podia funcionar — e o registro legislativo ja estava modelado certo em outro lugar, com uma ficha por proposicao.

*Onde é cobrada:* `validar.py`

### Dependem de julgamento humano

*Não dá para cobrar em código sem produzir falso erro, e validador que grita errado é validador desligado. Estas vivem na tela de revisão.*

**R-FONTE-03 — API legislativa nao sustenta campanha**

Posicao com documento api_dados_abertos so pode afirmar autoria, ementa, voto ou mandato.

*Por quê:* p077 afirmava enfase de campanha e cargo ministerial citando a API da Camara.

*Onde é cobrada:* `revisao humana`

**R-AUSENCIA-02 — Silencio nao vira posicao**

Pergunta enviada ao gabinete e nao respondida registra-se como pergunta feita, com a data, nunca como posicao ou recusa.

*Por quê:* A mensagem enviada promete isso ao gabinete. E interpretar silencio e inventar.

*Onde é cobrada:* `revisao humana`

**R-AUSENCIA-03 — Zero declarado nao e zero arrecadado**

Valor ausente em janela parcial de prestacao de contas registra-se como nao declarado, jamais como zero.

*Por quê:* Em 24/08/2026, 9 das 15 candidaturas apareciam com R$ 0,00 porque a janela parcial ainda estava aberta. Publicar zero seria afirmacao falsa com aparencia de dado oficial.

*Onde é cobrada:* `revisao humana`

**R-PRIVACIDADE-02 — Contato so de fonte oficial**

E-mail e rede social entram apenas de dados abertos oficiais, nunca de busca ou raspagem.

*Por quê:* Contato errado manda o eleitor escrever para um estranho, e o erro cai sobre quem escreveu.

*Onde é cobrada:* `revisao humana`

### Sem cobrança ainda

*Estão aqui para não serem esquecidas. Regra sem cobrança é lembrete, e lembrete é o que falhou antes.*

**R-FONTE-04 — Link e da proposicao, nao da raiz da API**

Posicao ou registro que cita casa legislativa precisa de URL da propria proposicao.

*Por quê:* 12 posicoes apontavam para dadosabertos.camara.leg.br/api/v2 — a raiz do servico. Link que existe e nao leva a fonte parece procedencia sem ser.

*Onde é cobrada:* `AINDA NAO COBRADA`

