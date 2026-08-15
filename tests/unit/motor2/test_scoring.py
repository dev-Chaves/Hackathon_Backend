from datetime import date
from uuid import UUID, uuid4

import pytest

from app.modules.motor2.domain import (
    BlockReason,
    BusFactorClassification,
    CandidateContext,
    MatchClassification,
    MatchComponents,
    MatchmakingConfig,
    SkillQualification,
    SkillRequirement,
)
from app.modules.motor2.scoring import (
    calculate_idp,
    calculate_ioc,
    calculate_msc,
    calculate_mso,
    calculate_nca,
    classify_bus_factor,
    classify_match,
    evaluate_candidate,
)

REFERENCE_DATE = date(2026, 8, 15)


def requirement(skill_id: UUID, minimum: int = 3) -> SkillRequirement:
    return SkillRequirement(habilidade_id=skill_id, nome="Skill", nivel_minimo=minimum)


def candidate(
    skills: dict[UUID, SkillQualification] | None = None,
    **overrides: object,
) -> CandidateContext:
    values: dict[str, object] = {
        "funcionario_id": uuid4(),
        "nome": "Candidato",
        "status": "ATIVO",
        "criticidade_funcionario": 2,
        "habilidades": skills or {},
        "quantidade_substitutos_origem": 3,
        "cobertura_atual_origem": 95.0,
        "cobertura_pos_movimentacao": 90.0,
    }
    values.update(overrides)
    return CandidateContext(**values)  # type: ignore[arg-type]


def qualification(
    skill_id: UUID, level: int, valid_until: date | None = None
) -> SkillQualification:
    return SkillQualification(
        habilidade_id=skill_id,
        nivel=level,
        validade=valid_until,
    )


def test_msc_counts_only_valid_qualifications_at_required_level() -> None:
    skill_a, skill_b, skill_c = uuid4(), uuid4(), uuid4()
    requirements = [requirement(skill_a), requirement(skill_b), requirement(skill_c)]
    subject = candidate(
        {
            skill_a: qualification(skill_a, 4, date(2027, 1, 1)),
            skill_b: qualification(skill_b, 2, date(2027, 1, 1)),
            skill_c: qualification(skill_c, 5, date(2025, 1, 1)),
        }
    )

    assert calculate_msc(requirements, subject, REFERENCE_DATE) == 33.33


def test_nca_normalizes_average_level_to_one_hundred() -> None:
    skill_a, skill_b = uuid4(), uuid4()
    subject = candidate(
        {
            skill_a: qualification(skill_a, 5),
            skill_b: qualification(skill_b, 3),
        }
    )

    assert calculate_nca([requirement(skill_a), requirement(skill_b)], subject) == 80.0


@pytest.mark.parametrize(
    ("status", "has_absence", "expected"),
    [
        ("ATIVO", False, 100.0),
        ("TREINAMENTO", False, 50.0),
        ("FERIAS", False, 0.0),
        ("ATIVO", True, 0.0),
    ],
)
def test_idp_reflects_real_availability(status: str, has_absence: bool, expected: float) -> None:
    assert (
        calculate_idp(candidate(status=status, possui_ausencia_na_data=has_absence)) == expected
    )


@pytest.mark.parametrize(
    ("criticality", "backups", "expected"),
    [(5, 0, 100.0), (2, 4, 12.5), (4, 1, 100.0), (0, 0, 0.0)],
)
def test_ioc_penalizes_critical_origin_with_few_backups(
    criticality: int, backups: int, expected: float
) -> None:
    assert calculate_ioc(criticality, backups) == expected


@pytest.mark.parametrize(
    ("backups", "expected"),
    [
        (0, BusFactorClassification.CRITICO),
        (1, BusFactorClassification.CRITICO),
        (2, BusFactorClassification.ATENCAO),
        (4, BusFactorClassification.ADEQUADO),
        (5, BusFactorClassification.SEGURO),
    ],
)
def test_bus_factor_classification(backups: int, expected: BusFactorClassification) -> None:
    assert classify_bus_factor(backups) == expected


def test_mso_uses_documented_weights() -> None:
    components = MatchComponents(
        msc=100,
        nca=80,
        idp=100,
        icp=90,
        ioc=20,
        bfo=BusFactorClassification.ADEQUADO,
    )

    assert calculate_mso(components, MatchmakingConfig()) == 90.5
    assert classify_match(90.5) == MatchClassification.EXCELENTE


def test_candidate_is_blocked_when_required_skill_is_missing() -> None:
    evaluation = evaluate_candidate(
        candidate=candidate(),
        requirements=[requirement(uuid4())],
        destination_criticality=5,
        reference_date=REFERENCE_DATE,
    )

    assert not evaluation.elegivel
    assert BlockReason.HABILIDADE_OBRIGATORIA_AUSENTE in evaluation.bloqueios


def test_candidate_is_blocked_when_qualification_is_expired() -> None:
    skill_id = uuid4()
    evaluation = evaluate_candidate(
        candidate=candidate({skill_id: qualification(skill_id, 5, date(2026, 8, 14))}),
        requirements=[requirement(skill_id)],
        destination_criticality=5,
        reference_date=REFERENCE_DATE,
    )

    assert BlockReason.CAPACITACAO_VENCIDA in evaluation.bloqueios


def test_critical_professional_without_backup_cannot_move() -> None:
    skill_id = uuid4()
    evaluation = evaluate_candidate(
        candidate=candidate(
            {skill_id: qualification(skill_id, 5)},
            criticidade_funcionario=4,
            posto_origem_id=uuid4(),
            criticidade_origem=3,
            quantidade_substitutos_origem=1,
        ),
        requirements=[requirement(skill_id)],
        destination_criticality=5,
        reference_date=REFERENCE_DATE,
    )

    assert BlockReason.PROFISSIONAL_CRITICO_SEM_BACKUP in evaluation.bloqueios


def test_more_critical_origin_and_low_coverage_are_eliminatory() -> None:
    skill_id = uuid4()
    evaluation = evaluate_candidate(
        candidate=candidate(
            {skill_id: qualification(skill_id, 5)},
            criticidade_origem=5,
            cobertura_pos_movimentacao=79.99,
        ),
        requirements=[requirement(skill_id)],
        destination_criticality=4,
        reference_date=REFERENCE_DATE,
    )

    assert BlockReason.ORIGEM_MAIS_CRITICA in evaluation.bloqueios
    assert BlockReason.COBERTURA_ORIGEM_ABAIXO_DO_LIMITE in evaluation.bloqueios


def test_fully_qualified_available_candidate_is_eligible() -> None:
    skill_id = uuid4()
    evaluation = evaluate_candidate(
        candidate=candidate(
            {skill_id: qualification(skill_id, 5, date(2027, 1, 1))},
            criticidade_origem=2,
            quantidade_substitutos_origem=5,
        ),
        requirements=[requirement(skill_id, minimum=4)],
        destination_criticality=5,
        reference_date=REFERENCE_DATE,
    )

    assert evaluation.elegivel
    assert evaluation.bloqueios == ()
    assert evaluation.componentes.msc == 100.0
