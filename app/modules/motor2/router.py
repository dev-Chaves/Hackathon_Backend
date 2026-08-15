from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.modules.motor2.batch_service import BatchMatchmakingService
from app.modules.motor2.exceptions import (
    ActiveAllocationNotFoundError,
    EmployeeNotFoundError,
)
from app.modules.motor2.schemas import (
    BatchPlanningResponse,
    MatchCandidateResponse,
    MatchComponentsResponse,
    MatchmakingRequest,
    MatchmakingResponse,
    MatchTargetResponse,
    PlannedSubstitutionResponse,
    SkillRequirementResponse,
)
from app.modules.motor2.service import MatchmakingService

router = APIRouter(tags=["motor2 - matchmaking"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"motor": "motor2", "status": "ready"}


@router.post(
    "/substituicoes/planejar-ausencias",
    response_model=BatchPlanningResponse,
    status_code=status.HTTP_200_OK,
)
async def plan_daily_absences(
    session: AsyncSession = Depends(get_session),
) -> BatchPlanningResponse:
    result = await BatchMatchmakingService(session).plan_daily_absences(date.today())
    return BatchPlanningResponse(
        data_referencia=result.data_referencia,
        total_ausentes=result.total_ausentes,
        total_cobertos=result.total_cobertos,
        total_sem_cobertura=result.total_sem_cobertura,
        substituicoes=[
            PlannedSubstitutionResponse(
                funcionario_ausente_id=item.funcionario_ausente_id,
                funcionario_ausente_nome=item.funcionario_ausente_nome,
                funcionario_substituto_id=item.funcionario_substituto_id,
                funcionario_substituto_nome=item.funcionario_substituto_nome,
                posto_destino_id=item.posto_destino_id,
                posto_destino_codigo=item.posto_destino_codigo,
                score=item.score,
                equipe_id=item.equipe_id,
                equipe_nome=item.equipe_nome,
                tech_lead_nome=item.tech_lead_nome,
                tech_lead_email=item.tech_lead_email,
            )
            for item in result.substituicoes
        ],
    )


@router.post(
    "/substituicoes/recomendar",
    response_model=MatchmakingResponse,
    status_code=status.HTTP_200_OK,
)
async def recommend_substitutes(
    payload: MatchmakingRequest,
    session: AsyncSession = Depends(get_session),
) -> MatchmakingResponse:
    service = MatchmakingService(session)
    try:
        result = await service.recommend_substitutes(
            funcionario_ausente_id=payload.funcionario_ausente_id,
            reference_date=date.today(),
            limit=payload.limit,
        )
    except EmployeeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ActiveAllocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    target = MatchTargetResponse(
        funcionario_ausente_id=result.alvo.funcionario_ausente_id,
        funcionario_ausente_nome=result.alvo.funcionario_ausente_nome,
        posto_id=result.alvo.posto_id,
        posto_codigo=result.alvo.posto_codigo,
        posto_nome=result.alvo.posto_nome,
        linha_id=result.alvo.linha_id,
        linha_nome=result.alvo.linha_nome,
        area_id=result.alvo.area_id,
        area_nome=result.alvo.area_nome,
        criticidade_destino=result.alvo.criticidade_destino,
        requisitos=[
            SkillRequirementResponse(
                habilidade_id=requirement.habilidade_id,
                nome=requirement.nome,
                nivel_minimo=requirement.nivel_minimo,
            )
            for requirement in result.alvo.requisitos
        ],
    )
    substitutes = [
        MatchCandidateResponse(
            posicao=position,
            funcionario_id=candidate.funcionario_id,
            nome=candidate.nome,
            score=candidate.score,
            classificacao=candidate.classificacao,
            impacto=candidate.impacto,
            componentes=MatchComponentsResponse(
                msc=candidate.componentes.msc,
                nca=candidate.componentes.nca,
                idp=candidate.componentes.idp,
                icp=candidate.componentes.icp,
                ioc=candidate.componentes.ioc,
                bfo=candidate.componentes.bfo,
            ),
            bloqueios=list(candidate.bloqueios),
            posto_origem_id=candidate.posto_origem_id,
            posto_origem_codigo=candidate.posto_origem_codigo,
        )
        for position, candidate in enumerate(result.ranking, start=1)
    ]
    return MatchmakingResponse(
        data_referencia=result.data_referencia,
        versao_algoritmo=result.versao_algoritmo,
        total_avaliados=result.total_avaliados,
        total_bloqueados=result.total_bloqueados,
        alvo=target,
        substitutos=substitutes,
    )
