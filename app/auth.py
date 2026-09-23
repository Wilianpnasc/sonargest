"""Autenticação e sessão na camada de apresentação (Streamlit).

Este módulo é a ponte entre a tela e as regras de `services.autenticar`.
Ele guarda o usuário logado em `st.session_state`, que é a sessão do
Streamlit: existe por aba do navegador e some quando o usuário sai.

Nada de senha é guardado na sessão — apenas id, nome, e-mail, perfil e o
vínculo com o motorista.
"""

from __future__ import annotations

import streamlit as st

from app.db import sessao
from app.models import PERFIL_ADMIN, PERFIL_MOTORISTA
from app.services import RegraDeNegocioError, UsuarioLogado, autenticar

CHAVE_SESSAO = "usuario_logado"

ROTULO_PERFIL = {
    PERFIL_ADMIN: "Empresa",
    PERFIL_MOTORISTA: "Motorista",
}


def usuario_atual() -> UsuarioLogado | None:
    """Devolve o usuário da sessão, ou None se ninguém estiver logado."""
    return st.session_state.get(CHAVE_SESSAO)


def entrar(email: str, senha: str) -> UsuarioLogado:
    """Valida as credenciais no banco e abre a sessão."""
    with sessao() as db:
        usuario = autenticar(db, email.strip().lower(), senha)
    st.session_state[CHAVE_SESSAO] = usuario
    return usuario


def sair() -> None:
    """Encerra a sessão e volta para a tela de login."""
    st.session_state.pop(CHAVE_SESSAO, None)
    st.rerun()


def exigir_login() -> UsuarioLogado:
    """Protege uma página: sem sessão, nada é renderizado.

    Chamada na primeira linha de cada página. Como o Streamlit executa o
    script de cima para baixo, o `st.stop()` impede que o conteúdo
    protegido chegue a ser desenhado.
    """
    usuario = usuario_atual()
    if usuario is None:
        st.warning("Faça login para acessar esta página.")
        st.page_link("Home.py", label="Ir para o login", icon="🔑")
        st.stop()
    return usuario


def exigir_perfil(perfil: str) -> UsuarioLogado:
    """Autorização por perfil: bloqueia quem está logado mas não pode entrar."""
    usuario = exigir_login()
    if usuario.perfil != perfil:
        st.error(
            "Você não tem permissão para acessar esta área "
            f"(exclusiva do perfil {ROTULO_PERFIL.get(perfil, perfil)})."
        )
        st.stop()
    return usuario


def barra_lateral(usuario: UsuarioLogado) -> None:
    """Identificação do usuário e botão de sair, iguais em todas as páginas."""
    with st.sidebar:
        st.markdown(f"**{usuario.nome}**")
        st.caption(f"{ROTULO_PERFIL.get(usuario.perfil, usuario.perfil)} · {usuario.email}")
        if st.button("Sair", use_container_width=True):
            sair()


def formulario_login() -> None:
    """Formulário de e-mail e senha exibido quando não há sessão."""
    with st.form("login"):
        email = st.text_input("E-mail", placeholder="voce@empresa.com.br")
        senha = st.text_input("Senha", type="password")
        enviado = st.form_submit_button("Entrar", use_container_width=True)

    if not enviado:
        return

    if not email or not senha:
        st.error("Informe e-mail e senha.")
        return

    try:
        entrar(email, senha)
    except RegraDeNegocioError as erro:
        st.error(str(erro))
    except Exception:  # falha de conexão, configuração ausente etc.
        st.error("Não foi possível acessar o banco de dados. Confira o arquivo .env.")
    else:
        st.rerun()
