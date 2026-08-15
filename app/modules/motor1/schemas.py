"""Schemas HTTP do Motor 1."""

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.modules.motor1.domain import ClassificacaoAbsenteismo


class FatoresFuncionarioAbsenteismoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    iha: float
    idt: float


class FuncionarioAbsenteismoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    matricula: str
    nome: str
    turno: str
    status: str
    probabilidade_falta: float
    classificacao: ClassificacaoAbsenteismo
    fatores: FatoresFuncionarioAbsenteismoResponse


class PrevisaoAbsenteismoEquipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    equipe: str
    equipe_numero: int
    data_referencia: date
    total_funcionarios: int
    funcionarios: tuple[FuncionarioAbsenteismoResponse, ...]
    algoritmo_versao: str
