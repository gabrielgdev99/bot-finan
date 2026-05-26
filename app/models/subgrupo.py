from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Subgrupo(Base):
    __tablename__ = "subgrupos"

    id: Mapped[int] = mapped_column(primary_key=True)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("grupos.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    orcamento_mensal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )

    __table_args__ = (UniqueConstraint("grupo_id", "nome"),)

    grupo: Mapped["Grupo"] = relationship(back_populates="subgrupos")
    lancamentos: Mapped[list["Lancamento"]] = relationship(back_populates="subgrupo")
