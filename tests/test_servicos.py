"""Testes das regras de negócio de serviços (app/services.py)."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from app import services
from app.models import STATUS_CANCELADO, STATUS_EM_ANDAMENTO, STATUS_FINALIZADO, STATUS_PLANEJADO
from app.services import RegraDeNegocioError

HOJE = date(2025, 5, 10)
INICIO = datetime(2025, 5, 10, 8, 0)
FIM = datetime(2025, 5, 10, 12, 0)


def _criar(db, base, horas=4.0, motorista=None):
    return services.criar_servico(
        db,
        base["admin"],
        cliente_id=base["cliente"].id,
        motorista_id=(motorista or base["motorista"]).id,
        carro_id=base["carro"].id,
        data_servico=HOJE,
        horas_contratadas=horas,
    )


# ------------------------------------------------------------- criação
def test_criar_servico_nasce_planejado(db, base_minima):
    servico = _criar(db, base_minima)
    assert servico.status == STATUS_PLANEJADO
    assert servico.inicio_real is None and servico.fim_real is None


@pytest.mark.parametrize("campo", ["cliente_id", "motorista_id", "carro_id", "data_servico"])
def test_criar_servico_exige_campos_obrigatorios(db, base_minima, campo):
    dados = dict(
        cliente_id=base_minima["cliente"].id,
        motorista_id=base_minima["motorista"].id,
        carro_id=base_minima["carro"].id,
        data_servico=HOJE,
        horas_contratadas=4.0,
    )
    dados[campo] = None
    with pytest.raises(RegraDeNegocioError):
        services.criar_servico(db, base_minima["admin"], **dados)


@pytest.mark.parametrize("horas", [0, -3])
def test_horas_contratadas_devem_ser_maiores_que_zero(db, base_minima, horas):
    with pytest.raises(RegraDeNegocioError):
        _criar(db, base_minima, horas=horas)


def test_motorista_nao_pode_criar_servico(db, base_minima):
    with pytest.raises(RegraDeNegocioError):
        services.criar_servico(
            db,
            base_minima["joao"],
            cliente_id=base_minima["cliente"].id,
            motorista_id=base_minima["motorista"].id,
            carro_id=base_minima["carro"].id,
            data_servico=HOJE,
            horas_contratadas=4.0,
        )


# ------------------------------------------------- execução pelo motorista
def test_iniciar_e_finalizar_calcula_o_realizado(db, base_minima):
    servico = _criar(db, base_minima)
    services.iniciar_servico(db, base_minima["joao"], servico.id, momento=INICIO)
    assert servico.status == STATUS_EM_ANDAMENTO

    services.finalizar_servico(db, base_minima["joao"], servico.id, momento=FIM)
    assert servico.status == STATUS_FINALIZADO
    assert (servico.fim_real - servico.inicio_real) == timedelta(hours=4)


def test_nao_finaliza_sem_iniciar(db, base_minima):
    servico = _criar(db, base_minima)
    with pytest.raises(RegraDeNegocioError):
        services.finalizar_servico(db, base_minima["joao"], servico.id, momento=FIM)


def test_nao_inicia_duas_vezes(db, base_minima):
    servico = _criar(db, base_minima)
    services.iniciar_servico(db, base_minima["joao"], servico.id, momento=INICIO)
    with pytest.raises(RegraDeNegocioError):
        services.iniciar_servico(db, base_minima["joao"], servico.id, momento=INICIO)


def test_termino_nao_pode_ser_anterior_ao_inicio(db, base_minima):
    servico = _criar(db, base_minima)
    services.iniciar_servico(db, base_minima["joao"], servico.id, momento=FIM)
    with pytest.raises(RegraDeNegocioError):
        services.finalizar_servico(db, base_minima["joao"], servico.id, momento=INICIO)


def test_servico_cancelado_nao_pode_ser_iniciado(db, base_minima):
    servico = _criar(db, base_minima)
    services.cancelar_servico(db, base_minima["admin"], servico.id, "cliente desistiu")
    assert servico.status == STATUS_CANCELADO
    with pytest.raises(RegraDeNegocioError):
        services.iniciar_servico(db, base_minima["joao"], servico.id, momento=INICIO)


def test_servico_finalizado_nao_pode_ser_alterado_nem_cancelado(db, base_minima):
    servico = _criar(db, base_minima)
    services.iniciar_servico(db, base_minima["joao"], servico.id, momento=INICIO)
    services.finalizar_servico(db, base_minima["joao"], servico.id, momento=FIM)

    with pytest.raises(RegraDeNegocioError):
        services.cancelar_servico(db, base_minima["admin"], servico.id, "tarde demais")
    with pytest.raises(RegraDeNegocioError):
        services.alterar_servico(
            db,
            base_minima["admin"],
            servico.id,
            cliente_id=base_minima["cliente"].id,
            motorista_id=base_minima["motorista"].id,
            carro_id=base_minima["carro"].id,
            data_servico=HOJE,
            horas_contratadas=6.0,
        )


# -------------------------------------------------------- autorização
def test_motorista_nao_age_em_servico_de_outro(db, base_minima):
    servico = _criar(db, base_minima, motorista=base_minima["outro_motorista"])
    with pytest.raises(RegraDeNegocioError):
        services.iniciar_servico(db, base_minima["joao"], servico.id, momento=INICIO)


def test_itinerario_traz_apenas_os_servicos_do_motorista_logado(db, base_minima):
    _criar(db, base_minima)
    _criar(db, base_minima, motorista=base_minima["outro_motorista"])
    db.flush()

    meus = services.itinerario_do_dia(db, base_minima["joao"], HOJE)
    assert len(meus) == 1
    assert meus[0].motorista_id == base_minima["motorista"].id
