"""Acesso a dados da previsao de absenteismo."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Equipe, Funcionario
from app.modules.motor1.domain import AusenciaHistorica, FuncionarioAbsenteismoInput


class Motor1Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def buscar_absenteismo_por_equipe_numero(
        self,
        equipe_numero: int,
    ) -> tuple[str, tuple[FuncionarioAbsenteismoInput, ...]] | None:
        nome_nissa = f"Nissa - Equipe {equipe_numero:02d}"
        prefixo_linha = f"Equipe L{equipe_numero:03d} - Turno "
        result = await self._session.execute(
            select(Equipe)
            .where(
                or_(
                    Equipe.nome == nome_nissa,
                    Equipe.nome.like(f"{prefixo_linha}%"),
                )
            )
            .options(
                selectinload(Equipe.funcionarios).selectinload(Funcionario.ausencias),
            )
            .order_by(Equipe.nome)
        )
        equipes = tuple(result.scalars().all())
        if not equipes:
            return None

        funcionarios = tuple(
            FuncionarioAbsenteismoInput(
                id=str(funcionario.id),
                matricula=funcionario.matricula,
                nome=funcionario.nome,
                turno=funcionario.turno,
                status=funcionario.status.value,
                distancia_trabalho_km=float(funcionario.distancia_trabalho_km),
                tempo_deslocamento_min=funcionario.tempo_deslocamento_min,
                tipo_transporte=funcionario.tipo_transporte,
                ausencias=tuple(
                    AusenciaHistorica(ausencia.data_ausencia)
                    for ausencia in funcionario.ausencias
                ),
            )
            for funcionario in sorted(
                (funcionario for equipe in equipes for funcionario in equipe.funcionarios),
                key=lambda item: item.nome,
            )
        )
        nome_equipe = f"Equipe L{equipe_numero:03d}" if len(equipes) > 1 else equipes[0].nome
        return nome_equipe, funcionarios
