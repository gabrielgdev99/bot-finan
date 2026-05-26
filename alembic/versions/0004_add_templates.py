"""add templates table"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False, unique=True),
        sa.Column("descricao", sa.String(200), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("subgrupo_id", sa.Integer(), nullable=False),
        sa.Column("cartao", sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(["subgrupo_id"], ["subgrupos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_templates_nome"), "templates", ["nome"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_templates_nome"), table_name="templates")
    op.drop_table("templates")
