"""Respostas às perguntas de negócio do Projeto Integrador.

Cada função devolve uma resposta pronta para leitura, combinando as funções
de `analytics.indicadores`. É a camada que traduz número em informação — o
que o professor espera ver na etapa de "análise".

Uso rápido:
    python -m analytics.perguntas
"""

from __future__ import annotations

import pandas as pd

from analytics import indicadores
from analytics.extracao import carregar_servicos


def cliente_com_mais_horas(df: pd.DataFrame) -> pd.Series | None:
    tabela = indicadores.por_cliente(df)
    return None if tabela.empty else tabela.iloc[0]


def cliente_com_maior_excesso(df: pd.DataFrame) -> pd.Series | None:
    tabela = indicadores.por_cliente(df)
    if tabela.empty:
        return None
    return tabela.sort_values("desvio_horas", ascending=False).iloc[0]


def motorista_mais_aderente(df: pd.DataFrame) -> pd.Series | None:
    tabela = indicadores.por_motorista(df)
    if tabela.empty:
        return None
    tabela = tabela.assign(distancia=(tabela["aderencia_media"] - 1).abs())
    return tabela.sort_values("distancia").iloc[0]


def motorista_com_mais_horas(df: pd.DataFrame) -> pd.Series | None:
    tabela = indicadores.por_motorista(df)
    if tabela.empty:
        return None
    return tabela.sort_values("horas_realizadas", ascending=False).iloc[0]


def dia_de_maior_demanda(df: pd.DataFrame) -> pd.Series | None:
    tabela = indicadores.servicos_por_dia(df)
    if tabela.empty:
        return None
    return tabela.sort_values("servicos", ascending=False).iloc[0]


def relatorio(df: pd.DataFrame) -> str:
    """Monta um texto com as principais conclusões da base."""
    resumo = indicadores.resumo_geral(df)
    saldo = indicadores.horas_perdidas_e_excedidas(df)
    linhas = [
        "=== SonarGest — leitura analítica ===",
        f"Serviços: {resumo['total_servicos']} ({resumo['servicos_finalizados']} finalizados)",
        f"Horas contratadas: {resumo['horas_contratadas']} | realizadas: {resumo['horas_realizadas']}",
        f"Aderência média: {resumo['aderencia_media']} | dentro do contratado: {resumo['pct_dentro']}%",
        f"Horas não entregues: {saldo['horas_perdidas']} | horas excedentes: {saldo['horas_excedidas']}",
    ]

    if (cliente := cliente_com_mais_horas(df)) is not None:
        linhas.append(f"Cliente com mais horas: {cliente['cliente']} ({cliente['horas_contratadas']}h contratadas)")
    if (excesso := cliente_com_maior_excesso(df)) is not None:
        linhas.append(f"Cliente com maior excesso: {excesso['cliente']} ({excesso['desvio_horas']}h)")
    if (aderente := motorista_mais_aderente(df)) is not None:
        linhas.append(f"Motorista mais aderente: {aderente['motorista']} (aderência {aderente['aderencia_media']})")
    if (produtivo := motorista_com_mais_horas(df)) is not None:
        linhas.append(f"Motorista com mais horas: {produtivo['motorista']} ({produtivo['horas_realizadas']}h)")
    if (dia := dia_de_maior_demanda(df)) is not None:
        linhas.append(f"Dia de maior demanda: {dia['data_servico'].date()} ({int(dia['servicos'])} serviços)")

    return "\n".join(linhas)


if __name__ == "__main__":
    print(relatorio(carregar_servicos()))
