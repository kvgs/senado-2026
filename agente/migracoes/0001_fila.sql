-- Fila de perguntas que o acervo nao respondeu.
--
-- Guarda o minimo: a pergunta, para quem e, e quando. Sem IP, sem identificador
-- de visitante, sem cookie. Uma pergunta politica diz muito sobre quem pergunta,
-- e este projeto nao tem motivo nenhum para saber quem foi.

CREATE TABLE IF NOT EXISTS perguntas (
  id            TEXT PRIMARY KEY,
  criada_em     TEXT NOT NULL,
  pergunta      TEXT NOT NULL,
  id_candidatura TEXT NOT NULL,
  id_tema       TEXT,
  -- pendente: esperando moderacao | enviada: a curadoria perguntou ao gabinete
  -- descartada: fora de escopo, ofensiva, ou duplicada
  estado        TEXT NOT NULL DEFAULT 'pendente',
  decidida_em   TEXT,
  nota          TEXT
);

CREATE INDEX IF NOT EXISTS idx_pendentes ON perguntas (estado, id_candidatura, id_tema);
CREATE INDEX IF NOT EXISTS idx_criada ON perguntas (criada_em);
