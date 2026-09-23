-- ============================================================
-- SonarGest - Sistema de Gestão de Carro de Som
-- Modelo físico do banco (PostgreSQL 14+)
-- ETAPA 2 - Projeto Integrador de Ciência de Dados
-- ============================================================
-- Execute este arquivo UMA vez no banco criado no Supabase/Neon:
--   psql "$DATABASE_URL" -f database/schema.sql
-- ============================================================

-- Remove objetos antigos (permite reexecutar o script durante o desenvolvimento)
DROP VIEW IF EXISTS vw_kpi_motorista CASCADE;
DROP VIEW IF EXISTS vw_kpi_cliente CASCADE;
DROP VIEW IF EXISTS vw_servicos_analitico CASCADE;
DROP TABLE IF EXISTS servicos_log CASCADE;
DROP TABLE IF EXISTS servicos CASCADE;
DROP TABLE IF EXISTS motoristas CASCADE;
DROP TABLE IF EXISTS carros CASCADE;
DROP TABLE IF EXISTS clientes CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- ------------------------------------------------------------
-- USUARIOS: identidade de login (empresa e motoristas)
-- ------------------------------------------------------------
CREATE TABLE usuarios (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(120)  NOT NULL,
    email       VARCHAR(160)  NOT NULL UNIQUE,
    senha_hash  VARCHAR(255)  NOT NULL,               -- bcrypt; NUNCA senha em texto puro
    perfil      VARCHAR(20)   NOT NULL,
    ativo       BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_usuarios_perfil CHECK (perfil IN ('admin', 'motorista'))
);

-- ------------------------------------------------------------
-- CLIENTES: quem contrata o serviço de divulgação
-- ------------------------------------------------------------
CREATE TABLE clientes (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(120) NOT NULL,
    documento   VARCHAR(20)  UNIQUE,                  -- CNPJ/CPF (fictício no seed)
    telefone    VARCHAR(20),
    email       VARCHAR(160),
    endereco    VARCHAR(200),
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- MOTORISTAS: dados operacionais, vinculados 1:1 a um usuário
-- ------------------------------------------------------------
CREATE TABLE motoristas (
    id          SERIAL PRIMARY KEY,
    usuario_id  INTEGER      NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE RESTRICT,
    nome        VARCHAR(120) NOT NULL,
    telefone    VARCHAR(20),
    cnh         VARCHAR(20)  UNIQUE,
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- CARROS: frota de carros de som
-- ------------------------------------------------------------
CREATE TABLE carros (
    id          SERIAL PRIMARY KEY,
    placa       VARCHAR(10)  NOT NULL UNIQUE,
    modelo      VARCHAR(80)  NOT NULL,
    descricao   VARCHAR(200),
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- SERVICOS: tabela-fato. Guarda o PLANEJADO e o REALIZADO.
-- ------------------------------------------------------------
CREATE TABLE servicos (
    id                 SERIAL PRIMARY KEY,
    cliente_id         INTEGER      NOT NULL REFERENCES clientes(id)   ON DELETE RESTRICT,
    motorista_id       INTEGER      NOT NULL REFERENCES motoristas(id) ON DELETE RESTRICT,
    carro_id           INTEGER      NOT NULL REFERENCES carros(id)     ON DELETE RESTRICT,
    data_servico       DATE         NOT NULL,
    hora_prevista      TIME,                                  -- opcional
    horas_contratadas  NUMERIC(5,2) NOT NULL,
    inicio_real        TIMESTAMPTZ,                           -- registrado pelo motorista
    fim_real           TIMESTAMPTZ,                           -- registrado pelo motorista
    status             VARCHAR(20)  NOT NULL DEFAULT 'planejado',
    observacao         TEXT,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_servicos_horas   CHECK (horas_contratadas > 0),
    CONSTRAINT ck_servicos_status  CHECK (status IN ('planejado','em_andamento','finalizado','cancelado')),
    -- término nunca antes do início
    CONSTRAINT ck_servicos_periodo CHECK (fim_real IS NULL OR inicio_real IS NULL OR fim_real > inicio_real),
    -- não existe fim sem início
    CONSTRAINT ck_servicos_fim_sem_inicio CHECK (fim_real IS NULL OR inicio_real IS NOT NULL)
);

-- ------------------------------------------------------------
-- SERVICOS_LOG: trilha de auditoria das ações relevantes
-- ------------------------------------------------------------
CREATE TABLE servicos_log (
    id          SERIAL PRIMARY KEY,
    servico_id  INTEGER     NOT NULL REFERENCES servicos(id) ON DELETE CASCADE,
    usuario_id  INTEGER     REFERENCES usuarios(id) ON DELETE SET NULL,
    acao        VARCHAR(40) NOT NULL,   -- criado, alterado, iniciado, finalizado, cancelado
    detalhe     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- ÍNDICES: aceleram as consultas mais frequentes do sistema
-- ------------------------------------------------------------
CREATE INDEX idx_servicos_data          ON servicos (data_servico);
CREATE INDEX idx_servicos_cliente       ON servicos (cliente_id);
CREATE INDEX idx_servicos_status        ON servicos (status);
-- consulta do app do motorista: "meus serviços nesta data"
CREATE INDEX idx_servicos_motorista_dia ON servicos (motorista_id, data_servico);
CREATE INDEX idx_log_servico            ON servicos_log (servico_id);

-- ------------------------------------------------------------
-- TRIGGER: mantém updated_at sempre correto
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_servicos_updated_at
    BEFORE UPDATE ON servicos
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- ============================================================
-- CAMADA ANALÍTICA (views)
-- Os indicadores NÃO são gravados na tabela: são calculados.
-- Isso evita dado duplicado/inconsistente (normalização).
-- ============================================================

-- View principal: um registro por serviço, já com planejado x realizado
CREATE VIEW vw_servicos_analitico AS
SELECT
    s.id,
    s.data_servico,
    EXTRACT(YEAR  FROM s.data_servico)::INT           AS ano,
    EXTRACT(MONTH FROM s.data_servico)::INT           AS mes,
    TO_CHAR(s.data_servico, 'YYYY-MM')                AS ano_mes,
    TRIM(TO_CHAR(s.data_servico, 'Day'))              AS dia_semana,
    c.id   AS cliente_id,   c.nome AS cliente,
    m.id   AS motorista_id, m.nome AS motorista,
    k.id   AS carro_id,     k.placa AS carro,
    s.status,
    s.horas_contratadas,
    s.inicio_real,
    s.fim_real,
    -- tempo efetivamente realizado, em horas decimais
    ROUND(EXTRACT(EPOCH FROM (s.fim_real - s.inicio_real)) / 3600.0, 2) AS horas_realizadas,
    -- desvio absoluto (realizado - contratado)
    ROUND(EXTRACT(EPOCH FROM (s.fim_real - s.inicio_real)) / 3600.0 - s.horas_contratadas, 2) AS desvio_horas,
    -- desvio percentual
    ROUND(
        ((EXTRACT(EPOCH FROM (s.fim_real - s.inicio_real)) / 3600.0 - s.horas_contratadas)
         / NULLIF(s.horas_contratadas, 0)) * 100, 2
    ) AS desvio_pct,
    -- aderência = realizado / contratado
    ROUND(
        (EXTRACT(EPOCH FROM (s.fim_real - s.inicio_real)) / 3600.0)
        / NULLIF(s.horas_contratadas, 0), 4
    ) AS aderencia,
    -- classificação com tolerância de 5 minutos (0,0833h)
    CASE
        WHEN s.fim_real IS NULL THEN 'Não realizado'
        WHEN EXTRACT(EPOCH FROM (s.fim_real - s.inicio_real))/3600.0 - s.horas_contratadas >  0.0833 THEN 'Acima'
        WHEN EXTRACT(EPOCH FROM (s.fim_real - s.inicio_real))/3600.0 - s.horas_contratadas < -0.0833 THEN 'Abaixo'
        ELSE 'Dentro'
    END AS classificacao
FROM servicos s
JOIN clientes   c ON c.id = s.cliente_id
JOIN motoristas m ON m.id = s.motorista_id
JOIN carros     k ON k.id = s.carro_id;

-- KPIs agregados por cliente
CREATE VIEW vw_kpi_cliente AS
SELECT
    cliente,
    COUNT(*)                                          AS total_servicos,
    COUNT(*) FILTER (WHERE status = 'finalizado')     AS servicos_finalizados,
    SUM(horas_contratadas)                            AS horas_contratadas,
    COALESCE(SUM(horas_realizadas), 0)                AS horas_realizadas,
    COALESCE(SUM(desvio_horas), 0)                    AS desvio_total,
    ROUND(AVG(aderencia)::NUMERIC, 4)                 AS aderencia_media
FROM vw_servicos_analitico
GROUP BY cliente;

-- KPIs agregados por motorista
CREATE VIEW vw_kpi_motorista AS
SELECT
    motorista,
    COUNT(*)                                          AS total_servicos,
    COUNT(*) FILTER (WHERE classificacao = 'Dentro')  AS dentro,
    COUNT(*) FILTER (WHERE classificacao = 'Acima')   AS acima,
    COUNT(*) FILTER (WHERE classificacao = 'Abaixo')  AS abaixo,
    SUM(horas_contratadas)                            AS horas_contratadas,
    COALESCE(SUM(horas_realizadas), 0)                AS horas_realizadas,
    ROUND(AVG(aderencia)::NUMERIC, 4)                 AS aderencia_media
FROM vw_servicos_analitico
GROUP BY motorista;
