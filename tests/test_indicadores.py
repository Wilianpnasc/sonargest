"""Testes dos indicadores em pandas (analytics/indicadores.py)."""

from __future__ import annotations

import pandas as pd

from analytics.indicadores import (
    distribuicao_classificacao,
    horas_perdidas_e_excedidas,
    maiores_desvios,
    por_motorista,
    resumo_geral,
)


def base() -> pd.DataFrame:
    """Três finalizados (dentro, acima, abaixo) e um planejado."""
    return pd.DataFrame(
        [
            {
                "id": 1,
                "data_servico": pd.Timestamp("2025-05-01"),
                "cliente": "Cliente A",
                "motorista": "João",
                "status": "finalizado",
                "horas_contratadas": 4.0,
                "horas_realizadas": 4.0,
                "desvio_horas": 0.0,
                "desvio_pct": 0.0,
                "aderencia": 1.0,
                "classificacao": "Dentro",
            },
            {
                "id": 2,
                "data_servico": pd.Timestamp("2025-05-02"),
                "cliente": "Cliente B",
                "motorista": "João",
                "status": "finalizado",
                "horas_contratadas": 4.0,
                "horas_realizadas": 6.0,
                "desvio_horas": 2.0,
                "desvio_pct": 50.0,
                "aderencia": 1.5,
                "classificacao": "Acima",
            },
            {
                "id": 3,
                "data_servico": pd.Timestamp("2025-05-03"),
                "cliente": "Cliente A",
                "motorista": "Maria",
                "status": "finalizado",
                "horas_contratadas": 4.0,
                "horas_realizadas": 3.0,
                "desvio_horas": -1.0,
                "desvio_pct": -25.0,
                "aderencia": 0.75,
                "classificacao": "Abaixo",
            },
            {
                "id": 4,
                "data_servico": pd.Timestamp("2025-05-04"),
                "cliente": "Cliente C",
                "motorista": "Maria",
                "status": "planejado",
                "horas_contratadas": 4.0,
                "horas_realizadas": None,
                "desvio_horas": None,
                "desvio_pct": None,
                "aderencia": None,
                "classificacao": "Não realizado",
            },
        ]
    )


def test_resumo_geral_ignora_nao_finalizados_no_realizado():
    r = resumo_geral(base())
    assert r["total_servicos"] == 4
    assert r["servicos_finalizados"] == 3
    assert r["horas_contratadas"] == 16.0
    assert r["horas_realizadas"] == 13.0
    assert r["desvio_total"] == 1.0
    assert r["pct_dentro"] == 33.3


def test_distribuicao_soma_cem_por_cento():
    d = distribuicao_classificacao(base())
    assert set(d["classificacao"]) == {"Dentro", "Acima", "Abaixo"}
    assert d["servicos"].sum() == 3
    assert round(d["percentual"].sum()) == 100


def test_horas_perdidas_e_excedidas():
    h = horas_perdidas_e_excedidas(base())
    assert h["horas_excedidas"] == 2.0
    assert h["horas_perdidas"] == 1.0


def test_por_motorista_agrupa_corretamente():
    m = por_motorista(base()).set_index("motorista")
    # João: 2 finalizados. Maria: 1 finalizado + 1 planejado (o total conta os dois).
    assert m.loc["João", "servicos"] == 2
    assert m.loc["Maria", "servicos"] == 2
    assert m.loc["João", "horas_realizadas"] == 10.0
    assert m.loc["Maria", "horas_realizadas"] == 3.0


def test_maior_desvio_vem_primeiro():
    top = maiores_desvios(base(), quantidade=1)
    assert abs(top.iloc[0]["desvio_horas"]) == 2.0


def test_base_vazia_nao_quebra():
    vazio = base().iloc[0:0]
    assert resumo_geral(vazio)["total_servicos"] == 0
    assert distribuicao_classificacao(vazio)["servicos"].sum() == 0
