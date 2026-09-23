"""Conexão com o banco PostgreSQL.

Cria um único engine (pool de conexões) reaproveitado por toda a aplicação e
oferece um gerenciador de contexto para abrir/fechar sessões com segurança.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # descarta conexões mortas (comum em banco na nuvem)
    pool_recycle=1800,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


@contextmanager
def sessao() -> Iterator[Session]:
    """Abre uma sessão, confirma no sucesso e desfaz no erro."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def consultar_df(sql: str, parametros: dict | None = None) -> pd.DataFrame:
    """Executa uma consulta parametrizada e devolve um DataFrame do pandas.

    Usado pela camada de análise e pelo dashboard. Sempre com parâmetros
    nomeados (:nome), nunca concatenando strings — evita SQL injection.
    """
    with engine.connect() as conexao:
        return pd.read_sql(text(sql), conexao, params=parametros or {})
