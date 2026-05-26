"""add subgrupos table and migrate data"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "subgrupos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("grupo_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column(
            "orcamento_mensal",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
        sa.ForeignKeyConstraint(["grupo_id"], ["grupos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("grupo_id", "nome"),
    )

    op.execute(
        """
        INSERT INTO subgrupos (grupo_id, nome, orcamento_mensal)
        SELECT DISTINCT grupo_id, subgrupo, 0
        FROM lancamentos
        WHERE subgrupo IS NOT NULL
        """
    )

    op.add_column(
        "lancamentos",
        sa.Column("subgrupo_id", sa.Integer(), nullable=True),
    )

    op.execute(
        """
        UPDATE lancamentos
        SET subgrupo_id = (
            SELECT id
            FROM subgrupos
            WHERE grupo_id = lancamentos.grupo_id
            AND nome = lancamentos.subgrupo
        )
        WHERE subgrupo IS NOT NULL
        """
    )

    op.alter_column(
        "lancamentos",
        "subgrupo_id",
        nullable=False,
        existing_type=sa.Integer(),
        existing_nullable=True,
    )

    op.create_foreign_key(
        "fk_lancamentos_subgrupo_id",
        "lancamentos",
        "subgrupos",
        ["subgrupo_id"],
        ["id"],
    )

    op.drop_column("lancamentos", "subgrupo")

    op.drop_column("grupos", "orcamento_mensal")


def downgrade():
    op.add_column(
        "grupos",
        sa.Column(
            "orcamento_mensal",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "lancamentos",
        sa.Column("subgrupo", sa.String(100), nullable=True),
    )

    op.execute(
        """
        UPDATE lancamentos
        SET subgrupo = (
            SELECT nome
            FROM subgrupos
            WHERE id = lancamentos.subgrupo_id
        )
        """
    )

    op.drop_constraint("fk_lancamentos_subgrupo_id", "lancamentos", type_="foreignkey")

    op.drop_column("lancamentos", "subgrupo_id")

    op.drop_table("subgrupos")
