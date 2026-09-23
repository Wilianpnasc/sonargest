"""Cálculos de indicadores.

Funções puras: recebem valores e devolvem resultados, sem tocar no banco.
Isso torna as regras fáceis de testar (ver tests/) e reaproveitáveis pelo
dashboard e pela camada de análise.
"""

from __future__ import annotations

from datetime import datetime

from app.config import TOLERANCIA_HORAS

DENTRO = "Dentro"
ACIMA = "Acima"
ABAIXO = "Abaixo"
NAO_REALIZADO = "Não realizado"


def horas_realizadas(inicio: datetime | None, fim: datetime | None) -> float | None:
    """Tempo efetivamente realizado, em horas decimais (ex.: 4h10 -> 4.17)."""
    if inicio is None or fim is None:
        return None
    if fim <= inicio:
        raise ValueError("O término não pode ser anterior ou igual ao início.")
    return round((fim - inicio).total_seconds() / 3600, 2)


def desvio_horas(contratadas: float, realizadas: float | None) -> float | None:
    """Diferença entre o realizado e o contratado. Positivo = passou do combinado."""
    if realizadas is None:
        return None
    return round(realizadas - float(contratadas), 2)


def desvio_percentual(contratadas: float, realizadas: float | None) -> float | None:
    """Desvio em percentual sobre o contratado."""
    contratadas = float(contratadas)
    if realizadas is None or contratadas == 0:
        return None
    return round(((realizadas - contratadas) / contratadas) * 100, 2)


def aderencia(contratadas: float, realizadas: float | None) -> float | None:
    """Aderência = realizado / contratado. 1,00 significa execução exata."""
    contratadas = float(contratadas)
    if realizadas is None or contratadas == 0:
        return None
    return round(realizadas / contratadas, 4)


def classificar(contratadas: float, realizadas: float | None) -> str:
    """Classifica o serviço com tolerância de 5 minutos."""
    desvio = desvio_horas(contratadas, realizadas)
    if desvio is None:
        return NAO_REALIZADO
    if desvio > TOLERANCIA_HORAS:
        return ACIMA
    if desvio < -TOLERANCIA_HORAS:
        return ABAIXO
    return DENTRO


def formatar_horas(valor: float | None) -> str:
    """Converte horas decimais em texto legível: 4.17 -> '4h10'."""
    if valor is None:
        return "--"
    sinal = "-" if valor < 0 else ""
    total_minutos = round(abs(valor) * 60)
    return f"{sinal}{total_minutos // 60}h{total_minutos % 60:02d}"
