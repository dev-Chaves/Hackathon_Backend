"""Adiciona tech leads e reservas concorrentes de substituicao.

Revision ID: 20260815_0008
Revises: 20260815_0007
Create Date: 2026-08-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0008"
down_revision: str | None = "20260815_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("equipes", sa.Column("tech_lead_nome", sa.String(180), nullable=True))
    op.add_column("equipes", sa.Column("tech_lead_email", sa.String(255), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE equipes
            SET
                tech_lead_nome = 'Tech Lead ' || nome,
                tech_lead_email = lower(
                    regexp_replace(nome, '[^A-Za-z0-9]+', '.', 'g')
                ) || '@automotiva.example'
            WHERE nome LIKE 'Equipe L% - Turno %'
            """
        )
    )

    op.create_table(
        "substituicoes_planejadas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("data_referencia", sa.Date(), nullable=False),
        sa.Column("funcionario_ausente_id", sa.UUID(), nullable=False),
        sa.Column("funcionario_substituto_id", sa.UUID(), nullable=False),
        sa.Column("posto_destino_id", sa.UUID(), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["funcionario_ausente_id"],
            ["funcionarios.id"],
            name="fk_substituicoes_planejadas_ausente",
        ),
        sa.ForeignKeyConstraint(
            ["funcionario_substituto_id"],
            ["funcionarios.id"],
            name="fk_substituicoes_planejadas_substituto",
        ),
        sa.ForeignKeyConstraint(
            ["posto_destino_id"],
            ["postos.id"],
            name="fk_substituicoes_planejadas_posto",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_substituicoes_planejadas"),
        sa.UniqueConstraint(
            "data_referencia",
            "funcionario_ausente_id",
            name="uq_substituicoes_planejadas_data_ausente",
        ),
        sa.UniqueConstraint(
            "data_referencia",
            "funcionario_substituto_id",
            name="uq_substituicoes_planejadas_data_substituto",
        ),
    )
    op.create_index(
        "ix_substituicoes_planejadas_data",
        "substituicoes_planejadas",
        ["data_referencia"],
    )
    op.create_index(
        "ix_substituicoes_planejadas_funcionario_ausente_id",
        "substituicoes_planejadas",
        ["funcionario_ausente_id"],
    )
    op.create_index(
        "ix_substituicoes_planejadas_funcionario_substituto_id",
        "substituicoes_planejadas",
        ["funcionario_substituto_id"],
    )
    op.create_index(
        "ix_substituicoes_planejadas_posto_destino_id",
        "substituicoes_planejadas",
        ["posto_destino_id"],
    )


def downgrade() -> None:
    op.drop_table("substituicoes_planejadas")
    op.drop_column("equipes", "tech_lead_email")
    op.drop_column("equipes", "tech_lead_nome")
