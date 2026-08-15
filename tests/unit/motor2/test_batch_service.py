from uuid import uuid4

from app.modules.motor2.batch_service import optimize_global_assignments
from app.modules.motor2.domain import (
    BusFactorClassification,
    CandidateEvaluation,
    MatchClassification,
    MatchComponents,
    OperationalImpact,
)


def evaluation(candidate_id, name: str, score: float) -> CandidateEvaluation:
    return CandidateEvaluation(
        funcionario_id=candidate_id,
        nome=name,
        elegivel=True,
        score=score,
        classificacao=MatchClassification.EXCELENTE,
        impacto=OperationalImpact.BAIXO,
        componentes=MatchComponents(
            msc=100,
            nca=100,
            idp=100,
            icp=100,
            ioc=0,
            bfo=BusFactorClassification.SEGURO,
        ),
    )


def test_optimizer_never_assigns_same_person_twice() -> None:
    absent_a, absent_b = uuid4(), uuid4()
    shared_candidate, alternative = uuid4(), uuid4()

    result = optimize_global_assignments(
        {
            absent_a: [
                evaluation(shared_candidate, "Compartilhado", 99),
                evaluation(alternative, "Alternativo", 80),
            ],
            absent_b: [evaluation(shared_candidate, "Compartilhado", 98)],
        }
    )

    assert len(result) == 2
    assert result[absent_b].funcionario_id == shared_candidate
    assert result[absent_a].funcionario_id == alternative
    assert len({item.funcionario_id for item in result.values()}) == 2


def test_optimizer_returns_empty_when_nobody_is_eligible() -> None:
    assert optimize_global_assignments({uuid4(): []}) == {}
