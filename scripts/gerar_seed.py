"""Gera o arquivo database/seed.sql com dados fictícios para demonstração.

Uso:
    python scripts/gerar_seed.py

Resultado esperado: arquivo database/seed.sql com 10 clientes, 5 motoristas,
3 carros e 120 serviços variados (dentro, acima, abaixo e não realizados).
Nenhum dado pessoal real é utilizado.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from pathlib import Path

random.seed(42)  # resultado reproduzível

SAIDA = Path(__file__).resolve().parents[1] / "database" / "seed.sql"

# Hash bcrypt da senha "senha123" (mesma para todos os usuários de demonstração).
# É calculado de verdade quando a biblioteca bcrypt está instalada
# (pip install -r requirements.txt). Sem ela, fica um marcador inválido.
SENHA_DEMO = "senha123"
try:
    import bcrypt

    SENHA_HASH = bcrypt.hashpw(SENHA_DEMO.encode(), bcrypt.gensalt()).decode()
except ImportError:  # pragma: no cover
    SENHA_HASH = "PRECISA_INSTALAR_BCRYPT_E_RODAR_DE_NOVO"
    print("AVISO: bcrypt não instalado - o hash de senha do seed é apenas um marcador.")


CLIENTES = [
    ("Supermercado Estrela", "11.111.111/0001-11", "Av. Central, 100"),
    ("Farmácia Bem-Estar", "22.222.222/0001-22", "Rua das Flores, 22"),
    ("Loja Mundo Kids", "33.333.333/0001-33", "Rua Onze, 340"),
    ("Auto Peças Trindade", "44.444.444/0001-44", "Rod. BR-101, km 12"),
    ("Padaria Pão Quente", "55.555.555/0001-55", "Rua Boa Vista, 8"),
    ("Ótica Visão Clara", "66.666.666/0001-66", "Av. Brasil, 512"),
    ("Restaurante Sabor Local", "77.777.777/0001-77", "Praça Matriz, 15"),
    ("Móveis Conforto", "88.888.888/0001-88", "Av. Industrial, 900"),
    ("Pet Shop Amigo Fiel", "99.999.999/0001-99", "Rua Verde, 61"),
    ("Academia Corpo Ativo", "10.101.010/0001-10", "Av. Litorânea, 77"),
]

MOTORISTAS = [
    ("Joao Silva", "joao@sonargest.com", "(88) 90000-0001", "12345678901"),
    ("Pedro Souza", "pedro@sonargest.com", "(88) 90000-0002", "12345678902"),
    ("Marcos Lima", "marcos@sonargest.com", "(88) 90000-0003", "12345678903"),
    ("Ana Ribeiro", "ana@sonargest.com", "(88) 90000-0004", "12345678904"),
    ("Carla Mendes", "carla@sonargest.com", "(88) 90000-0005", "12345678905"),
]

CARROS = [
    ("SOM-1A01", "Fiat Fiorino", "Carro 01 - som duplo"),
    ("SOM-2B02", "VW Saveiro", "Carro 02 - trio elétrico pequeno"),
    ("SOM-3C03", "Kombi Antiga", "Carro 03 - reserva"),
]

# Perfil de comportamento por motorista: (media_desvio_horas, dispersao)
PERFIL_MOTORISTA = {
    1: (0.05, 0.10),   # muito aderente
    2: (-0.30, 0.20),  # tende a encerrar antes
    3: (0.35, 0.25),   # tende a estender o serviço
    4: (0.02, 0.15),   # aderente
    5: (0.12, 0.30),   # irregular
}


def esc(texto: str) -> str:
    """Escapa aspas simples para uso seguro dentro do SQL."""
    return texto.replace("'", "''")


def gerar_servicos(quantidade: int = 120) -> list[str]:
    linhas: list[str] = []
    inicio_periodo = date(2026, 5, 1)

    for _ in range(quantidade):
        dia = inicio_periodo + timedelta(days=random.randint(0, 119))
        cliente_id = random.randint(1, len(CLIENTES))
        motorista_id = random.randint(1, len(MOTORISTAS))
        carro_id = random.randint(1, len(CARROS))
        horas = random.choice([2, 2.5, 3, 4, 4, 5, 6, 8])
        hora_inicio_prev = random.choice([7, 8, 9, 13, 14, 15])

        # 12% dos serviços continuam apenas planejados (ainda não executados)
        if random.random() < 0.12:
            linhas.append(
                f"({cliente_id}, {motorista_id}, {carro_id}, DATE '{dia}', "
                f"TIME '{hora_inicio_prev:02d}:00', {horas}, NULL, NULL, 'planejado', NULL)"
            )
            continue

        # 5% cancelados
        if random.random() < 0.05:
            linhas.append(
                f"({cliente_id}, {motorista_id}, {carro_id}, DATE '{dia}', "
                f"TIME '{hora_inicio_prev:02d}:00', {horas}, NULL, NULL, 'cancelado', "
                f"'Cancelado pelo cliente')"
            )
            continue

        media, dispersao = PERFIL_MOTORISTA[motorista_id]
        desvio = round(random.gauss(media, dispersao), 2)

        atraso_min = random.randint(-5, 20)
        inicio = datetime.combine(dia, datetime.min.time()).replace(
            hour=hora_inicio_prev
        ) + timedelta(minutes=atraso_min)
        fim = inicio + timedelta(hours=max(0.25, horas + desvio))

        linhas.append(
            f"({cliente_id}, {motorista_id}, {carro_id}, DATE '{dia}', "
            f"TIME '{hora_inicio_prev:02d}:00', {horas}, "
            f"TIMESTAMPTZ '{inicio:%Y-%m-%d %H:%M:00}-03', "
            f"TIMESTAMPTZ '{fim:%Y-%m-%d %H:%M:00}-03', 'finalizado', NULL)"
        )

    return linhas


def main() -> None:
    partes: list[str] = []
    partes.append(
        "-- ============================================================\n"
        "-- SonarGest - dados fictícios para demonstração\n"
        "-- ARQUIVO GERADO AUTOMATICAMENTE por scripts/gerar_seed.py\n"
        "-- Senha de todos os usuários de demonstração: senha123\n"
        "-- ============================================================\n\n"
        "TRUNCATE servicos_log, servicos, motoristas, carros, clientes, usuarios "
        "RESTART IDENTITY CASCADE;\n"
    )

    # Usuários: 1 admin + 1 por motorista
    partes.append("\n-- Usuários\nINSERT INTO usuarios (nome, email, senha_hash, perfil) VALUES")
    usuarios = [f"('Empresa SonarGest', 'admin@sonargest.com', '{SENHA_HASH}', 'admin')"]
    usuarios += [
        f"('{esc(nome)}', '{email}', '{SENHA_HASH}', 'motorista')"
        for nome, email, _, _ in MOTORISTAS
    ]
    partes.append("\n" + ",\n".join(usuarios) + ";\n")

    partes.append("\n-- Clientes\nINSERT INTO clientes (nome, documento, telefone, email, endereco) VALUES")
    clientes = [
        f"('{esc(nome)}', '{doc}', '(88) 3000-00{i:02d}', "
        f"'contato{i}@exemplo.com', '{esc(end)}')"

        for i, (nome, doc, end) in enumerate(CLIENTES, start=1)
    ]
    partes.append("\n" + ",\n".join(clientes) + ";\n")

    partes.append("\n-- Motoristas (usuario_id 2..6, pois o 1 é o admin)\n"
                  "INSERT INTO motoristas (usuario_id, nome, telefone, cnh) VALUES")
    motoristas = [
        f"({i + 1}, '{esc(nome)}', '{fone}', '{cnh}')"
        for i, (nome, _, fone, cnh) in enumerate(MOTORISTAS, start=1)
    ]
    partes.append("\n" + ",\n".join(motoristas) + ";\n")

    partes.append("\n-- Carros\nINSERT INTO carros (placa, modelo, descricao) VALUES")
    carros = [f"('{p}', '{esc(m)}', '{esc(d)}')" for p, m, d in CARROS]
    partes.append("\n" + ",\n".join(carros) + ";\n")

    partes.append(
        "\n-- Serviços\nINSERT INTO servicos (cliente_id, motorista_id, carro_id, data_servico, "
        "hora_prevista, horas_contratadas, inicio_real, fim_real, status, observacao) VALUES"
    )
    partes.append("\n" + ",\n".join(gerar_servicos()) + ";\n")

    SAIDA.write_text("".join(partes), encoding="utf-8")
    print(f"Arquivo gerado: {SAIDA}")


if __name__ == "__main__":
    main()
