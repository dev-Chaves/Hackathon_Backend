"""Adiciona historicos variados de ausencia a uma equipe demonstrativa.

Revision ID: 20260815_0009
Revises: 20260815_0008
Create Date: 2026-08-15

Os colaboradores selecionados pertencem a Equipe L001 - Turno 1. A quantidade
gradual de eventos recentes faz o Motor 1 apresentar riscos baixo, medio e alto
sem alterar a regra de calculo.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0009"
down_revision: str | None = "20260815_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO historicos_ausencia (
                id, funcionario_id, data_ausencia, tipo, motivo, justificada
            )
            SELECT
                md5(
                    'absenteismo-variado-equipe-l001-t1-'
                    || dados.funcionario_n || '-' || evento.evento_n
                )::uuid,
                md5('automotiva-real-funcionario-' || dados.funcionario_n)::uuid,
                CURRENT_DATE - ((evento.evento_n * 2 + dados.funcionario_n) % 27),
                (ARRAY['FALTA', 'ATESTADO', 'LICENCA'])[
                    ((evento.evento_n - 1) % 3) + 1
                ]::tipo_ausencia,
                'Historico ficticio para demonstracao de risco de absenteismo.',
                evento.evento_n % 3 <> 1
            FROM (
                VALUES
                    (4, 2),
                    (5, 4),
                    (6, 6),
                    (7, 8),
                    (8, 10),
                    (9, 10),
                    (10, 10)
            ) AS dados(funcionario_n, total_ausencias)
            CROSS JOIN LATERAL generate_series(
                1, dados.total_ausencias
            ) AS evento(evento_n)
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM historicos_ausencia
            WHERE motivo = 'Historico ficticio para demonstracao de risco de absenteismo.'
              AND funcionario_id IN (
                  SELECT md5('automotiva-real-funcionario-' || n)::uuid
                  FROM generate_series(4, 10) AS funcionarios(n)
              )
            """
        )
    )
