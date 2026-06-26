import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

#DATABASE_URL = os.getenv(
#    "DATABASE_URL",
#    "postgresql://postgres:postgres@localhost:5432/plm_db"
#)
# 绕过环境变量，直接硬编码测试连接
DATABASE_URL = "postgresql://postgres:admin@localhost:5432/plm_db"
engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
