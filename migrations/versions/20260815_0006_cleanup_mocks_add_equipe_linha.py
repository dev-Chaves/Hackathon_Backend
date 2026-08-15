"""Remove mocks antigos e vincula equipes a linhas.

Revision ID: 20260815_0006
Revises: 20260815_0005
Create Date: 2026-08-15

A limpeza e intencional e irreversivel: o downgrade remove apenas a coluna adicionada, sem
restaurar os registros ficticios descartados.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0006"
down_revision: str | None = "20260815_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM alocacoes
            WHERE funcionario_id IN (
                SELECT id FROM funcionarios WHERE matricula LIKE 'NISSA-%'
            )
            OR posto_id IN (
                SELECT id FROM postos WHERE codigo LIKE 'NIS-%'
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM historicos_ausencia
            WHERE funcionario_id IN (
                SELECT id FROM funcionarios WHERE matricula LIKE 'NISSA-%'
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM funcionarios_habilidades
            WHERE funcionario_id IN (
                SELECT id FROM funcionarios WHERE matricula LIKE 'NISSA-%'
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM postos_habilidades
            WHERE posto_id IN (
                SELECT id FROM postos WHERE codigo LIKE 'NIS-%'
            )
            """
        )
    )
    op.execute(sa.text("DELETE FROM funcionarios WHERE matricula LIKE 'NISSA-%'"))
    op.execute(sa.text("DELETE FROM postos WHERE codigo LIKE 'NIS-%'"))
    op.execute(
        sa.text(
            """
            DELETE FROM linhas AS linha
            WHERE linha.nome LIKE 'Nissa - %'
              AND NOT EXISTS (SELECT 1 FROM postos WHERE linha_id = linha.id)
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM equipes AS equipe
            WHERE equipe.nome LIKE 'Nissa%'
              AND NOT EXISTS (SELECT 1 FROM funcionarios WHERE equipe_id = equipe.id)
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM areas AS area
            WHERE area.nome LIKE 'Nissa - %'
              AND NOT EXISTS (SELECT 1 FROM funcionarios WHERE area_id = area.id)
              AND NOT EXISTS (SELECT 1 FROM linhas WHERE area_id = area.id)
            """
        )
    )

    op.add_column(
        "equipes",
        sa.Column("linha_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_equipes_linha_id_linhas",
        "equipes",
        "linhas",
        ["linha_id"],
        ["id"],
    )
    op.create_index("ix_equipes_linha_id", "equipes", ["linha_id"])


def downgrade() -> None:
    op.drop_index("ix_equipes_linha_id", table_name="equipes")
    op.drop_constraint("fk_equipes_linha_id_linhas", "equipes", type_="foreignkey")
    op.drop_column("equipes", "linha_id")
