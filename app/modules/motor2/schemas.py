from datetime import date
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.modules.motor2.domain import (
    BlockReason,
    BusFactorClassification,
    MatchClassification,
    OperationalImpact,
)


class MatchmakingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    funcionario_ausente_id: UUID
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        validation_alias=AliasChoices("limit", "limite"),
    )


class SkillRequirementResponse(BaseModel):
    habilidade_id: UUID
    nome: str
    nivel_minimo: int


class MatchTargetResponse(BaseModel):
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
    requisitos: list[SkillRequirementResponse]


class MatchComponentsResponse(BaseModel):
    msc: float
    nca: float
    idp: float
    icp: float
    ioc: float
    bfo: BusFactorClassification


class MatchCandidateResponse(BaseModel):
    posicao: int
    funcionario_id: UUID
    nome: str
    score: float
    classificacao: MatchClassification
    impacto: OperationalImpact
    componentes: MatchComponentsResponse
    bloqueios: list[BlockReason]
    posto_origem_id: UUID | None
    posto_origem_codigo: str | None


class MatchmakingResponse(BaseModel):
    data_referencia: date
    versao_algoritmo: str
    total_avaliados: int
    total_bloqueados: int
    alvo: MatchTargetResponse
    substitutos: list[MatchCandidateResponse]


class PlannedSubstitutionResponse(BaseModel):
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


class BatchPlanningResponse(BaseModel):
    data_referencia: date
    total_ausentes: int
    total_cobertos: int
    total_sem_cobertura: int
    substituicoes: list[PlannedSubstitutionResponse]
