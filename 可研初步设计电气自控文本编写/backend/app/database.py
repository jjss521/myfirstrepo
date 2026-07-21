# -*- coding: utf-8 -*-
"""SQLite 数据库连接与初始化（SQLAlchemy）。"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import DB_PATH

engine = create_engine(f'sqlite:///{DB_PATH}', connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """创建所有表（已存在则忽略）。"""
    import app.models  # noqa: F401  确保模型已注册
    Base.metadata.create_all(bind=engine)
