"""Adiciona controle de presenca diaria ao funcionario.

Revision ID: 20260815_0004
Revises: 20260815_0003
Create Date: 2026-08-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0004"
down_revision: str | None = "20260815_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "funcionarios",
        sa.Column(
            "presenca_diaria",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("funcionarios", "presenca_diaria")
