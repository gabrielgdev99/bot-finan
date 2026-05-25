"""rename data_pagamento_cartao to data_pagamento e torna not null

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # preenche valores nulos com data_gasto antes de tornar not null
    op.execute("UPDATE lancamentos SET data_pagamento_cartao = data_gasto WHERE data_pagamento_cartao IS NULL")
    op.alter_column("lancamentos", "data_pagamento_cartao", new_column_name="data_pagamento", nullable=False)


def downgrade() -> None:
    op.alter_column("lancamentos", "data_pagamento", new_column_name="data_pagamento_cartao", nullable=True)
