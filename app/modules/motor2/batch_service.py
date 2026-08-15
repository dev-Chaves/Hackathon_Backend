import uuid
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from uuid import UUID

from ortools.sat.python import cp_model
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.entities import Equipe, Funcionario, Posto, SubstituicaoPlanejada
from app.modules.motor2.domain import (
    BatchPlanningResult,
    CandidateEvaluation,
    MatchmakingConfig,
    PlannedSubstitution,
)
from app.modules.motor2.repository import MatchmakingRepository
from app.modules.motor2.scoring import evaluate_candidate


class BatchMatchmakingService:
    def __init__(
        self,
        session: AsyncSession,
        config: MatchmakingConfig | None = None,
        repository: MatchmakingRepository | None = None,
    ) -> None:
        self.session = session
        self.config = config or MatchmakingConfig()
        self.repository = repository or MatchmakingRepository(session)

    async def plan_daily_absences(self, reference_date: date) -> BatchPlanningResult:
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"motor2-planejamento-{reference_date.isoformat()}"},
        )
        existing = await self._existing_reservations(reference_date)
        reserved_candidates = {item.funcionario_substituto_id for item in existing}
        planned_absents = {item.funcionario_ausente_id for item in existing}
        snapshots = await self.repository.build_batch_snapshots(
            reference_date,
            reserved_candidate_ids=reserved_candidates,
        )
        candidates_by_absent: dict[UUID, list[CandidateEvaluation]] = {}
        targets = {}
        for snapshot in snapshots:
            absent_id = snapshot.alvo.funcionario_ausente_id
            targets[absent_id] = snapshot.alvo
            if absent_id in planned_absents:
                continue
            candidates_by_absent[absent_id] = [
                evaluation
                for candidate in snapshot.candidatos
                if (
                    evaluation := evaluate_candidate(
                        candidate=candidate,
                        requirements=list(snapshot.alvo.requisitos),
                        destination_criticality=snapshot.alvo.criticidade_destino,
                        reference_date=reference_date,
                        config=self.config,
                    )
                ).elegivel
            ]

        assignments = optimize_global_assignments(candidates_by_absent)
        for absent_id, evaluation in assignments.items():
            target = targets[absent_id]
            self.session.add(
                SubstituicaoPlanejada(
                    id=uuid.uuid4(),
                    data_referencia=reference_date,
                    funcionario_ausente_id=absent_id,
                    funcionario_substituto_id=evaluation.funcionario_id,
                    posto_destino_id=target.posto_id,
                    score=Decimal(str(evaluation.score)),
                )
            )
        await self.session.commit()

        substitutions = await self._load_planned_results(reference_date)
        total_absent = len(snapshots)
        total_covered = len(substitutions)
        return BatchPlanningResult(
            data_referencia=reference_date,
            total_ausentes=total_absent,
            total_cobertos=total_covered,
            total_sem_cobertura=max(total_absent - total_covered, 0),
            substituicoes=tuple(substitutions),
        )

    async def _existing_reservations(self, reference_date: date) -> list[SubstituicaoPlanejada]:
        statement = select(SubstituicaoPlanejada).where(
            SubstituicaoPlanejada.data_referencia == reference_date
        )
        return list((await self.session.execute(statement)).scalars().all())

    async def _load_planned_results(self, reference_date: date) -> list[PlannedSubstitution]:
        absent = aliased(Funcionario)
        substitute = aliased(Funcionario)
        statement = (
            select(
                SubstituicaoPlanejada,
                absent.nome,
                substitute.nome,
                Posto.codigo,
                Equipe.id,
                Equipe.nome,
                Equipe.tech_lead_nome,
                Equipe.tech_lead_email,
            )
            .join(absent, absent.id == SubstituicaoPlanejada.funcionario_ausente_id)
            .join(substitute, substitute.id == SubstituicaoPlanejada.funcionario_substituto_id)
            .join(Posto, Posto.id == SubstituicaoPlanejada.posto_destino_id)
            .join(Equipe, Equipe.id == absent.equipe_id)
            .where(SubstituicaoPlanejada.data_referencia == reference_date)
            .order_by(Equipe.nome, absent.nome)
        )
        return [
            PlannedSubstitution(
                funcionario_ausente_id=reservation.funcionario_ausente_id,
                funcionario_ausente_nome=absent_name,
                funcionario_substituto_id=reservation.funcionario_substituto_id,
                funcionario_substituto_nome=substitute_name,
                posto_destino_id=reservation.posto_destino_id,
                posto_destino_codigo=post_code,
                score=float(reservation.score),
                equipe_id=team_id,
                equipe_nome=team_name,
                tech_lead_nome=lead_name,
                tech_lead_email=lead_email,
            )
            for (
                reservation,
                absent_name,
                substitute_name,
                post_code,
                team_id,
                team_name,
                lead_name,
                lead_email,
            ) in (await self.session.execute(statement)).all()
        ]


def optimize_global_assignments(
    candidates_by_absent: Mapping[UUID, Sequence[CandidateEvaluation]],
) -> dict[UUID, CandidateEvaluation]:
    model = cp_model.CpModel()
    variables = {}
    evaluations = {}
    for absent_id, candidates in candidates_by_absent.items():
        for candidate in candidates:
            key = (absent_id, candidate.funcionario_id)
            variables[key] = model.new_bool_var(f"assign_{absent_id}_{candidate.funcionario_id}")
            evaluations[key] = candidate

    for absent_id in candidates_by_absent:
        model.add(
            sum(
                variable
                for (current_absent, _), variable in variables.items()
                if current_absent == absent_id
            )
            <= 1
        )
    candidate_ids = {candidate_id for _, candidate_id in variables}
    for candidate_id in candidate_ids:
        model.add(
            sum(
                variable
                for (_, current_candidate), variable in variables.items()
                if current_candidate == candidate_id
            )
            <= 1
        )

    model.maximize(
        sum(
            (1_000_000 + round(evaluations[key].score * 100)) * variable
            for key, variable in variables.items()
        )
    )
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.num_search_workers = 8
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {}
    return {
        absent_id: evaluations[(absent_id, candidate_id)]
        for (absent_id, candidate_id), variable in variables.items()
        if solver.value(variable)
    }
