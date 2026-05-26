from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Alias(Base):
    __tablename__ = "aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    palavra_chave: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    subgrupo_id: Mapped[int] = mapped_column(ForeignKey("subgrupos.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    subgrupo: Mapped["Subgrupo"] = relationship()
