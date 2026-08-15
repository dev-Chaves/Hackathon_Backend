"""Casos de uso do Motor 1."""

from datetime import date

from app.modules.motor1.domain import ResultadoPrevisaoAbsenteismoEquipe
from app.modules.motor1.exceptions import EquipeNaoEncontradaError
from app.modules.motor1.repository import Motor1Repository
from app.modules.motor1.scoring import analisar_funcionario_absenteismo


class Motor1Service:
    def __init__(self, repository: Motor1Repository) -> None:
        self._repository = repository

    async def prever_absenteismo_por_equipe(
        self,
        equipe_numero: int,
        data_referencia: date,
    ) -> ResultadoPrevisaoAbsenteismoEquipe:
        dados_equipe = await self._repository.buscar_absenteismo_por_equipe_numero(equipe_numero)
        if dados_equipe is None:
            raise EquipeNaoEncontradaError(f"Equipe {equipe_numero} nao encontrada")

        equipe_nome, funcionarios = dados_equipe
        resultados = tuple(
            sorted(
                (
                    analisar_funcionario_absenteismo(funcionario, data_referencia)
                    for funcionario in funcionarios
                ),
                key=lambda resultado: (-resultado.probabilidade_falta, resultado.nome),
            )
        )

        return ResultadoPrevisaoAbsenteismoEquipe(
            equipe=equipe_nome,
            equipe_numero=equipe_numero,
            data_referencia=data_referencia,
            total_funcionarios=len(resultados),
            funcionarios=resultados,
        )
