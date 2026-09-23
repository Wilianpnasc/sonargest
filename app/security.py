"""Segurança de senhas.

A senha do usuário nunca é armazenada. Guardamos apenas o hash bcrypt, que é
uma via de mão única: dá para conferir se a senha bate, mas não dá para
recuperar a senha original a partir do hash.
"""

from __future__ import annotations

import bcrypt


def gerar_hash(senha: str) -> str:
    """Transforma a senha em hash bcrypt (com salt aleatório embutido)."""
    if not senha or len(senha) < 6:
        raise ValueError("A senha deve ter pelo menos 6 caracteres.")
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def conferir_senha(senha: str, senha_hash: str) -> bool:
    """Confere se a senha digitada corresponde ao hash guardado."""
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False
