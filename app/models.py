"""Mapeamento objeto-relacional (ORM) das tabelas definidas em database/schema.sql.

Cada classe representa uma tabela; cada atributo, uma coluna.
"""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

PERFIL_ADMIN = "admin"
PERFIL_MOTORISTA = "motorista"

STATUS_PLANEJADO = "planejado"
STATUS_EM_ANDAMENTO = "em_andamento"
STATUS_FINALIZADO = "finalizado"
STATUS_CANCELADO = "cancelado"


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[str] = mapped_column(String(20), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    motorista: Mapped["Motorista | None"] = relationship(back_populates="usuario", uselist=False)

    @property
    def eh_admin(self) -> bool:
        return self.perfil == PERFIL_ADMIN


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    documento: Mapped[str | None] = mapped_column(String(20), unique=True)
    telefone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(160))
    endereco: Mapped[str | None] = mapped_column(String(200))
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Motorista(Base):
    __tablename__ = "motoristas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(20))
    cnh: Mapped[str | None] = mapped_column(String(20), unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuario: Mapped[Usuario] = relationship(back_populates="motorista")


class Carro(Base):
    __tablename__ = "carros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    placa: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    modelo: Mapped[str] = mapped_column(String(80), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(200))
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Servico(Base):
    """Tabela-fato: guarda o planejado e o realizado."""

    __tablename__ = "servicos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    motorista_id: Mapped[int] = mapped_column(ForeignKey("motoristas.id"), nullable=False)
    carro_id: Mapped[int] = mapped_column(ForeignKey("carros.id"), nullable=False)
    data_servico: Mapped[date] = mapped_column(Date, nullable=False)
    hora_prevista: Mapped[time | None] = mapped_column(Time)
    horas_contratadas: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    inicio_real: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fim_real: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=STATUS_PLANEJADO)
    observacao: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cliente: Mapped[Cliente] = relationship(lazy="joined")
    motorista: Mapped[Motorista] = relationship(lazy="joined")
    carro: Mapped[Carro] = relationship(lazy="joined")


class ServicoLog(Base):
    __tablename__ = "servicos_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    servico_id: Mapped[int] = mapped_column(ForeignKey("servicos.id"), nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    acao: Mapped[str] = mapped_column(String(40), nullable=False)
    detalhe: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
