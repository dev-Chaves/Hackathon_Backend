from datetime import date
from uuid import UUID, uuid4

import pytest

from app.modules.motor2.domain import (
    CandidateContext,
    MatchmakingSnapshot,
    SkillQualification,
    SkillRequirement,
    TargetContext,
)
from app.modules.motor2.service import MatchmakingService


class FakeRepository:
    def __init__(self, snapshot: MatchmakingSnapshot) -> None:
        self.snapshot = snapshot

    async def build_snapshot(self, *_: object) -> MatchmakingSnapshot:
        return self.snapshot


def make_candidate(name: str, level: int, skill_id: UUID, backups: int) -> CandidateContext:
    return CandidateContext(
        funcionario_id=uuid4(),
        nome=name,
        status="ATIVO",
        criticidade_funcionario=2,
        habilidades={
            skill_id: SkillQualification(
                habilidade_id=skill_id,
                nivel=level,
                validade=date(2027, 1, 1),
            )
        },
        criticidade_origem=2,
        quantidade_substitutos_origem=backups,
        cobertura_atual_origem=95,
        cobertura_pos_movimentacao=90,
    )


@pytest.mark.asyncio
async def test_service_ranks_best_score_and_respects_limit() -> None:
    skill_id = uuid4()
    target = TargetContext(
        funcionario_ausente_id=uuid4(),
        funcionario_ausente_nome="Ausente",
        posto_id=uuid4(),
        posto_codigo="P101",
        posto_nome="Solda",
        linha_id=uuid4(),
        linha_nome="Linha 1",
        area_id=uuid4(),
        area_nome="Carroceria",
        criticidade_destino=5,
        requisitos=(SkillRequirement(skill_id, "Solda", 3),),
    )
    snapshot = MatchmakingSnapshot(
        alvo=target,
        candidatos=(
            make_candidate("Carlos", 3, skill_id, 2),
            make_candidate("Pedro", 5, skill_id, 5),
            make_candidate("Sem nivel", 2, skill_id, 5),
        ),
    )
    service = MatchmakingService(
        session=None,  # type: ignore[arg-type]
        repository=FakeRepository(snapshot),  # type: ignore[arg-type]
    )

    result = await service.recommend_substitutes(target.funcionario_ausente_id, date.today(), 1)

    assert result.total_avaliados == 3
    assert result.total_bloqueados == 1
    assert len(result.ranking) == 1
    assert result.ranking[0].nome == "Pedro"


@pytest.mark.asyncio
async def test_service_uses_stable_name_tiebreaker() -> None:
    skill_id = uuid4()
    target = TargetContext(
        funcionario_ausente_id=uuid4(),
        funcionario_ausente_nome="Ausente",
        posto_id=uuid4(),
        posto_codigo="P101",
        posto_nome="Solda",
        linha_id=uuid4(),
        linha_nome="Linha 1",
        area_id=uuid4(),
        area_nome="Carroceria",
        criticidade_destino=5,
        requisitos=(SkillRequirement(skill_id, "Solda", 3),),
    )
    snapshot = MatchmakingSnapshot(
        alvo=target,
        candidatos=(
            make_candidate("Bruno", 4, skill_id, 3),
            make_candidate("Ana", 4, skill_id, 3),
        ),
    )
    service = MatchmakingService(
        session=None,  # type: ignore[arg-type]
        repository=FakeRepository(snapshot),  # type: ignore[arg-type]
    )

    result = await service.recommend_substitutes(target.funcionario_ausente_id, date.today())

    assert [candidate.nome for candidate in result.ranking] == ["Ana", "Bruno"]
