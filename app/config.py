"""Configuração central da aplicação.

Lê as variáveis de ambiente do arquivo .env (execução local) ou dos *secrets*
do Streamlit Community Cloud (execução publicada). Nenhuma credencial fica no
código.
"""

from __future__ import annotations

import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


class ConfiguracaoAusente(RuntimeError):
    """Erro lançado quando uma variável de ambiente obrigatória não existe."""


def _do_streamlit(nome: str) -> str | None:
    """Busca o valor nos secrets do Streamlit, se a aplicação estiver rodando nele."""
    try:
        import streamlit as st

        return st.secrets.get(nome)  # type: ignore[no-any-return]
    except Exception:
        return None


def _ler(nome: str) -> str | None:
    return os.getenv(nome) or _do_streamlit(nome)


def _obrigatoria(nome: str) -> str:
    valor = _ler(nome)
    if not valor:
        raise ConfiguracaoAusente(
            f"A variável de ambiente {nome} não está definida. "
            "Localmente: copie .env.example para .env e preencha os valores. "
            "No Streamlit Cloud: cadastre em Settings -> Secrets."
        )
    return valor


DATABASE_URL: str = _obrigatoria("DATABASE_URL")
APP_SECRET_KEY: str = _obrigatoria("APP_SECRET_KEY")

# A empresa opera no horário de Brasília. O banco guarda TIMESTAMPTZ (UTC);
# a exibição e o registro de horários usam este fuso.
FUSO = ZoneInfo(_ler("TIMEZONE") or "America/Sao_Paulo")


# Tolerância, em horas, para considerar um serviço "dentro do contratado" (5 min).
TOLERANCIA_HORAS = 5 / 60
