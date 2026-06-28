import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 自动读取同级目录下的 .env 文件
load_dotenv()

# 从环境变中获取刚刚填入的云端数据库链接
DATABASE_URL = os.getenv("DATABASE_URL")

# 建立数据库连接
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()