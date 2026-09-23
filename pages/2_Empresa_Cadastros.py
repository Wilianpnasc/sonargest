"""Tela da empresa — cadastros de clientes, motoristas e carros."""

from __future__ import annotations

import streamlit as st

from app import repositories as repo
from app.auth import barra_lateral, exigir_perfil
from app.db import sessao
from app.models import PERFIL_ADMIN, Carro
from app.services import (
    RegraDeNegocioError,
    alternar_ativo,
    criar_carro,
    criar_cliente,
    criar_motorista,
)

st.set_page_config(page_title="Cadastros · SonarGest", page_icon="🗂️", layout="wide")

usuario = exigir_perfil(PERFIL_ADMIN)
barra_lateral(usuario)

st.title("Cadastros")
st.caption("Clientes, motoristas e carros usados no planejamento dos serviços.")


def _mensagem(execucao) -> None:
    """Executa a operação e traduz o erro de regra de negócio para a tela."""
    try:
        with sessao() as db:
            execucao(db)
    except RegraDeNegocioError as erro:
        st.error(str(erro))
    except Exception:
        st.error("Não foi possível concluir. Verifique se os dados já existem no sistema.")
    else:
        st.success("Cadastro salvo.")
        st.rerun()


aba_clientes, aba_motoristas, aba_carros = st.tabs(["Clientes", "Motoristas", "Carros"])

# ------------------------------------------------------------------ clientes
with aba_clientes:
    with st.form("novo_cliente", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome / razão social")
        contato = c2.text_input("Contato")
        c3, c4 = st.columns(2)
        telefone = c3.text_input("Telefone")
        email = c4.text_input("E-mail")
        if st.form_submit_button("Cadastrar cliente", use_container_width=True):
            _mensagem(lambda db: criar_cliente(db, usuario, nome, contato, telefone, email))

    with sessao() as db:
        clientes = [
            {"ID": c.id, "Nome": c.nome, "Contato": c.contato or "--",
             "Telefone": c.telefone or "--", "Ativo": "Sim" if c.ativo else "Não"}
            for c in repo.listar_clientes(db, apenas_ativos=False)
        ]
    st.dataframe(clientes, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------- motoristas
with aba_motoristas:
    st.caption("Ao cadastrar o motorista, o acesso dele ao sistema é criado junto.")
    with st.form("novo_motorista", clear_on_submit=True):
        m1, m2 = st.columns(2)
        nome_m = m1.text_input("Nome do motorista")
        email_m = m2.text_input("E-mail de acesso")
        m3, m4, m5 = st.columns(3)
        telefone_m = m3.text_input("Telefone")
        cnh = m4.text_input("CNH")
        senha = m5.text_input("Senha inicial", type="password")
        if st.form_submit_button("Cadastrar motorista", use_container_width=True):
            _mensagem(
                lambda db: criar_motorista(db, usuario, nome_m, email_m, senha, telefone_m, cnh)
            )

    with sessao() as db:
        motoristas = [
            {"ID": m.id, "Nome": m.nome, "Telefone": m.telefone or "--",
             "CNH": m.cnh or "--", "Ativo": "Sim" if m.ativo else "Não"}
            for m in repo.listar_motoristas(db, apenas_ativos=False)
        ]
    st.dataframe(motoristas, use_container_width=True, hide_index=True)

# -------------------------------------------------------------------- carros
with aba_carros:
    with st.form("novo_carro", clear_on_submit=True):
        k1, k2 = st.columns(2)
        placa = k1.text_input("Placa")
        modelo = k2.text_input("Modelo")
        descricao = st.text_input("Descrição", placeholder="Equipamento de som, potência...")
        if st.form_submit_button("Cadastrar carro", use_container_width=True):
            _mensagem(lambda db: criar_carro(db, usuario, placa, modelo, descricao))

    with sessao() as db:
        carros_lista = repo.listar_carros(db, apenas_ativos=False)
        carros = [
            {"ID": c.id, "Placa": c.placa, "Modelo": c.modelo,
             "Descrição": c.descricao or "--", "Ativo": "Sim" if c.ativo else "Não"}
            for c in carros_lista
        ]
        rotulos = {f"{c.placa} — {c.modelo}": c.id for c in carros_lista}
    st.dataframe(carros, use_container_width=True, hide_index=True)

    if rotulos:
        escolhido = st.selectbox("Ativar / desativar carro", list(rotulos))
        if st.button("Alternar situação"):
            def _alternar(db):
                carro = db.get(Carro, rotulos[escolhido])
                alternar_ativo(db, usuario, carro)

            _mensagem(_alternar)
