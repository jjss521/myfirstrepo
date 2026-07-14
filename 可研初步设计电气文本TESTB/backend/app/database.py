from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL
import os

# 确保data目录存在
os.makedirs(os.path.dirname(DATABASE_URL.replace('sqlite:///', '')), exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库表"""
    from .models import Base
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
