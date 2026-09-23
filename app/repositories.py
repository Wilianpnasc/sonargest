"""Camada de acesso a dados.

Só esta camada conversa com o banco. As regras de negócio ficam em services.py
e as telas ficam em app/paginas. Essa separação é o que permite testar as
regras sem depender do banco.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Carro, Cliente, Motorista, Servico, ServicoLog, Usuario


# ---------------------------------------------------------------- usuários
def buscar_usuario_por_email(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.email == email.strip().lower()))


def buscar_motorista_por_usuario(db: Session, usuario_id: int) -> Motorista | None:
    return db.scalar(select(Motorista).where(Motorista.usuario_id == usuario_id))


# ---------------------------------------------------------------- cadastros
def listar_clientes(db: Session, apenas_ativos: bool = True) -> list[Cliente]:
    consulta = select(Cliente).order_by(Cliente.nome)
    if apenas_ativos:
        consulta = consulta.where(Cliente.ativo.is_(True))
    return list(db.scalars(consulta))


def listar_motoristas(db: Session, apenas_ativos: bool = True) -> list[Motorista]:
    consulta = select(Motorista).order_by(Motorista.nome)
    if apenas_ativos:
        consulta = consulta.where(Motorista.ativo.is_(True))
    return list(db.scalars(consulta))


def listar_carros(db: Session, apenas_ativos: bool = True) -> list[Carro]:
    consulta = select(Carro).order_by(Carro.placa)
    if apenas_ativos:
        consulta = consulta.where(Carro.ativo.is_(True))
    return list(db.scalars(consulta))


def salvar(db: Session, registro) -> object:
    """Insere ou atualiza qualquer entidade do modelo."""
    db.add(registro)
    db.flush()
    return registro


# ---------------------------------------------------------------- serviços
def buscar_servico(db: Session, servico_id: int) -> Servico | None:
    return db.get(Servico, servico_id)


def listar_servicos(
    db: Session,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    motorista_id: int | None = None,
    cliente_id: int | None = None,
    status: str | None = None,
) -> list[Servico]:
    consulta = select(Servico).order_by(Servico.data_servico.desc(), Servico.id.desc())
    if data_inicio:
        consulta = consulta.where(Servico.data_servico >= data_inicio)
    if data_fim:
        consulta = consulta.where(Servico.data_servico <= data_fim)
    if motorista_id:
        consulta = consulta.where(Servico.motorista_id == motorista_id)
    if cliente_id:
        consulta = consulta.where(Servico.cliente_id == cliente_id)
    if status:
        consulta = consulta.where(Servico.status == status)
    return list(db.scalars(consulta).unique())


def listar_servicos_do_motorista_no_dia(
    db: Session, motorista_id: int, dia: date
) -> list[Servico]:
    """Consulta da tela do motorista (usa o índice motorista_id + data_servico)."""
    consulta = (
        select(Servico)
        .where(Servico.motorista_id == motorista_id, Servico.data_servico == dia)
        .order_by(Servico.hora_prevista.nulls_last(), Servico.id)
    )
    return list(db.scalars(consulta).unique())


def registrar_log(
    db: Session, servico_id: int, usuario_id: int | None, acao: str, detalhe: str | None = None
) -> None:
    db.add(ServicoLog(servico_id=servico_id, usuario_id=usuario_id, acao=acao, detalhe=detalhe))
