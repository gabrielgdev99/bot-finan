from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subgrupo_id: Mapped[int] = mapped_column(ForeignKey("subgrupos.id"), nullable=False)
    cartao: Mapped[str | None] = mapped_column(String(100), nullable=True)

    subgrupo: Mapped["Subgrupo"] = relationship()
