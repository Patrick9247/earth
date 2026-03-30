"""
数据库连接和会话管理
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# 确保数据库目录存在
if settings.USE_SQLITE:
    db_dir = os.path.dirname(settings.SQLITE_DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

# 创建数据库引擎
# SQLite 需要特殊的 connect_args
engine_args = {"pool_pre_ping": True, "pool_recycle": 3600, "echo": settings.DEBUG}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_args = {"echo": settings.DEBUG, "connect_args": {"check_same_thread": False}}

engine = create_engine(settings.DATABASE_URL, **engine_args)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """获取数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表"""
    # 确保目录存在
    if settings.USE_SQLITE:
        db_dir = os.path.dirname(settings.SQLITE_DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
