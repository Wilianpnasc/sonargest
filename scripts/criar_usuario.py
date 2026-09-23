"""Cria (ou atualiza a senha de) um usuário do SonarGest.

A senha nunca é digitada no código nem gravada em texto puro: o script pede
a senha no terminal e grava apenas o hash bcrypt.

Uso:
    python -m scripts.criar_usuario --nome "Empresa" --email admin@sonargest.com --perfil admin
    python -m scripts.criar_usuario --nome "João" --email joao@sonargest.com \
        --perfil motorista --motorista-id 1
"""

from __future__ import annotations

import argparse
import getpass
import sys

from app.db import sessao
from app.models import PERFIL_ADMIN, PERFIL_MOTORISTA, Motorista, Usuario
from app.security import gerar_hash


def main() -> int:
    parser = argparse.ArgumentParser(description="Cria um usuário do SonarGest.")
    parser.add_argument("--nome", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--perfil", required=True, choices=[PERFIL_ADMIN, PERFIL_MOTORISTA])
    parser.add_argument(
        "--motorista-id",
        type=int,
        help="Obrigatório para o perfil motorista: id na tabela motoristas.",
    )
    args = parser.parse_args()

    email = args.email.strip().lower()

    if args.perfil == PERFIL_MOTORISTA and not args.motorista_id:
        print("Para o perfil motorista informe --motorista-id.")
        return 1

    senha = getpass.getpass("Senha (mínimo 6 caracteres): ")
    if senha != getpass.getpass("Repita a senha: "):
        print("As senhas não conferem.")
        return 1

    try:
        senha_hash = gerar_hash(senha)
    except ValueError as erro:
        print(erro)
        return 1

    with sessao() as db:
        usuario = db.query(Usuario).filter(Usuario.email == email).one_or_none()
        if usuario is None:
            usuario = Usuario(nome=args.nome, email=email, perfil=args.perfil, ativo=True)
            db.add(usuario)
            acao = "criado"
        else:
            usuario.nome = args.nome
            usuario.perfil = args.perfil
            usuario.ativo = True
            acao = "atualizado"
        usuario.senha_hash = senha_hash
        db.flush()

        if args.perfil == PERFIL_MOTORISTA:
            motorista = db.get(Motorista, args.motorista_id)
            if motorista is None:
                print(f"Motorista {args.motorista_id} não encontrado.")
                return 1
            motorista.usuario_id = usuario.id

    print(f"Usuário {email} {acao} com sucesso (perfil {args.perfil}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
