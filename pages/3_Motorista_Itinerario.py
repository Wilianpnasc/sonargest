"""Tela do motorista — itinerário do dia e registro dos horários reais.

Pensada para o celular: uma coluna, textos grandes e apenas dois botões
por serviço (INICIAR e FINALIZAR). O motorista vê somente os serviços
atribuídos a ele; a garantia disso está em services.itinerario_do_dia.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from app.auth import barra_lateral, exigir_perfil
from app.calculos import formatar_horas, horas_realizadas
from app.db import sessao
from app.models import PERFIL_MOTORISTA, STATUS_CANCELADO, STATUS_FINALIZADO
from app.services import (
    RegraDeNegocioError,
    finalizar_servico,
    iniciar_servico,
    itinerario_do_dia,
)
from app.ui import ROTULO_STATUS, hora_local

st.set_page_config(page_title="Meu dia · SonarGest", page_icon="🚚", layout="centered")

usuario = exigir_perfil(PERFIL_MOTORISTA)
barra_lateral(usuario)

st.title("Meu dia")
dia = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")


def _acao(funcao, servico_id: int, mensagem: str) -> None:
    """Executa iniciar/finalizar e mostra o resultado na tela."""
    try:
        with sessao() as db:
            funcao(db, usuario, servico_id)
    except RegraDeNegocioError as erro:
        st.error(str(erro))
    else:
        st.success(mensagem)
        st.rerun()


try:
    with sessao() as db:
        servicos = itinerario_do_dia(db, usuario, dia)
        cartoes = [
            {
                "id": s.id,
                "cliente": s.cliente.nome,
                "carro": f"{s.carro.placa} — {s.carro.modelo}",
                "previsto": s.hora_prevista.strftime("%H:%M") if s.hora_prevista else "--",
                "contratadas": float(s.horas_contratadas),
                "inicio": hora_local(s.inicio_real),
                "fim": hora_local(s.fim_real),
                "realizadas": horas_realizadas(s.inicio_real, s.fim_real),
                "status": s.status,
                "observacao": s.observacao,
                "iniciado": s.inicio_real is not None,
                "encerrado": s.status in (STATUS_FINALIZADO, STATUS_CANCELADO),
            }
            for s in servicos
        ]
except RegraDeNegocioError as erro:
    st.error(str(erro))
    st.stop()

if not cartoes:
    st.info("Nenhum serviço atribuído a você nesta data.")
    st.stop()

st.caption(f"{len(cartoes)} serviço(s) para {dia.strftime('%d/%m/%Y')}.")

for c in cartoes:
    with st.container(border=True):
        st.subheader(c["cliente"])
        st.write(
            f"**Carro:** {c['carro']}  \n"
            f"**Horário previsto:** {c['previsto']}  \n"
            f"**Horas contratadas:** {formatar_horas(c['contratadas'])}"
        )
        if c["observacao"]:
            st.caption(c["observacao"])

        st.write(
            f"Início: **{c['inicio']}** · Término: **{c['fim']}** · "
            f"Realizado: **{formatar_horas(c['realizadas'])}**"
        )
        st.write(f"Situação: **{ROTULO_STATUS.get(c['status'], c['status'])}**")

        if c["status"] == STATUS_CANCELADO:
            st.warning("Serviço cancelado pela empresa.")
        elif c["status"] == STATUS_FINALIZADO:
            diferenca = (c["realizadas"] or 0) - c["contratadas"]
            st.success(f"Concluído. Diferença: {formatar_horas(diferenca)}")
        else:
            col_inicio, col_fim = st.columns(2)
            col_inicio.button(
                "INICIAR",
                key=f"iniciar_{c['id']}",
                use_container_width=True,
                disabled=c["iniciado"],
                on_click=_acao,
                args=(iniciar_servico, c["id"], "Início registrado."),
            )
            col_fim.button(
                "FINALIZAR",
                key=f"finalizar_{c['id']}",
                type="primary",
                use_container_width=True,
                disabled=not c["iniciado"],  # não finaliza sem ter iniciado
                on_click=_acao,
                args=(finalizar_servico, c["id"], "Término registrado."),
            )
