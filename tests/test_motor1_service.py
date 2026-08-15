from datetime import date, timedelta

from app.models.enums import TipoTransporte
from app.modules.motor1.domain import (
    AusenciaHistorica,
    ClassificacaoAbsenteismo,
    FuncionarioAbsenteismoInput,
)
from app.modules.motor1.scoring import (
    analisar_funcionario_absenteismo,
    calcular_idt,
    calcular_iha,
    calcular_probabilidade_falta,
    classificar_absenteismo,
)


def test_calcular_iha_pondera_janelas_historicas() -> None:
    data_referencia = date(2026, 8, 15)
    ausencias = (
        AusenciaHistorica(data_referencia - timedelta(days=10)),
        AusenciaHistorica(data_referencia - timedelta(days=60)),
        AusenciaHistorica(data_referencia - timedelta(days=180)),
        AusenciaHistorica(data_referencia + timedelta(days=1)),
    )

    assert calcular_iha(ausencias, data_referencia) == 17


def test_calcular_iha_limita_resultado_em_cem() -> None:
    data_referencia = date(2026, 8, 15)
    ausencias = tuple(
        AusenciaHistorica(data_referencia - timedelta(days=1)) for _ in range(20)
    )

    assert calcular_iha(ausencias, data_referencia) == 100


def test_calcular_idt_normaliza_distancia_tempo_e_transporte() -> None:
    resultado = calcular_idt(
        distancia_trabalho_km=25,
        tempo_deslocamento_min=60,
        tipo_transporte=TipoTransporte.ONIBUS,
    )

    assert resultado == 55


def test_calcular_idt_aceita_transporte_como_texto() -> None:
    resultado = calcular_idt(
        distancia_trabalho_km=50,
        tempo_deslocamento_min=120,
        tipo_transporte="MOTO",
    )

    assert round(resultado, 2) == 93.33


def test_calcular_probabilidade_falta_combina_iha_e_idt() -> None:
    resultado = calcular_probabilidade_falta(iha=70, idt=40)

    assert resultado == 61


def test_classificar_absenteismo_respeita_faixas_de_risco() -> None:
    assert classificar_absenteismo(30) == ClassificacaoAbsenteismo.BAIXO_RISCO
    assert classificar_absenteismo(60) == ClassificacaoAbsenteismo.MEDIO_RISCO
    assert classificar_absenteismo(80) == ClassificacaoAbsenteismo.ALTO_RISCO
    assert classificar_absenteismo(81) == ClassificacaoAbsenteismo.CRITICO


def test_analisar_funcionario_absenteismo_retorna_dados_da_rota() -> None:
    data_referencia = date(2026, 8, 15)
    funcionario = FuncionarioAbsenteismoInput(
        id="f1",
        matricula="M001",
        nome="Ana",
        turno="TURNO_1",
        status="ATIVO",
        distancia_trabalho_km=25,
        tempo_deslocamento_min=60,
        tipo_transporte=TipoTransporte.ONIBUS,
        ausencias=(AusenciaHistorica(data_referencia - timedelta(days=10)),),
    )

    resultado = analisar_funcionario_absenteismo(funcionario, data_referencia)

    assert resultado.id == "f1"
    assert resultado.matricula == "M001"
    assert resultado.nome == "Ana"
    assert resultado.turno == "TURNO_1"
    assert resultado.status == "ATIVO"
    assert resultado.probabilidade_falta == 23.5
    assert resultado.classificacao == ClassificacaoAbsenteismo.BAIXO_RISCO
    assert resultado.fatores.iha == 10
    assert resultado.fatores.idt == 55
