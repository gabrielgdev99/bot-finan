from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Lancamento(Base):
    __tablename__ = "lancamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    criado_em: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    data_gasto: Mapped[date] = mapped_column(Date, nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("grupos.id"), nullable=False)
    subgrupo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cartao: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_pagamento: Mapped[date] = mapped_column(Date, nullable=False)
    hash_msg: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    grupo: Mapped["Grupo"] = relationship(back_populates="lancamentos")
