"""Banco de dados: usuários e histórico de análises (SQLAlchemy).

Sem DATABASE_URL, usa um SQLite em data/edupredict.db (bom para desenvolvimento).
Em produção, use um Postgres (ex.: o gratuito do Render) definindo DATABASE_URL.

As tabelas são criadas na subida da API (create_all). Se o modelo das tabelas mudar,
apague o SQLite local ou crie a coluna nova no Postgres.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


def _agora() -> datetime:
    return datetime.now(UTC)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    cargo: Mapped[str] = mapped_column(String(120), default="")
    senha_hash: Mapped[str] = mapped_column(String(300))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class Analise(Base):
    """Uma previsão feita por um usuário. Guarda o perfil (sem nome do aluno) e o resultado."""

    __tablename__ = "analises"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora, index=True)
    perfil: Mapped[dict] = mapped_column(JSON)
    previsao: Mapped[dict] = mapped_column(JSON)
    probabilidade: Mapped[float] = mapped_column(Float)
    nivel: Mapped[str] = mapped_column(String(10))
    acompanhamento: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    modelo: Mapped[str] = mapped_column(String(60))


class Banco:
    def __init__(self, url: str):
        argumentos = {}
        if url.startswith("sqlite:///"):
            Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
            argumentos["connect_args"] = {"check_same_thread": False}
        self.engine: Engine = create_engine(url, pool_pre_ping=True, **argumentos)
        self.sessao = sessionmaker(self.engine, expire_on_commit=False)

    def criar_tabelas(self) -> None:
        Base.metadata.create_all(self.engine)

    def criar_usuario_inicial(self, email: str, senha: str, nome: str, cargo: str = "Coordenação pedagógica") -> None:
        """Cria o primeiro usuário se o banco ainda não tiver nenhum."""
        from .auth import gerar_hash

        with self.sessao() as s:
            if s.scalar(select(Usuario.id).limit(1)) is None:
                s.add(Usuario(nome=nome, email=email.lower(), cargo=cargo, senha_hash=gerar_hash(senha)))
                s.commit()

    def abrir(self) -> Session:
        return self.sessao()
