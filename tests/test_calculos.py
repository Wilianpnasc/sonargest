"""Testes das funções puras de indicadores (app/calculos.py)."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.calculos import (
    ABAIXO,
    ACIMA,
    DENTRO,
    NAO_REALIZADO,
    aderencia,
    classificar,
    desvio_horas,
    desvio_percentual,
    formatar_horas,
    horas_realizadas,
)


def _dt(hora: int, minuto: int = 0) -> datetime:
    return datetime(2025, 5, 10, hora, minuto)


def test_horas_realizadas_converte_para_horas_decimais():
    assert horas_realizadas(_dt(8), _dt(12, 10)) == 4.17


def test_horas_realizadas_sem_registro_devolve_none():
    assert horas_realizadas(None, _dt(12)) is None
    assert horas_realizadas(_dt(8), None) is None


def test_horas_realizadas_recusa_fim_antes_do_inicio():
    with pytest.raises(ValueError):
        horas_realizadas(_dt(12), _dt(8))


def test_desvio_positivo_quando_passa_do_contratado():
    assert desvio_horas(4, 5.5) == 1.5


def test_desvio_negativo_quando_entrega_menos():
    assert desvio_horas(4, 3.0) == -1.0


def test_desvio_percentual():
    assert desvio_percentual(4, 5) == 25.0
    assert desvio_percentual(0, 5) is None


def test_aderencia_um_significa_execucao_exata():
    assert aderencia(4, 4) == 1.0
    assert aderencia(4, 2) == 0.5


def test_classificacao_usa_tolerancia_de_cinco_minutos():
    assert classificar(4, 4.05) == DENTRO       # 3 minutos a mais
    assert classificar(4, 4.5) == ACIMA
    assert classificar(4, 3.5) == ABAIXO
    assert classificar(4, None) == NAO_REALIZADO


def test_formatar_horas_legivel():
    assert formatar_horas(4.17) == "4h10"
    assert formatar_horas(-1.5) == "-1h30"
    assert formatar_horas(None) == "--"
