"""add aliases table"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("palavra_chave", sa.String(100), nullable=False, unique=True),
        sa.Column("subgrupo_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["subgrupo_id"], ["subgrupos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_aliases_palavra_chave"), "aliases", ["palavra_chave"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_aliases_palavra_chave"), table_name="aliases")
    op.drop_table("aliases")
