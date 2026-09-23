"""Funções de apresentação compartilhadas pelas telas.

Aqui só há formatação e montagem de tabelas. Nenhuma regra de negócio:
os cálculos vêm de app/calculos.py e as validações de app/services.py.
"""

from __future__ import annotations

import pandas as pd

from app.calculos import (
    classificar,
    desvio_horas,
    desvio_percentual,
    formatar_horas,
    horas_realizadas,
)
from app.config import FUSO
from app.models import Servico

ROTULO_STATUS = {
    "planejado": "Planejado",
    "em_andamento": "Em andamento",
    "finalizado": "Finalizado",
    "cancelado": "Cancelado",
}


def hora_local(valor) -> str:
    """Mostra o horário no fuso de Brasília (o banco guarda em UTC)."""
    if valor is None:
        return "--"
    return valor.astimezone(FUSO).strftime("%H:%M")


def servicos_para_dataframe(servicos: list[Servico]) -> pd.DataFrame:
    """Monta a tabela Data | Cliente | ... | Realizado | Diferença | Status."""
    linhas = []
    for s in servicos:
        contratadas = float(s.horas_contratadas)
        realizadas = horas_realizadas(s.inicio_real, s.fim_real)
        linhas.append(
            {
                "ID": s.id,
                "Data": s.data_servico.strftime("%d/%m/%Y"),
                "Cliente": s.cliente.nome,
                "Motorista": s.motorista.nome,
                "Carro": s.carro.placa,
                "Contratado": formatar_horas(contratadas),
                "Início": hora_local(s.inicio_real),
                "Término": hora_local(s.fim_real),
                "Realizado": formatar_horas(realizadas),
                "Diferença": formatar_horas(desvio_horas(contratadas, realizadas)),
                "Desvio %": desvio_percentual(contratadas, realizadas),
                "Classificação": classificar(contratadas, realizadas),
                "Status": ROTULO_STATUS.get(s.status, s.status),
            }
        )
    colunas = [
        "ID", "Data", "Cliente", "Motorista", "Carro", "Contratado",
        "Início", "Término", "Realizado", "Diferença", "Desvio %",
        "Classificação", "Status",
    ]
    return pd.DataFrame(linhas, columns=colunas)


def opcoes(registros, rotulo=lambda r: r.nome) -> dict[str, int]:
    """Transforma uma lista de entidades em {texto exibido: id} para selectbox."""
    return {rotulo(r): r.id for r in registros}
