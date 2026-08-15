"""Formulas deterministicas da previsao de absenteismo."""

from collections.abc import Iterable
from datetime import date, timedelta

from app.models.enums import TipoTransporte
from app.modules.motor1.domain import (
    AusenciaHistorica,
    ClassificacaoAbsenteismo,
    FatoresFuncionarioAbsenteismo,
    FuncionarioAbsenteismoInput,
    ResultadoFuncionarioAbsenteismo,
)

MAX_WEIGHTED_ABSENCES = 10
MAX_DISTANCE_KM = 50
MAX_COMMUTE_MINUTES = 120

ABSENTEISMO_IHA_WEIGHT = 0.70
ABSENTEISMO_IDT_WEIGHT = 0.30


def calcular_iha(ausencias: Iterable[AusenciaHistorica], data_referencia: date) -> float:
    faltas_30d = 0
    faltas_90d = 0
    faltas_12m = 0

    limite_30d = data_referencia - timedelta(days=30)
    limite_90d = data_referencia - timedelta(days=90)
    limite_12m = data_referencia - timedelta(days=365)

    for ausencia in ausencias:
        if ausencia.data_ausencia > data_referencia:
            continue
        if ausencia.data_ausencia >= limite_30d:
            faltas_30d += 1
        if ausencia.data_ausencia >= limite_90d:
            faltas_90d += 1
        if ausencia.data_ausencia >= limite_12m:
            faltas_12m += 1

    score_bruto = (faltas_30d * 0.5) + (faltas_90d * 0.3) + (faltas_12m * 0.2)
    return _as_percent(score_bruto, MAX_WEIGHTED_ABSENCES)


def calcular_idt(
    distancia_trabalho_km: float,
    tempo_deslocamento_min: int,
    tipo_transporte: str | TipoTransporte | None,
) -> float:
    distancia_score = _as_percent(distancia_trabalho_km, MAX_DISTANCE_KM)
    tempo_score = _as_percent(tempo_deslocamento_min, MAX_COMMUTE_MINUTES)
    transporte_score = _as_percent(_peso_transporte(tipo_transporte), 3)

    return _clamp((distancia_score * 0.4) + (tempo_score * 0.5) + (transporte_score * 0.1))


def calcular_probabilidade_falta(iha: float, idt: float) -> float:
    return round(_clamp((iha * ABSENTEISMO_IHA_WEIGHT) + (idt * ABSENTEISMO_IDT_WEIGHT)), 2)


def classificar_absenteismo(probabilidade_falta: float) -> ClassificacaoAbsenteismo:
    if probabilidade_falta <= 30:
        return ClassificacaoAbsenteismo.BAIXO_RISCO
    if probabilidade_falta <= 60:
        return ClassificacaoAbsenteismo.MEDIO_RISCO
    if probabilidade_falta <= 80:
        return ClassificacaoAbsenteismo.ALTO_RISCO
    return ClassificacaoAbsenteismo.CRITICO


def analisar_funcionario_absenteismo(
    funcionario: FuncionarioAbsenteismoInput,
    data_referencia: date,
) -> ResultadoFuncionarioAbsenteismo:
    iha = calcular_iha(funcionario.ausencias, data_referencia)
    idt = calcular_idt(
        funcionario.distancia_trabalho_km,
        funcionario.tempo_deslocamento_min,
        funcionario.tipo_transporte,
    )
    probabilidade_falta = calcular_probabilidade_falta(iha=iha, idt=idt)

    return ResultadoFuncionarioAbsenteismo(
        id=funcionario.id,
        matricula=funcionario.matricula,
        nome=funcionario.nome,
        turno=funcionario.turno,
        status=funcionario.status,
        probabilidade_falta=probabilidade_falta,
        classificacao=classificar_absenteismo(probabilidade_falta),
        fatores=FatoresFuncionarioAbsenteismo(
            iha=round(iha, 2),
            idt=round(idt, 2),
        ),
    )


def _peso_transporte(tipo_transporte: str | TipoTransporte | None) -> int:
    if tipo_transporte is None:
        return 0

    transporte = str(tipo_transporte)
    if "." in transporte:
        transporte = transporte.rsplit(".", maxsplit=1)[-1]

    pesos = {
        TipoTransporte.CARRO.value: 0,
        TipoTransporte.MOTO.value: 1,
        TipoTransporte.FRETADO.value: 2,
        TipoTransporte.ONIBUS.value: 3,
        TipoTransporte.UBER.value: 2,
        TipoTransporte.BICICLETA.value: 1,
        TipoTransporte.A_PE.value: 2,
    }
    return pesos.get(transporte.upper(), 0)


def _clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return min(max(value, minimum), maximum)


def _as_percent(value: float, maximum: float) -> float:
    if maximum <= 0:
        return 0
    return _clamp((value / maximum) * 100)
