from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from uuid import UUID


class MatchClassification(StrEnum):
    EXCELENTE = "EXCELENTE"
    BOM = "BOM"
    ACEITAVEL = "ACEITAVEL"
    NAO_RECOMENDADO = "NAO_RECOMENDADO"


class OperationalImpact(StrEnum):
    BAIXO = "BAIXO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


class BusFactorClassification(StrEnum):
    CRITICO = "CRITICO"
    ATENCAO = "ATENCAO"
    ADEQUADO = "ADEQUADO"
    SEGURO = "SEGURO"


class BlockReason(StrEnum):
    INDISPONIVEL = "INDISPONIVEL"
    HABILIDADE_OBRIGATORIA_AUSENTE = "HABILIDADE_OBRIGATORIA_AUSENTE"
    CAPACITACAO_VENCIDA = "CAPACITACAO_VENCIDA"
    NIVEL_INSUFICIENTE = "NIVEL_INSUFICIENTE"
    PROFISSIONAL_CRITICO_SEM_BACKUP = "PROFISSIONAL_CRITICO_SEM_BACKUP"
    ORIGEM_MAIS_CRITICA = "ORIGEM_MAIS_CRITICA"
    COBERTURA_ORIGEM_ABAIXO_DO_LIMITE = "COBERTURA_ORIGEM_ABAIXO_DO_LIMITE"


@dataclass(frozen=True)
class SkillRequirement:
    habilidade_id: UUID
    nome: str
    nivel_minimo: int


@dataclass(frozen=True)
class SkillQualification:
    habilidade_id: UUID
    nivel: int
    validade: date | None


@dataclass(frozen=True)
class CandidateContext:
    funcionario_id: UUID
    nome: str
    status: str
    criticidade_funcionario: int
    habilidades: dict[UUID, SkillQualification]
    possui_ausencia_na_data: bool = False
    criticidade_origem: int = 0
    quantidade_substitutos_origem: int = 0
    cobertura_atual_origem: float = 100.0
    cobertura_pos_movimentacao: float = 100.0
    posto_origem_id: UUID | None = None
    posto_origem_codigo: str | None = None


@dataclass(frozen=True)
class MatchComponents:
    msc: float
    nca: float
    idp: float
    icp: float
    ioc: float
    bfo: BusFactorClassification


@dataclass(frozen=True)
class CandidateEvaluation:
    funcionario_id: UUID
    nome: str
    elegivel: bool
    score: float
    classificacao: MatchClassification
    impacto: OperationalImpact
    componentes: MatchComponents
    bloqueios: tuple[BlockReason, ...] = field(default_factory=tuple)
    posto_origem_id: UUID | None = None
    posto_origem_codigo: str | None = None


@dataclass(frozen=True)
class MatchmakingConfig:
    cobertura_minima: float = 80.0
    peso_msc: float = 0.35
    peso_nca: float = 0.25
    peso_idp: float = 0.10
    peso_icp: float = 0.15
    peso_ioc_invertido: float = 0.15
    versao_algoritmo: str = "mms-1.0"


@dataclass(frozen=True)
class TargetContext:
    funcionario_ausente_id: UUID
    funcionario_ausente_nome: str
    posto_id: UUID
    posto_codigo: str
    posto_nome: str
    linha_id: UUID
    linha_nome: str
    area_id: UUID
    area_nome: str
    criticidade_destino: int
    requisitos: tuple[SkillRequirement, ...]
    equipe_id: UUID | None = None
    equipe_nome: str | None = None
    tech_lead_nome: str | None = None
    tech_lead_email: str | None = None


@dataclass(frozen=True)
class MatchmakingSnapshot:
    alvo: TargetContext
    candidatos: tuple[CandidateContext, ...]


@dataclass(frozen=True)
class MatchmakingResult:
    alvo: TargetContext
    data_referencia: date
    versao_algoritmo: str
    total_avaliados: int
    total_bloqueados: int
    ranking: tuple[CandidateEvaluation, ...]


@dataclass(frozen=True)
class PlannedSubstitution:
    funcionario_ausente_id: UUID
    funcionario_ausente_nome: str
    funcionario_substituto_id: UUID
    funcionario_substituto_nome: str
    posto_destino_id: UUID
    posto_destino_codigo: str
    score: float
    equipe_id: UUID | None
    equipe_nome: str | None
    tech_lead_nome: str | None
    tech_lead_email: str | None


@dataclass(frozen=True)
class BatchPlanningResult:
    data_referencia: date
    total_ausentes: int
    total_cobertos: int
    total_sem_cobertura: int
    substituicoes: tuple[PlannedSubstitution, ...]
