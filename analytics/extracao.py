"""Extração dos dados do PostgreSQL para DataFrames do pandas.

Este é o único módulo da camada de análise que fala com o banco. Ele lê a
view `vw_servicos_analitico`, que já entrega o dado enriquecido (horas
realizadas, desvio, aderência e classificação) calculado no servidor — mais
rápido e sem risco de a fórmula divergir entre aplicação e análise.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from app.db import consultar_df

BASE = "vw_servicos_analitico"

COLUNAS_NUMERICAS = [
    "horas_contratadas",
    "horas_realizadas",
    "desvio_horas",
    "desvio_pct",
    "aderencia",
]


def carregar_servicos(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    apenas_finalizados: bool = False,
) -> pd.DataFrame:
    """Devolve a base analítica de serviços, opcionalmente filtrada por período."""
    filtros = ["1 = 1"]
    parametros: dict = {}

    if data_inicio:
        filtros.append("data_servico >= :data_inicio")
        parametros["data_inicio"] = data_inicio
    if data_fim:
        filtros.append("data_servico <= :data_fim")
        parametros["data_fim"] = data_fim
    if apenas_finalizados:
        filtros.append("status = 'finalizado'")

    sql = f"SELECT * FROM {BASE} WHERE {' AND '.join(filtros)} ORDER BY data_servico"
    df = consultar_df(sql, parametros)
    return _tipar(df)


def _tipar(df: pd.DataFrame) -> pd.DataFrame:
    """Converte NUMERIC do Postgres (que vem como Decimal) para float.

    Sem isso, operações como média e soma no pandas ficam lentas ou falham
    ao misturar Decimal com float.
    """
    if df.empty:
        return df
    for coluna in COLUNAS_NUMERICAS:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    df["data_servico"] = pd.to_datetime(df["data_servico"])
    return df


def carregar_kpi_cliente() -> pd.DataFrame:
    return consultar_df("SELECT * FROM vw_kpi_cliente ORDER BY horas_contratadas DESC")


def carregar_kpi_motorista() -> pd.DataFrame:
    return consultar_df("SELECT * FROM vw_kpi_motorista ORDER BY horas_contratadas DESC")
