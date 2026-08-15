import os
from datetime import date

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import engine
from app.models.entities import Alocacao, Funcionario
from app.modules.motor2.service import MatchmakingService

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.prod,
    pytest.mark.skipif(
        os.getenv("RUN_PROD_TESTS") != "1",
        reason="Defina RUN_PROD_TESTS=1 para executar consultas somente-leitura no Neon.",
    ),
]


async def test_neon_schema_and_seed_have_expected_readable_data() -> None:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            await connection.execute(text("SET TRANSACTION READ ONLY"))
            employees = await connection.scalar(select(func.count(Funcionario.id)))
            allocations = await connection.scalar(select(func.count(Alocacao.id)))

            assert employees is not None and employees > 0
            assert allocations is not None and allocations > 0
        finally:
            await transaction.rollback()


async def test_motor2_builds_real_ranking_without_writing_to_neon() -> None:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            await connection.execute(text("SET TRANSACTION READ ONLY"))
            employee_id = await connection.scalar(
                select(Alocacao.funcionario_id)
                .where(Alocacao.ativo.is_(True))
                .order_by(Alocacao.created_at, Alocacao.id)
                .limit(1)
            )
            assert employee_id is not None

            session = AsyncSession(bind=connection, expire_on_commit=False)
            try:
                result = await MatchmakingService(session).recommend_substitutes(
                    employee_id,
                    reference_date=date.today(),
                    limit=3,
                )
            finally:
                await session.close()

            assert result.alvo.funcionario_ausente_id == employee_id
            assert result.total_avaliados > 0
            assert len(result.ranking) <= 3
            assert all(candidate.elegivel for candidate in result.ranking)
            if not result.ranking:
                assert result.total_bloqueados == result.total_avaliados
        finally:
            await transaction.rollback()


async def test_automotive_seed_has_ten_people_per_team_and_consistent_lines() -> None:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            await connection.execute(text("SET TRANSACTION READ ONLY"))
            distribution = (
                await connection.execute(
                    text(
                        """
                        SELECT MIN(total), MAX(total), COUNT(*)
                        FROM (
                            SELECT equipe_id, COUNT(*) AS total
                            FROM funcionarios
                            WHERE matricula LIKE 'AUT-%'
                            GROUP BY equipe_id
                        ) AS equipes
                        """
                    )
                )
            ).one()
            teams_per_line = await connection.scalar(
                text(
                    """
                    SELECT COUNT(*)
                    FROM (
                        SELECT linha_id
                        FROM equipes
                        WHERE nome LIKE 'Equipe L% - Turno %'
                        GROUP BY linha_id
                        HAVING COUNT(*) <> 3
                    ) AS invalidas
                    """
                )
            )
            inconsistent_allocations = await connection.scalar(
                text(
                    """
                    SELECT COUNT(*)
                    FROM funcionarios AS funcionario
                    JOIN equipes AS equipe ON equipe.id = funcionario.equipe_id
                    JOIN alocacoes AS alocacao
                      ON alocacao.funcionario_id = funcionario.id AND alocacao.ativo = true
                    JOIN postos AS posto ON posto.id = alocacao.posto_id
                    WHERE funcionario.matricula LIKE 'AUT-%'
                      AND equipe.linha_id IS DISTINCT FROM posto.linha_id
                    """
                )
            )
            summary = (
                await connection.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM funcionarios WHERE matricula LIKE 'AUT-%'),
                            (SELECT COUNT(*) FROM funcionarios WHERE matricula LIKE 'NISSA-%'),
                            (SELECT COUNT(*) FROM equipes
                             WHERE nome LIKE 'Equipe L% - Turno %'),
                            (SELECT COUNT(*) FROM linhas
                             WHERE nome LIKE 'Linha Automotiva L%'),
                            (SELECT COUNT(*) FROM postos WHERE codigo LIKE 'AUT-%')
                        """
                    )
                )
            ).one()

            assert distribution == (10, 10, 300)
            assert teams_per_line == 0
            assert inconsistent_allocations == 0
            assert summary == (3000, 0, 300, 100, 1000)
        finally:
            await transaction.rollback()
