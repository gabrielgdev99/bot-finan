from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OrcamentoMensal(Base):
    __tablename__ = "orcamentos_mensais"

    id: Mapped[int] = mapped_column(primary_key=True)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("grupos.id"), nullable=False)
    mes: Mapped[date] = mapped_column(Date, nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    __table_args__ = (UniqueConstraint("grupo_id", "mes"),)

    grupo: Mapped["Grupo"] = relationship(back_populates="orcamentos_mensais")
