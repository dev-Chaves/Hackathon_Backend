import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import StatusFuncionario, TipoAusencia, TipoTransporte


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Area(TimestampMixin, Base):
    __tablename__ = "areas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    descricao: Mapped[str | None] = mapped_column(Text)

    funcionarios: Mapped[list["Funcionario"]] = relationship(back_populates="area")
    linhas: Mapped[list["Linha"]] = relationship(back_populates="area")


class Equipe(TimestampMixin, Base):
    __tablename__ = "equipes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    descricao: Mapped[str | None] = mapped_column(Text)

    funcionarios: Mapped[list["Funcionario"]] = relationship(back_populates="equipe")


class Funcionario(TimestampMixin, Base):
    __tablename__ = "funcionarios"
    __table_args__ = (
        CheckConstraint("criticidade_funcionario BETWEEN 1 AND 5", name="criticidade_valida"),
        CheckConstraint("distancia_trabalho_km >= 0", name="distancia_nao_negativa"),
        CheckConstraint("tempo_deslocamento_min >= 0", name="deslocamento_nao_negativo"),
        Index("ix_funcionarios_area_equipe_status", "area_id", "equipe_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matricula: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(180), index=True)
    cpf: Mapped[str] = mapped_column(String(11), unique=True, index=True)
    sexo: Mapped[str | None] = mapped_column(String(1))
    data_nascimento: Mapped[date | None] = mapped_column(Date)
    data_admissao: Mapped[date] = mapped_column(Date)
    area_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("areas.id"), index=True)
    equipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("equipes.id"), index=True)
    turno: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[StatusFuncionario] = mapped_column(
        Enum(StatusFuncionario, name="status_funcionario"), default=StatusFuncionario.ATIVO, index=True
    )
    distancia_trabalho_km: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    tempo_deslocamento_min: Mapped[int] = mapped_column(Integer, default=0)
    possui_veiculo: Mapped[bool] = mapped_column(Boolean, default=False)
    tipo_transporte: Mapped[TipoTransporte | None] = mapped_column(
        Enum(TipoTransporte, name="tipo_transporte")
    )
    criticidade_funcionario: Mapped[int] = mapped_column(Integer, default=1)

    area: Mapped[Area] = relationship(back_populates="funcionarios")
    equipe: Mapped[Equipe] = relationship(back_populates="funcionarios")
    ausencias: Mapped[list["HistoricoAusencia"]] = relationship(back_populates="funcionario")
    habilidades: Mapped[list["FuncionarioHabilidade"]] = relationship(back_populates="funcionario")
    alocacoes: Mapped[list["Alocacao"]] = relationship(back_populates="funcionario")


class HistoricoAusencia(Base):
    __tablename__ = "historicos_ausencia"
    __table_args__ = (Index("ix_ausencias_funcionario_data", "funcionario_id", "data_ausencia"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    funcionario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("funcionarios.id", ondelete="CASCADE"), index=True
    )
    data_ausencia: Mapped[date] = mapped_column(Date, index=True)
    tipo: Mapped[TipoAusencia] = mapped_column(Enum(TipoAusencia, name="tipo_ausencia"))
    motivo: Mapped[str | None] = mapped_column(Text)
    justificada: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    funcionario: Mapped[Funcionario] = relationship(back_populates="ausencias")


class Habilidade(Base):
    __tablename__ = "habilidades"
    __table_args__ = (CheckConstraint("criticidade BETWEEN 1 AND 5", name="criticidade_valida"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    categoria: Mapped[str] = mapped_column(String(100), index=True)
    criticidade: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    funcionarios: Mapped[list["FuncionarioHabilidade"]] = relationship(back_populates="habilidade")
    postos: Mapped[list["PostoHabilidade"]] = relationship(back_populates="habilidade")


class FuncionarioHabilidade(Base):
    __tablename__ = "funcionarios_habilidades"
    __table_args__ = (
        UniqueConstraint("funcionario_id", "habilidade_id"),
        CheckConstraint("nivel BETWEEN 0 AND 5", name="nivel_valido"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    funcionario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("funcionarios.id", ondelete="CASCADE"), index=True
    )
    habilidade_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("habilidades.id", ondelete="CASCADE"), index=True
    )
    nivel: Mapped[int] = mapped_column(Integer, default=0)
    ultima_avaliacao: Mapped[date | None] = mapped_column(Date)
    validade: Mapped[date | None] = mapped_column(Date, index=True)

    funcionario: Mapped[Funcionario] = relationship(back_populates="habilidades")
    habilidade: Mapped[Habilidade] = relationship(back_populates="funcionarios")


class Linha(TimestampMixin, Base):
    __tablename__ = "linhas"
    __table_args__ = (
        UniqueConstraint("area_id", "nome"),
        CheckConstraint("meta_diaria >= 0", name="meta_nao_negativa"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(120))
    area_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("areas.id"), index=True)
    meta_diaria: Mapped[int] = mapped_column(Integer, default=0)

    area: Mapped[Area] = relationship(back_populates="linhas")
    postos: Mapped[list["Posto"]] = relationship(back_populates="linha")


class Posto(Base):
    __tablename__ = "postos"
    __table_args__ = (CheckConstraint("criticidade BETWEEN 1 AND 5", name="criticidade_valida"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(150))
    linha_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("linhas.id"), index=True)
    criticidade: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    linha: Mapped[Linha] = relationship(back_populates="postos")
    habilidades: Mapped[list["PostoHabilidade"]] = relationship(back_populates="posto")
    alocacoes: Mapped[list["Alocacao"]] = relationship(back_populates="posto")


class PostoHabilidade(Base):
    __tablename__ = "postos_habilidades"
    __table_args__ = (
        UniqueConstraint("posto_id", "habilidade_id"),
        CheckConstraint("nivel_minimo BETWEEN 0 AND 5", name="nivel_minimo_valido"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    posto_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("postos.id", ondelete="CASCADE"), index=True
    )
    habilidade_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("habilidades.id", ondelete="CASCADE"), index=True
    )
    nivel_minimo: Mapped[int] = mapped_column(Integer)

    posto: Mapped[Posto] = relationship(back_populates="habilidades")
    habilidade: Mapped[Habilidade] = relationship(back_populates="postos")


class Alocacao(Base):
    __tablename__ = "alocacoes"
    __table_args__ = (
        CheckConstraint("data_fim IS NULL OR data_fim >= data_inicio", name="periodo_valido"),
        Index("ix_alocacoes_posto_ativo", "posto_id", "ativo"),
        Index("ix_alocacoes_funcionario_ativo", "funcionario_id", "ativo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    funcionario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("funcionarios.id"), index=True)
    posto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("postos.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fim: Mapped[date | None] = mapped_column(Date)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    funcionario: Mapped[Funcionario] = relationship(back_populates="alocacoes")
    posto: Mapped[Posto] = relationship(back_populates="alocacoes")

