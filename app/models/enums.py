from enum import StrEnum


class StatusFuncionario(StrEnum):
    ATIVO = "ATIVO"
    FERIAS = "FERIAS"
    AFASTADO = "AFASTADO"
    TREINAMENTO = "TREINAMENTO"
    DESLIGADO = "DESLIGADO"


class TipoTransporte(StrEnum):
    CARRO = "CARRO"
    MOTO = "MOTO"
    ONIBUS = "ONIBUS"
    FRETADO = "FRETADO"
    UBER = "UBER"
    BICICLETA = "BICICLETA"
    A_PE = "A_PE"


class TipoAusencia(StrEnum):
    FALTA = "FALTA"
    ATESTADO = "ATESTADO"
    ACIDENTE = "ACIDENTE"
    FERIAS = "FERIAS"
    LICENCA = "LICENCA"
    TREINAMENTO = "TREINAMENTO"

