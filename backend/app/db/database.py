from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

db_path = Path(settings.database_url.replace("sqlite:///", ""))
db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_exchange_rule_columns()


def _migrate_exchange_rule_columns():
    """为现有 SQLite 数据库补充轻量字段，避免要求用户手动迁移。"""
    inspector = inspect(engine)
    if "exchange_rules" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("exchange_rules")}
    missing = {
        "store_name": "VARCHAR(100) NOT NULL DEFAULT ''",
        "city": "VARCHAR(100) NOT NULL DEFAULT ''",
    }
    with engine.begin() as connection:
        for name, definition in missing.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE exchange_rules ADD COLUMN {name} {definition}"))
