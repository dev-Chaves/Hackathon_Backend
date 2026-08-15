from datetime import date

from app.modules.motor2.domain import (
    BlockReason,
    BusFactorClassification,
    CandidateContext,
    CandidateEvaluation,
    MatchClassification,
    MatchComponents,
    MatchmakingConfig,
    OperationalImpact,
    SkillRequirement,
)


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def calculate_msc(
    requirements: list[SkillRequirement], candidate: CandidateContext, reference_date: date
) -> float:
    if not requirements:
        return 100.0
    compatible = sum(
        1
        for requirement in requirements
        if _qualification_meets(requirement, candidate, reference_date)
    )
    return round(compatible / len(requirements) * 100, 2)


def calculate_nca(requirements: list[SkillRequirement], candidate: CandidateContext) -> float:
    if not requirements:
        return 100.0
    levels = [
        candidate.habilidades.get(requirement.habilidade_id).nivel
        if candidate.habilidades.get(requirement.habilidade_id)
        else 0
        for requirement in requirements
    ]
    return round(sum(levels) / len(levels) / 5 * 100, 2)


def calculate_idp(candidate: CandidateContext) -> float:
    if candidate.possui_ausencia_na_data:
        return 0.0
    if candidate.status == "ATIVO":
        return 100.0
    if candidate.status == "TREINAMENTO":
        return 50.0
    return 0.0


def calculate_ioc(criticidade_origem: int, quantidade_substitutos: int) -> float:
    if criticidade_origem <= 0:
        return 0.0
    if quantidade_substitutos <= 0:
        return 100.0
    return round(clamp(criticidade_origem * 25 / quantidade_substitutos), 2)


def classify_bus_factor(quantidade_substitutos: int) -> BusFactorClassification:
    if quantidade_substitutos <= 1:
        return BusFactorClassification.CRITICO
    if quantidade_substitutos == 2:
        return BusFactorClassification.ATENCAO
    if quantidade_substitutos <= 4:
        return BusFactorClassification.ADEQUADO
    return BusFactorClassification.SEGURO


def calculate_mso(components: MatchComponents, config: MatchmakingConfig) -> float:
    score = (
        components.msc * config.peso_msc
        + components.nca * config.peso_nca
        + components.idp * config.peso_idp
        + components.icp * config.peso_icp
        + (100 - components.ioc) * config.peso_ioc_invertido
    )
    return round(clamp(score), 2)


def classify_match(score: float) -> MatchClassification:
    if score >= 90:
        return MatchClassification.EXCELENTE
    if score >= 75:
        return MatchClassification.BOM
    if score >= 60:
        return MatchClassification.ACEITAVEL
    return MatchClassification.NAO_RECOMENDADO


def classify_impact(ioc: float) -> OperationalImpact:
    if ioc >= 75:
        return OperationalImpact.CRITICO
    if ioc >= 50:
        return OperationalImpact.ALTO
    if ioc >= 25:
        return OperationalImpact.MEDIO
    return OperationalImpact.BAIXO


def evaluate_candidate(
    candidate: CandidateContext,
    requirements: list[SkillRequirement],
    destination_criticality: int,
    reference_date: date,
    config: MatchmakingConfig | None = None,
) -> CandidateEvaluation:
    config = config or MatchmakingConfig()
    blocks = _collect_blocks(
        candidate, requirements, destination_criticality, reference_date, config
    )
    components = MatchComponents(
        msc=calculate_msc(requirements, candidate, reference_date),
        nca=calculate_nca(requirements, candidate),
        idp=calculate_idp(candidate),
        icp=round(clamp(candidate.cobertura_pos_movimentacao), 2),
        ioc=calculate_ioc(
            candidate.criticidade_origem, candidate.quantidade_substitutos_origem
        ),
        bfo=classify_bus_factor(candidate.quantidade_substitutos_origem),
    )
    score = calculate_mso(components, config)
    return CandidateEvaluation(
        funcionario_id=candidate.funcionario_id,
        nome=candidate.nome,
        elegivel=not blocks,
        score=score,
        classificacao=classify_match(score),
        impacto=classify_impact(components.ioc),
        componentes=components,
        bloqueios=tuple(blocks),
        posto_origem_id=candidate.posto_origem_id,
        posto_origem_codigo=candidate.posto_origem_codigo,
    )


def _collect_blocks(
    candidate: CandidateContext,
    requirements: list[SkillRequirement],
    destination_criticality: int,
    reference_date: date,
    config: MatchmakingConfig,
) -> list[BlockReason]:
    blocks: list[BlockReason] = []
    if calculate_idp(candidate) < 100:
        blocks.append(BlockReason.INDISPONIVEL)

    for requirement in requirements:
        qualification = candidate.habilidades.get(requirement.habilidade_id)
        if qualification is None:
            blocks.append(BlockReason.HABILIDADE_OBRIGATORIA_AUSENTE)
        elif qualification.validade is not None and qualification.validade < reference_date:
            blocks.append(BlockReason.CAPACITACAO_VENCIDA)
        elif qualification.nivel < requirement.nivel_minimo:
            blocks.append(BlockReason.NIVEL_INSUFICIENTE)

    if (
        candidate.posto_origem_id is not None
        and candidate.criticidade_funcionario >= 4
        and candidate.quantidade_substitutos_origem <= 1
    ):
        blocks.append(BlockReason.PROFISSIONAL_CRITICO_SEM_BACKUP)
    if candidate.criticidade_origem > destination_criticality:
        blocks.append(BlockReason.ORIGEM_MAIS_CRITICA)
    if candidate.cobertura_pos_movimentacao < config.cobertura_minima:
        blocks.append(BlockReason.COBERTURA_ORIGEM_ABAIXO_DO_LIMITE)
    return list(dict.fromkeys(blocks))


def _qualification_meets(
    requirement: SkillRequirement, candidate: CandidateContext, reference_date: date
) -> bool:
    qualification = candidate.habilidades.get(requirement.habilidade_id)
    if qualification is None or qualification.nivel < requirement.nivel_minimo:
        return False
    return qualification.validade is None or qualification.validade >= reference_date

