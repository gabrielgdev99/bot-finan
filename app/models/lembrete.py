from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Lembrete(Base):
    __tablename__ = "lembretes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"), nullable=False, index=True)
    dia_vencimento: Mapped[int] = mapped_column(Integer, nullable=False)
    auto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    template: Mapped["Template"] = relationship(lazy="joined")
