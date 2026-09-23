"""Regras de negócio do SonarGest.

Toda validação importante fica aqui, e não nas telas. Assim as mesmas regras
valem para a tela da empresa, a tela do motorista e os testes automatizados.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from sqlalchemy.orm import Session

from app import repositories as repo
from app.calculos import horas_realizadas
from app.config import FUSO
from app.models import (
    PERFIL_ADMIN,
    PERFIL_MOTORISTA,
    Carro,
    Cliente,
    Motorista,
    STATUS_CANCELADO,
    STATUS_EM_ANDAMENTO,
    STATUS_FINALIZADO,
    STATUS_PLANEJADO,
    Servico,
    Usuario,
)
from app.security import conferir_senha, gerar_hash


class RegraDeNegocioError(Exception):
    """Erro previsto de regra de negócio, exibido ao usuário na tela."""


# ------------------------------------------------------------------ sessão
@dataclass(frozen=True)
class UsuarioLogado:
    """Dados mínimos guardados na sessão. A senha nunca circula."""

    id: int
    nome: str
    email: str
    perfil: str
    motorista_id: int | None

    @property
    def eh_admin(self) -> bool:
        return self.perfil == PERFIL_ADMIN


def autenticar(db: Session, email: str, senha: str) -> UsuarioLogado:
    """Valida e-mail e senha e devolve os dados de sessão."""
    usuario: Usuario | None = repo.buscar_usuario_por_email(db, email)
    # Mensagem genérica de propósito: não revela se o e-mail existe.
    if usuario is None or not conferir_senha(senha, usuario.senha_hash):
        raise RegraDeNegocioError("E-mail ou senha inválidos.")
    if not usuario.ativo:
        raise RegraDeNegocioError("Usuário inativo. Procure a empresa.")

    motorista = repo.buscar_motorista_por_usuario(db, usuario.id)
    return UsuarioLogado(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        perfil=usuario.perfil,
        motorista_id=motorista.id if motorista else None,
    )


def exigir_admin(usuario: UsuarioLogado) -> None:
    """Autorização por perfil: bloqueia o motorista em áreas administrativas."""
    if not usuario.eh_admin:
        raise RegraDeNegocioError("Acesso permitido apenas ao perfil da empresa.")


# ---------------------------------------------------------------- serviços
def criar_servico(
    db: Session,
    usuario: UsuarioLogado,
    cliente_id: int | None,
    motorista_id: int | None,
    carro_id: int | None,
    data_servico: date | None,
    horas_contratadas: float | None,
    hora_prevista: time | None = None,
    observacao: str | None = None,
) -> Servico:
    """Cria um serviço planejado após validar todos os campos obrigatórios."""
    exigir_admin(usuario)

    if not cliente_id:
        raise RegraDeNegocioError("Selecione o cliente.")
    if not motorista_id:
        raise RegraDeNegocioError("Selecione o motorista.")
    if not carro_id:
        raise RegraDeNegocioError("Selecione o carro.")
    if not data_servico:
        raise RegraDeNegocioError("Informe a data do serviço.")
    if horas_contratadas is None or float(horas_contratadas) <= 0:
        raise RegraDeNegocioError("As horas contratadas devem ser maiores que zero.")

    servico = Servico(
        cliente_id=cliente_id,
        motorista_id=motorista_id,
        carro_id=carro_id,
        data_servico=data_servico,
        hora_prevista=hora_prevista,
        horas_contratadas=float(horas_contratadas),
        status=STATUS_PLANEJADO,
        observacao=(observacao or "").strip() or None,
    )
    repo.salvar(db, servico)
    repo.registrar_log(db, servico.id, usuario.id, "criado")
    return servico


def alterar_servico(
    db: Session,
    usuario: UsuarioLogado,
    servico_id: int,
    cliente_id: int,
    motorista_id: int,
    carro_id: int,
    data_servico: date,
    horas_contratadas: float,
    hora_prevista: time | None = None,
    observacao: str | None = None,
) -> Servico:
    """Altera o planejamento de um serviço que ainda não foi finalizado."""
    exigir_admin(usuario)
    servico = _obter(db, servico_id)

    if servico.status == STATUS_FINALIZADO:
        raise RegraDeNegocioError("Um serviço finalizado não pode ser alterado.")
    if servico.status == STATUS_CANCELADO:
        raise RegraDeNegocioError("Um serviço cancelado não pode ser alterado.")
    if horas_contratadas is None or float(horas_contratadas) <= 0:
        raise RegraDeNegocioError("As horas contratadas devem ser maiores que zero.")
    if not (cliente_id and motorista_id and carro_id and data_servico):
        raise RegraDeNegocioError("Cliente, motorista, carro e data são obrigatórios.")

    servico.cliente_id = cliente_id
    servico.motorista_id = motorista_id
    servico.carro_id = carro_id
    servico.data_servico = data_servico
    servico.horas_contratadas = float(horas_contratadas)
    servico.hora_prevista = hora_prevista
    servico.observacao = (observacao or "").strip() or None
    repo.registrar_log(db, servico.id, usuario.id, "alterado")
    return servico


# --------------------------------------------------------------- cadastros
def criar_cliente(
    db: Session,
    usuario: UsuarioLogado,
    nome: str,
    contato: str | None = None,
    telefone: str | None = None,
    email: str | None = None,
) -> Cliente:
    exigir_admin(usuario)
    if not (nome or "").strip():
        raise RegraDeNegocioError("Informe o nome do cliente.")
    cliente = Cliente(
        nome=nome.strip(),
        documento=(contato or "").strip() or None,
        telefone=(telefone or "").strip() or None,
        email=(email or "").strip().lower() or None,
    )
    repo.salvar(db, cliente)
    return cliente


def criar_carro(
    db: Session,
    usuario: UsuarioLogado,
    placa: str,
    modelo: str,
    descricao: str | None = None,
) -> Carro:
    exigir_admin(usuario)
    if not (placa or "").strip() or not (modelo or "").strip():
        raise RegraDeNegocioError("Informe a placa e o modelo do carro.")
    carro = Carro(
        placa=placa.strip().upper(),
        modelo=modelo.strip(),
        descricao=(descricao or "").strip() or None,
    )
    repo.salvar(db, carro)
    return carro


def criar_motorista(
    db: Session,
    usuario: UsuarioLogado,
    nome: str,
    email: str,
    senha: str,
    telefone: str | None = None,
    cnh: str | None = None,
) -> Motorista:
    """Cria o motorista e o usuário de acesso dele (senha guardada em hash)."""
    exigir_admin(usuario)
    if not (nome or "").strip():
        raise RegraDeNegocioError("Informe o nome do motorista.")
    email = (email or "").strip().lower()
    if "@" not in email:
        raise RegraDeNegocioError("Informe um e-mail válido para o acesso do motorista.")
    if repo.buscar_usuario_por_email(db, email) is not None:
        raise RegraDeNegocioError("Já existe um usuário com este e-mail.")
    try:
        senha_hash = gerar_hash(senha or "")
    except ValueError as erro:
        raise RegraDeNegocioError(str(erro)) from erro

    acesso = Usuario(
        nome=nome.strip(),
        email=email,
        senha_hash=senha_hash,
        perfil=PERFIL_MOTORISTA,
        ativo=True,
    )
    repo.salvar(db, acesso)
    motorista = Motorista(
        usuario_id=acesso.id,
        nome=nome.strip(),
        telefone=(telefone or "").strip() or None,
        cnh=(cnh or "").strip() or None,
    )
    repo.salvar(db, motorista)
    return motorista


def alternar_ativo(db: Session, usuario: UsuarioLogado, registro) -> None:
    """Desativa/reativa um cadastro. Não excluímos: o histórico precisa dele."""
    exigir_admin(usuario)
    registro.ativo = not registro.ativo
    repo.salvar(db, registro)



def cancelar_servico(db: Session, usuario: UsuarioLogado, servico_id: int, motivo: str) -> Servico:
    exigir_admin(usuario)
    servico = _obter(db, servico_id)
    if servico.status == STATUS_FINALIZADO:
        raise RegraDeNegocioError("Um serviço finalizado não pode ser cancelado.")
    servico.status = STATUS_CANCELADO
    servico.observacao = motivo.strip() or servico.observacao
    repo.registrar_log(db, servico.id, usuario.id, "cancelado", motivo)
    return servico


def iniciar_servico(
    db: Session, usuario: UsuarioLogado, servico_id: int, momento: datetime | None = None
) -> Servico:
    """Registra o horário real de início. Executado pelo motorista, no celular."""
    servico = _obter(db, servico_id)
    _exigir_dono(usuario, servico)

    if servico.status == STATUS_CANCELADO:
        raise RegraDeNegocioError("Este serviço foi cancelado e não pode ser iniciado.")
    if servico.status == STATUS_FINALIZADO:
        raise RegraDeNegocioError("Este serviço já foi finalizado.")
    if servico.inicio_real is not None:
        raise RegraDeNegocioError("Este serviço já foi iniciado.")

    servico.inicio_real = momento or agora()
    servico.status = STATUS_EM_ANDAMENTO
    repo.registrar_log(db, servico.id, usuario.id, "iniciado")
    return servico


def finalizar_servico(
    db: Session, usuario: UsuarioLogado, servico_id: int, momento: datetime | None = None
) -> Servico:
    """Registra o horário real de término e fecha o serviço."""
    servico = _obter(db, servico_id)
    _exigir_dono(usuario, servico)

    if servico.status == STATUS_CANCELADO:
        raise RegraDeNegocioError("Este serviço foi cancelado.")
    if servico.inicio_real is None:
        raise RegraDeNegocioError("Registre o início antes de finalizar o serviço.")
    if servico.fim_real is not None:
        raise RegraDeNegocioError("Este serviço já foi finalizado.")

    fim = momento or agora()
    if fim <= servico.inicio_real:
        raise RegraDeNegocioError("O término não pode ser anterior ao início.")

    servico.fim_real = fim
    servico.status = STATUS_FINALIZADO
    realizado = horas_realizadas(servico.inicio_real, fim)
    repo.registrar_log(db, servico.id, usuario.id, "finalizado", f"{realizado} h realizadas")
    return servico


def itinerario_do_dia(db: Session, usuario: UsuarioLogado, dia: date) -> list[Servico]:
    """Serviços do motorista logado na data escolhida — e somente dele."""
    if usuario.motorista_id is None:
        raise RegraDeNegocioError("Este usuário não está vinculado a um motorista.")
    return repo.listar_servicos_do_motorista_no_dia(db, usuario.motorista_id, dia)


# ----------------------------------------------------------------- apoio
def agora() -> datetime:
    """Horário atual no fuso de operação da empresa (Brasília)."""
    return datetime.now(FUSO)


def _obter(db: Session, servico_id: int) -> Servico:
    servico = repo.buscar_servico(db, servico_id)
    if servico is None:
        raise RegraDeNegocioError("Serviço não encontrado.")
    return servico


def _exigir_dono(usuario: UsuarioLogado, servico: Servico) -> None:
    """O motorista só pode agir sobre os serviços atribuídos a ele."""
    if usuario.eh_admin:
        return
    if usuario.motorista_id != servico.motorista_id:
        raise RegraDeNegocioError("Este serviço não está atribuído a você.")
