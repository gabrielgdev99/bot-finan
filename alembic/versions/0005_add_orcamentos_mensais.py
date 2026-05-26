"""add orcamentos_mensais table"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "orcamentos_mensais",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("grupo_id", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Date(), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(["grupo_id"], ["grupos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("grupo_id", "mes"),
    )
    op.create_index(op.f("ix_orcamentos_mensais_grupo_id"), "orcamentos_mensais", ["grupo_id"])


def downgrade():
    op.drop_index(op.f("ix_orcamentos_mensais_grupo_id"), table_name="orcamentos_mensais")
    op.drop_table("orcamentos_mensais")
