"""Tela da empresa — planejamento e acompanhamento dos serviços.

Exclusiva do perfil ADMIN/EMPRESA: cadastra novos serviços, lista o
planejado × realizado e permite alterar ou cancelar.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from app import repositories as repo
from app.auth import barra_lateral, exigir_perfil
from app.db import sessao
from app.models import (
    PERFIL_ADMIN,
    STATUS_CANCELADO,
    STATUS_EM_ANDAMENTO,
    STATUS_FINALIZADO,
    STATUS_PLANEJADO,
)
from app.services import RegraDeNegocioError, alterar_servico, cancelar_servico, criar_servico
from app.ui import ROTULO_STATUS, opcoes, servicos_para_dataframe

st.set_page_config(page_title="Serviços · SonarGest", page_icon="📋", layout="wide")

usuario = exigir_perfil(PERFIL_ADMIN)
barra_lateral(usuario)

st.title("Serviços")
st.caption("Planejamento da empresa e comparação entre contratado e realizado.")

with sessao() as db:
    clientes = opcoes(repo.listar_clientes(db))
    motoristas = opcoes(repo.listar_motoristas(db))
    carros = opcoes(repo.listar_carros(db), rotulo=lambda c: f"{c.placa} — {c.modelo}")

if not (clientes and motoristas and carros):
    st.warning("Cadastre ao menos um cliente, um motorista e um carro antes de criar serviços.")
    st.page_link("pages/2_Empresa_Cadastros.py", label="Ir para Cadastros", icon="🗂️")
    st.stop()

# ------------------------------------------------------------ novo serviço
st.subheader("Novo serviço")
with st.form("novo_servico", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    data_servico = c1.date_input("Data", value=date.today(), format="DD/MM/YYYY")
    cliente = c2.selectbox("Cliente", list(clientes))
    motorista = c3.selectbox("Motorista", list(motoristas))

    c4, c5, c6 = st.columns(3)
    carro = c4.selectbox("Carro", list(carros))
    horas = c5.number_input("Horas contratadas", min_value=0.5, max_value=24.0, value=4.0, step=0.5)
    hora_prevista = c6.time_input("Horário previsto", value=None)

    observacao = st.text_area("Observação", placeholder="Bairro, roteiro, material de áudio...")
    enviado = st.form_submit_button("Cadastrar serviço", use_container_width=True)

if enviado:
    try:
        with sessao() as db:
            criar_servico(
                db,
                usuario,
                cliente_id=clientes[cliente],
                motorista_id=motoristas[motorista],
                carro_id=carros[carro],
                data_servico=data_servico,
                horas_contratadas=horas,
                hora_prevista=hora_prevista,
                observacao=observacao,
            )
    except RegraDeNegocioError as erro:
        st.error(str(erro))
    else:
        st.success("Serviço cadastrado.")

st.divider()

# --------------------------------------------------------------- filtros
st.subheader("Serviços cadastrados")
f1, f2, f3, f4 = st.columns(4)
inicio = f1.date_input("De", value=date.today() - timedelta(days=30), format="DD/MM/YYYY")
fim = f2.date_input("Até", value=date.today() + timedelta(days=30), format="DD/MM/YYYY")
filtro_cliente = f3.selectbox("Cliente", ["Todos", *clientes])
filtro_status = f4.selectbox(
    "Status",
    ["Todos", STATUS_PLANEJADO, STATUS_EM_ANDAMENTO, STATUS_FINALIZADO, STATUS_CANCELADO],
    format_func=lambda s: "Todos" if s == "Todos" else ROTULO_STATUS[s],
)

with sessao() as db:
    servicos = repo.listar_servicos(
        db,
        data_inicio=inicio,
        data_fim=fim,
        cliente_id=clientes.get(filtro_cliente),
        status=None if filtro_status == "Todos" else filtro_status,
    )
    tabela = servicos_para_dataframe(servicos)
    editaveis = {
        f"#{s.id} · {s.data_servico.strftime('%d/%m')} · {s.cliente.nome}": s.id
        for s in servicos
        if s.status in (STATUS_PLANEJADO, STATUS_EM_ANDAMENTO)
    }

if tabela.empty:
    st.info("Nenhum serviço no período selecionado.")
else:
    st.dataframe(tabela, use_container_width=True, hide_index=True)
    st.caption(f"{len(tabela)} serviço(s) no período.")

# ------------------------------------------------------- alterar / cancelar
if editaveis:
    st.divider()
    st.subheader("Alterar ou cancelar")
    escolhido = st.selectbox("Serviço", list(editaveis))
    servico_id = editaveis[escolhido]

    with sessao() as db:
        servico = repo.buscar_servico(db, servico_id)
        atual = {
            "cliente": servico.cliente.nome,
            "motorista": servico.motorista.nome,
            "carro": f"{servico.carro.placa} — {servico.carro.modelo}",
            "data": servico.data_servico,
            "horas": float(servico.horas_contratadas),
            "hora_prevista": servico.hora_prevista,
            "observacao": servico.observacao or "",
        }

    aba_alterar, aba_cancelar = st.tabs(["Alterar", "Cancelar"])

    with aba_alterar:
        with st.form("alterar_servico"):
            a1, a2, a3 = st.columns(3)
            nova_data = a1.date_input("Data", value=atual["data"], format="DD/MM/YYYY")
            novo_cliente = a2.selectbox(
                "Cliente", list(clientes), index=list(clientes).index(atual["cliente"])
            )
            novo_motorista = a3.selectbox(
                "Motorista", list(motoristas), index=list(motoristas).index(atual["motorista"])
            )
            a4, a5, a6 = st.columns(3)
            novo_carro = a4.selectbox(
                "Carro", list(carros), index=list(carros).index(atual["carro"])
            )
            novas_horas = a5.number_input(
                "Horas contratadas", min_value=0.5, max_value=24.0,
                value=atual["horas"], step=0.5,
            )
            nova_hora_prevista = a6.time_input("Horário previsto", value=atual["hora_prevista"])
            nova_obs = st.text_area("Observação", value=atual["observacao"])
            salvar = st.form_submit_button("Salvar alterações", use_container_width=True)

        if salvar:
            try:
                with sessao() as db:
                    alterar_servico(
                        db, usuario, servico_id,
                        cliente_id=clientes[novo_cliente],
                        motorista_id=motoristas[novo_motorista],
                        carro_id=carros[novo_carro],
                        data_servico=nova_data,
                        horas_contratadas=novas_horas,
                        hora_prevista=nova_hora_prevista,
                        observacao=nova_obs,
                    )
            except RegraDeNegocioError as erro:
                st.error(str(erro))
            else:
                st.success("Serviço atualizado.")
                st.rerun()

    with aba_cancelar:
        motivo = st.text_input("Motivo do cancelamento", key="motivo_cancelamento")
        if st.button("Cancelar serviço", type="primary"):
            try:
                with sessao() as db:
                    cancelar_servico(db, usuario, servico_id, motivo)
            except RegraDeNegocioError as erro:
                st.error(str(erro))
            else:
                st.success("Serviço cancelado.")
                st.rerun()
