-- ============================================================
-- SonarGest - Consultas analíticas principais
-- Cada consulta responde a uma pergunta de negócio do projeto.
-- Rode com: psql "$DATABASE_URL" -f database/queries.sql
-- ============================================================

-- 1) Qual cliente mais contrata horas?
SELECT cliente, SUM(horas_contratadas) AS horas_contratadas
FROM vw_servicos_analitico
GROUP BY cliente
ORDER BY horas_contratadas DESC;

-- 2) Qual cliente apresenta o maior desvio (horas a mais/menos)?
SELECT cliente, ROUND(SUM(desvio_horas), 2) AS desvio_total
FROM vw_servicos_analitico
WHERE status = 'finalizado'
GROUP BY cliente
ORDER BY ABS(SUM(desvio_horas)) DESC;

-- 3) Qual motorista executa mais horas?
SELECT motorista, ROUND(SUM(horas_realizadas), 2) AS horas_realizadas
FROM vw_servicos_analitico
WHERE status = 'finalizado'
GROUP BY motorista
ORDER BY horas_realizadas DESC;

-- 4) Qual motorista tem maior aderência ao contratado (mais perto de 1,0)?
SELECT motorista, ROUND(AVG(aderencia), 4) AS aderencia_media
FROM vw_servicos_analitico
WHERE status = 'finalizado'
GROUP BY motorista
ORDER BY ABS(AVG(aderencia) - 1) ASC;

-- 5) Em quais dias da semana existe maior demanda?
SELECT dia_semana, COUNT(*) AS servicos
FROM vw_servicos_analitico
GROUP BY dia_semana
ORDER BY servicos DESC;

-- 6) Quantas horas foram perdidas (abaixo) e excedidas (acima)?
SELECT
    ROUND(SUM(desvio_horas) FILTER (WHERE desvio_horas > 0), 2) AS horas_excedidas,
    ROUND(SUM(desvio_horas) FILTER (WHERE desvio_horas < 0), 2) AS horas_perdidas
FROM vw_servicos_analitico
WHERE status = 'finalizado';

-- 7) Percentual de serviços dentro / acima / abaixo do contratado
SELECT
    classificacao,
    COUNT(*) AS servicos,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentual
FROM vw_servicos_analitico
WHERE status = 'finalizado'
GROUP BY classificacao
ORDER BY servicos DESC;

-- 8) Qual cliente gera maior excesso de horas?
SELECT cliente, ROUND(SUM(desvio_horas), 2) AS excesso
FROM vw_servicos_analitico
WHERE status = 'finalizado' AND desvio_horas > 0
GROUP BY cliente
ORDER BY excesso DESC;

-- 9) Existe motorista com padrão sistemático de excesso ou falta?
SELECT
    motorista,
    ROUND(AVG(desvio_horas), 2)   AS desvio_medio,
    ROUND(STDDEV(desvio_horas), 2) AS desvio_padrao,
    COUNT(*)                       AS servicos
FROM vw_servicos_analitico
WHERE status = 'finalizado'
GROUP BY motorista
ORDER BY desvio_medio DESC;

-- 10) Como o desempenho evolui ao longo dos meses?
SELECT
    ano_mes,
    COUNT(*)                            AS servicos,
    SUM(horas_contratadas)              AS contratadas,
    ROUND(SUM(horas_realizadas), 2)     AS realizadas,
    ROUND(SUM(desvio_horas), 2)         AS desvio
FROM vw_servicos_analitico
WHERE status = 'finalizado'
GROUP BY ano_mes
ORDER BY ano_mes;
