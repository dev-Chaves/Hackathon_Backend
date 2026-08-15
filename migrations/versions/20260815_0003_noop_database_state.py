"""Reconhece estado atual do banco sem alterar schema.

Revision ID: 20260815_0003
Revises: 20260815_0002
Create Date: 2026-08-15
"""

from collections.abc import Sequence

revision: str = "20260815_0003"
down_revision: str | None = "20260815_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
