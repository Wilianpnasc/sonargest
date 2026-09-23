"""Tela do motorista — histórico dos próprios serviços.

Somente leitura: o motorista acompanha o que já executou e como ficou o
comparativo entre contratado e realizado. Ele não altera dado administrativo.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from app import repositories as repo
from app.auth import barra_lateral, exigir_perfil
from app.calculos import formatar_horas
from app.db import sessao
from app.models import PERFIL_MOTORISTA
from app.ui import servicos_para_dataframe

st.set_page_config(page_title="Histórico · SonarGest", page_icon="📆", layout="wide")

usuario = exigir_perfil(PERFIL_MOTORISTA)
barra_lateral(usuario)

st.title("Meu histórico")

if usuario.motorista_id is None:
    st.error("Este usuário não está vinculado a um motorista.")
    st.stop()

c1, c2 = st.columns(2)
inicio = c1.date_input("De", value=date.today() - timedelta(days=30), format="DD/MM/YYYY")
fim = c2.date_input("Até", value=date.today(), format="DD/MM/YYYY")

with sessao() as db:
    # O filtro por motorista_id do usuário logado é o que garante que ele
    # nunca enxergue o serviço de outro motorista.
    servicos = repo.listar_servicos(
        db, data_inicio=inicio, data_fim=fim, motorista_id=usuario.motorista_id
    )
    tabela = servicos_para_dataframe(servicos)

if tabela.empty:
    st.info("Nenhum serviço no período selecionado.")
    st.stop()

contratadas = sum(float(s.horas_contratadas) for s in servicos)
realizadas = sum(
    (s.fim_real - s.inicio_real).total_seconds() / 3600
    for s in servicos
    if s.inicio_real and s.fim_real
)

m1, m2, m3 = st.columns(3)
m1.metric("Serviços", len(servicos))
m2.metric("Horas contratadas", formatar_horas(contratadas))
m3.metric("Horas realizadas", formatar_horas(realizadas), formatar_horas(realizadas - contratadas))

st.dataframe(
    tabela.drop(columns=["Motorista"]), use_container_width=True, hide_index=True
)
