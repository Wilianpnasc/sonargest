"""Indicadores (KPIs) calculados em pandas sobre a base analítica.

Todas as funções recebem um DataFrame vindo de `analytics.extracao` e
devolvem outro DataFrame ou um dicionário — nenhuma delas acessa o banco.
Isso torna a camada testável sem conexão e reutilizável pelo dashboard e
pelo notebook.

Fórmulas de negócio:
    desvio_horas = horas_realizadas - horas_contratadas
    desvio_pct   = desvio_horas / horas_contratadas * 100
    aderencia    = horas_realizadas / horas_contratadas
"""

from __future__ import annotations

import pandas as pd

CLASSES = ["Dentro", "Acima", "Abaixo"]


def _finalizados(df: pd.DataFrame) -> pd.DataFrame:
    """Só serviços concluídos entram nos indicadores de desempenho."""
    if df.empty:
        return df
    return df[df["status"] == "finalizado"]


def resumo_geral(df: pd.DataFrame) -> dict:
    """Números do topo do dashboard."""
    fin = _finalizados(df)
    total = len(df)
    contratadas = float(df["horas_contratadas"].sum()) if total else 0.0
    realizadas = float(fin["horas_realizadas"].sum()) if len(fin) else 0.0
    dentro = int((fin["classificacao"] == "Dentro").sum()) if len(fin) else 0

    return {
        "total_servicos": total,
        "servicos_finalizados": len(fin),
        "horas_contratadas": round(contratadas, 2),
        "horas_realizadas": round(realizadas, 2),
        "desvio_total": round(realizadas - float(fin["horas_contratadas"].sum() if len(fin) else 0), 2),
        "aderencia_media": round(float(fin["aderencia"].mean()), 4) if len(fin) else 0.0,
        "media_horas_por_servico": round(float(df["horas_contratadas"].mean()), 2) if total else 0.0,
        "media_desvio": round(float(fin["desvio_horas"].mean()), 2) if len(fin) else 0.0,
        "pct_dentro": round(dentro / len(fin) * 100, 1) if len(fin) else 0.0,
    }


def distribuicao_classificacao(df: pd.DataFrame) -> pd.DataFrame:
    """Quantos serviços ficaram Dentro, Acima e Abaixo do contratado."""
    fin = _finalizados(df)
    if fin.empty:
        return pd.DataFrame({"classificacao": CLASSES, "servicos": [0, 0, 0], "percentual": [0.0] * 3})
    contagem = fin["classificacao"].value_counts().reindex(CLASSES, fill_value=0)
    return pd.DataFrame(
        {
            "classificacao": contagem.index,
            "servicos": contagem.values,
            "percentual": (contagem.values / len(fin) * 100).round(1),
        }
    )


def por_cliente(df: pd.DataFrame) -> pd.DataFrame:
    """Ranking de clientes: volume contratado, realizado e desvio."""
    return _agrupar(df, "cliente")


def por_motorista(df: pd.DataFrame) -> pd.DataFrame:
    """Desempenho por motorista, ordenado por aderência."""
    tabela = _agrupar(df, "motorista")
    if tabela.empty:
        return tabela
    return tabela.sort_values("aderencia_media", ascending=False, ignore_index=True)


def _agrupar(df: pd.DataFrame, chave: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    contratadas = df.groupby(chave)["horas_contratadas"].agg(["sum", "count"])
    fin = _finalizados(df)

    if fin.empty:
        tabela = contratadas.rename(columns={"sum": "horas_contratadas", "count": "servicos"})
        tabela[["horas_realizadas", "desvio_horas", "aderencia_media"]] = 0.0
        return tabela.reset_index()

    realizado = fin.groupby(chave).agg(
        horas_realizadas=("horas_realizadas", "sum"),
        desvio_horas=("desvio_horas", "sum"),
        aderencia_media=("aderencia", "mean"),
        finalizados=("id", "count"),
    )

    tabela = (
        contratadas.rename(columns={"sum": "horas_contratadas", "count": "servicos"})
        .join(realizado, how="left")
        .fillna(0)
        .round(2)
        .reset_index()
    )
    return tabela.sort_values("horas_contratadas", ascending=False, ignore_index=True)


def evolucao_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Série temporal contratado × realizado por mês."""
    if df.empty:
        return pd.DataFrame()
    fin = _finalizados(df)
    base = df.groupby("ano_mes")["horas_contratadas"].sum().rename("horas_contratadas")
    real = fin.groupby("ano_mes")["horas_realizadas"].sum().rename("horas_realizadas") if not fin.empty else None
    tabela = pd.concat([base, real], axis=1).fillna(0).round(2).reset_index()
    if "horas_realizadas" not in tabela.columns:
        tabela["horas_realizadas"] = 0.0
    tabela["desvio_horas"] = (tabela["horas_realizadas"] - tabela["horas_contratadas"]).round(2)
    return tabela


def servicos_por_dia(df: pd.DataFrame) -> pd.DataFrame:
    """Demanda diária — mostra picos de operação."""
    if df.empty:
        return pd.DataFrame()
    tabela = df.groupby("data_servico").agg(servicos=("id", "count"), horas_contratadas=("horas_contratadas", "sum"))
    return tabela.round(2).reset_index()


def demanda_por_dia_semana(df: pd.DataFrame) -> pd.DataFrame:
    """Dias da semana com maior volume."""
    if df.empty:
        return pd.DataFrame()
    tabela = df.groupby("dia_semana").agg(servicos=("id", "count"), horas_contratadas=("horas_contratadas", "sum"))
    return tabela.sort_values("servicos", ascending=False).round(2).reset_index()


def horas_perdidas_e_excedidas(df: pd.DataFrame) -> dict:
    """Separa o desvio em horas não entregues e horas além do contratado."""
    fin = _finalizados(df)
    if fin.empty:
        return {"horas_perdidas": 0.0, "horas_excedidas": 0.0, "saldo": 0.0}
    perdidas = float(fin.loc[fin["desvio_horas"] < 0, "desvio_horas"].sum())
    excedidas = float(fin.loc[fin["desvio_horas"] > 0, "desvio_horas"].sum())
    return {
        "horas_perdidas": round(abs(perdidas), 2),
        "horas_excedidas": round(excedidas, 2),
        "saldo": round(excedidas + perdidas, 2),
    }


def maiores_desvios(df: pd.DataFrame, quantidade: int = 10) -> pd.DataFrame:
    """Serviços com o maior desvio absoluto — candidatos a investigação."""
    fin = _finalizados(df)
    if fin.empty:
        return pd.DataFrame()
    tabela = fin.assign(desvio_abs=fin["desvio_horas"].abs())
    colunas = [
        "data_servico",
        "cliente",
        "motorista",
        "horas_contratadas",
        "horas_realizadas",
        "desvio_horas",
        "desvio_pct",
        "classificacao",
    ]
    return tabela.nlargest(quantidade, "desvio_abs")[colunas].reset_index(drop=True)
