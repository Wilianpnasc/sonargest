"""Configuração comum dos testes.

Os testes não usam o PostgreSQL de produção: montam um banco SQLite em
memória a partir do próprio ORM. Assim as regras de negócio são testadas
de ponta a ponta, mas sem depender de rede nem de credenciais.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# As variáveis obrigatórias precisam existir ANTES de importar app.config.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("APP_SECRET_KEY", "chave-de-teste")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.models import (  # noqa: E402
    PERFIL_ADMIN,
    PERFIL_MOTORISTA,
    Base,
    Carro,
    Cliente,
    Motorista,
    Usuario,
)
from app.services import UsuarioLogado  # noqa: E402


@pytest.fixture()
def db():
    """Banco limpo para cada teste (SQLite em memória)."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    sessao = Session()
    try:
        yield sessao
        sessao.rollback()
    finally:
        sessao.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def base_minima(db):
    """Um cliente, um carro e dois motoristas com seus usuários de acesso."""
    cliente = Cliente(nome="Supermercado Central")
    carro = Carro(placa="ABC1D23", modelo="Fiorino Som")
    admin = Usuario(
        nome="Empresa", email="admin@sonargest.com", senha_hash="x", perfil=PERFIL_ADMIN
    )
    u1 = Usuario(nome="João", email="joao@sonargest.com", senha_hash="x", perfil=PERFIL_MOTORISTA)
    u2 = Usuario(nome="Maria", email="maria@sonargest.com", senha_hash="x", perfil=PERFIL_MOTORISTA)
    db.add_all([cliente, carro, admin, u1, u2])
    db.flush()

    m1 = Motorista(usuario_id=u1.id, nome="João")
    m2 = Motorista(usuario_id=u2.id, nome="Maria")
    db.add_all([m1, m2])
    db.flush()

    return {
        "cliente": cliente,
        "carro": carro,
        "motorista": m1,
        "outro_motorista": m2,
        "admin": UsuarioLogado(
            id=admin.id,
            nome=admin.nome,
            email=admin.email,
            perfil=PERFIL_ADMIN,
            motorista_id=None,
        ),
        "joao": UsuarioLogado(
            id=u1.id, nome=u1.nome, email=u1.email, perfil=PERFIL_MOTORISTA, motorista_id=m1.id
        ),
        "maria": UsuarioLogado(
            id=u2.id, nome=u2.nome, email=u2.email, perfil=PERFIL_MOTORISTA, motorista_id=m2.id
        ),
    }
