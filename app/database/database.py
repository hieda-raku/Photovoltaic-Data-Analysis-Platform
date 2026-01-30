from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 数据库 URL 来自环境变量，若未设置则使用本地 PostgreSQL 默认值
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/photovoltaic_db"
)

# 创建 SQLAlchemy 引擎
engine = create_engine(DATABASE_URL)

# 创建 SessionLocal 类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建模型的 Base 基类
Base = declarative_base()


def get_db():
    """
    获取数据库会话的依赖函数。
    生成一个数据库会话，并在使用后关闭。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库表。
    创建模型中定义的所有表。
    """
    from app.models import measurement, system_config
    Base.metadata.create_all(bind=engine)
