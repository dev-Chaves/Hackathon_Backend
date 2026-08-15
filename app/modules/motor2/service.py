from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.motor2.domain import (
    CandidateEvaluation,
    MatchmakingConfig,
    MatchmakingResult,
)
from app.modules.motor2.repository import MatchmakingRepository
from app.modules.motor2.scoring import evaluate_candidate


class MatchmakingService:
    def __init__(
        self,
        session: AsyncSession,
        config: MatchmakingConfig | None = None,
        repository: MatchmakingRepository | None = None,
    ) -> None:
        self.config = config or MatchmakingConfig()
        self.repository = repository or MatchmakingRepository(session)

    async def recommend_substitutes(
        self,
        funcionario_ausente_id: UUID,
        reference_date: date,
        limit: int = 10,
    ) -> MatchmakingResult:
        snapshot = await self.repository.build_snapshot(funcionario_ausente_id, reference_date)
        evaluations = [
            evaluate_candidate(
                candidate=candidate,
                requirements=list(snapshot.alvo.requisitos),
                destination_criticality=snapshot.alvo.criticidade_destino,
                reference_date=reference_date,
                config=self.config,
            )
            for candidate in snapshot.candidatos
        ]
        eligible = sorted(
            (evaluation for evaluation in evaluations if evaluation.elegivel),
            key=_ranking_key,
        )
        return MatchmakingResult(
            alvo=snapshot.alvo,
            data_referencia=reference_date,
            versao_algoritmo=self.config.versao_algoritmo,
            total_avaliados=len(evaluations),
            total_bloqueados=sum(not evaluation.elegivel for evaluation in evaluations),
            ranking=tuple(eligible[:limit]),
        )


def _ranking_key(evaluation: CandidateEvaluation) -> tuple[float, float, str, str]:
    return (
        -evaluation.score,
        evaluation.componentes.ioc,
        evaluation.nome.casefold(),
        str(evaluation.funcionario_id),
    )
