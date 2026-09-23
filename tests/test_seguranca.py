"""Testes do hash de senha (app/security.py)."""

from __future__ import annotations

import pytest

from app.security import conferir_senha, gerar_hash


def test_hash_nunca_guarda_a_senha_em_texto_puro():
    hash_gerado = gerar_hash("senha123")
    assert "senha123" not in hash_gerado
    assert hash_gerado.startswith("$2")


def test_hashes_diferentes_para_a_mesma_senha():
    assert gerar_hash("senha123") != gerar_hash("senha123")


def test_confere_senha_correta_e_recusa_a_errada():
    hash_gerado = gerar_hash("senha123")
    assert conferir_senha("senha123", hash_gerado) is True
    assert conferir_senha("senha124", hash_gerado) is False


def test_hash_invalido_nao_quebra_a_aplicacao():
    assert conferir_senha("senha123", "não é um hash") is False


def test_senha_curta_e_recusada():
    with pytest.raises(ValueError):
        gerar_hash("123")
