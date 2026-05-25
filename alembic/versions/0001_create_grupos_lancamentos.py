"""create grupos e lancamentos

Revision ID: 0001
Revises:
Create Date: 2026-05-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "grupos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("orcamento_mensal", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )

    op.create_table(
        "lancamentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_gasto", sa.Date(), nullable=False),
        sa.Column("descricao", sa.String(length=200), nullable=False),
        sa.Column("valor", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("grupo_id", sa.Integer(), nullable=False),
        sa.Column("subgrupo", sa.String(length=100), nullable=True),
        sa.Column("cartao", sa.String(length=100), nullable=True),
        sa.Column("data_pagamento_cartao", sa.Date(), nullable=True),
        sa.Column("hash_msg", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["grupo_id"], ["grupos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hash_msg"),
    )
    op.create_index("ix_lancamentos_hash_msg", "lancamentos", ["hash_msg"])


def downgrade() -> None:
    op.drop_index("ix_lancamentos_hash_msg", table_name="lancamentos")
    op.drop_table("lancamentos")
    op.drop_table("grupos")
