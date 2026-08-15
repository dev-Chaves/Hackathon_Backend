"""Tipos de dominio do Motor 1."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from app.models.enums import TipoTransporte

ABSENTEISMO_ALGORITHM_VERSION = "absenteismo-v1"


class ClassificacaoAbsenteismo(StrEnum):
    BAIXO_RISCO = "BAIXO_RISCO"
    MEDIO_RISCO = "MEDIO_RISCO"
    ALTO_RISCO = "ALTO_RISCO"
    CRITICO = "CRITICO"


@dataclass(frozen=True)
class AusenciaHistorica:
    data_ausencia: date


@dataclass(frozen=True)
class FuncionarioAbsenteismoInput:
    id: str
    matricula: str
    nome: str
    turno: str
    status: str
    distancia_trabalho_km: float
    tempo_deslocamento_min: int
    tipo_transporte: str | TipoTransporte | None
    ausencias: tuple[AusenciaHistorica, ...] = ()


@dataclass(frozen=True)
class FatoresFuncionarioAbsenteismo:
    iha: float
    idt: float


@dataclass(frozen=True)
class ResultadoFuncionarioAbsenteismo:
    id: str
    matricula: str
    nome: str
    turno: str
    status: str
    probabilidade_falta: float
    classificacao: ClassificacaoAbsenteismo
    fatores: FatoresFuncionarioAbsenteismo


@dataclass(frozen=True)
class ResultadoPrevisaoAbsenteismoEquipe:
    equipe: str
    equipe_numero: int
    data_referencia: date
    total_funcionarios: int
    funcionarios: tuple[ResultadoFuncionarioAbsenteismo, ...]
    algoritmo_versao: str = ABSENTEISMO_ALGORITHM_VERSION
