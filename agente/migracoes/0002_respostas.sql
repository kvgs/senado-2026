-- Respostas recebidas dos gabinetes.
--
-- A tabela e CAIXA DE ENTRADA, nao fonte de publicacao. O site continua sendo
-- gerado a partir de dados/*.json versionados no Git; promover.py traz o que
-- esta aqui para la. Publicar direto do banco criaria informacao no ar sem
-- passar pelo validador e sem historico — exatamente o que o projeto evita.
--
-- Guarda o texto INTEGRAL, sem edicao. A mensagem que enviamos promete
-- "publicada na integra": resumir aqui quebraria a promessa na origem.

CREATE TABLE IF NOT EXISTS respostas (
  id             TEXT PRIMARY KEY,
  registrada_em  TEXT NOT NULL,        -- quando a autora registrou
  recebida_em    TEXT NOT NULL,        -- data que consta no e-mail recebido
  id_candidatura TEXT NOT NULL,
  id_tema        TEXT,
  canal          TEXT NOT NULL,        -- email | instagram | outro
  remetente      TEXT NOT NULL,        -- endereco ou @ de quem respondeu
  texto          TEXT NOT NULL,        -- integral, sem editar
  perguntas_ids  TEXT,                 -- JSON: quais perguntas da fila responde
  promovida_em   TEXT                  -- quando saiu daqui para dados/respostas.json
);

CREATE INDEX IF NOT EXISTS idx_resp_cand ON respostas (id_candidatura, id_tema);
CREATE INDEX IF NOT EXISTS idx_resp_promov ON respostas (promovida_em);
