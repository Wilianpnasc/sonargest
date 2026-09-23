"""Página inicial do SonarGest — login e roteamento por perfil.

Execute com:  streamlit run Home.py
"""

from __future__ import annotations

import streamlit as st

from app.auth import ROTULO_PERFIL, barra_lateral, formulario_login, usuario_atual
from app.models import PERFIL_ADMIN

st.set_page_config(
    page_title="SonarGest",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="auto",
)

st.title("SonarGest")
st.caption("Gestão de serviços de carro de som — planejado × realizado")

usuario = usuario_atual()

if usuario is None:
    st.subheader("Acesso ao sistema")
    formulario_login()
    st.info(
        "Empresa e motorista usam a mesma tela de login. "
        "O sistema abre a área correta conforme o seu perfil."
    )
else:
    barra_lateral(usuario)
    st.success(
        f"Bem-vindo(a), {usuario.nome} "
        f"({ROTULO_PERFIL.get(usuario.perfil, usuario.perfil)})."
    )
    if usuario.perfil == PERFIL_ADMIN:
        st.write(
            "Use o menu lateral para planejar serviços, acompanhar a execução "
            "e abrir o painel de indicadores."
        )
    else:
        st.write(
            "Use o menu lateral para ver o seu itinerário do dia e registrar "
            "os horários de início e término."
        )
    st.caption("As telas de empresa e motorista são construídas nas próximas etapas.")
