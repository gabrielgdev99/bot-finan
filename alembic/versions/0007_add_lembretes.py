"""add lembretes table"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lembretes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("dia_vencimento", sa.Integer(), nullable=False),
        sa.Column("auto", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["template_id"], ["templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lembretes_template_id"), "lembretes", ["template_id"])


def downgrade():
    op.drop_index(op.f("ix_lembretes_template_id"), table_name="lembretes")
    op.drop_table("lembretes")
