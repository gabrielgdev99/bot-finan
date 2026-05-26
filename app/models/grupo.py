from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Grupo(Base):
    __tablename__ = "grupos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    subgrupos: Mapped[list["Subgrupo"]] = relationship(back_populates="grupo")
    lancamentos: Mapped[list["Lancamento"]] = relationship(back_populates="grupo")
    orcamentos_mensais: Mapped[list["OrcamentoMensal"]] = relationship(back_populates="grupo")
