from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.modules.motor1.exceptions import EquipeNaoEncontradaError
from app.modules.motor1.repository import Motor1Repository
from app.modules.motor1.schemas import PrevisaoAbsenteismoEquipeResponse
from app.modules.motor1.service import Motor1Service

router = APIRouter(tags=["motor1 - previsao de absenteismo"])


@router.get(
    "/previsao-absenteismo/equipe/{equipe_numero}",
    response_model=PrevisaoAbsenteismoEquipeResponse,
)
async def prever_absenteismo_por_equipe(
    equipe_numero: int = Path(ge=1),
    data_referencia: date | None = None,
    session: AsyncSession = Depends(get_session),
) -> PrevisaoAbsenteismoEquipeResponse:
    service = Motor1Service(Motor1Repository(session))
    try:
        resultado = await service.prever_absenteismo_por_equipe(
            equipe_numero=equipe_numero,
            data_referencia=data_referencia or date.today(),
        )
    except EquipeNaoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PrevisaoAbsenteismoEquipeResponse.model_validate(resultado)
