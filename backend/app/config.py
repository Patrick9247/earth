"""
应用配置
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional

# 工作目录
WORKSPACE_PATH = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")

class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "地热流体资源建模系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "geothermal_db")
    
    # SQLite 作为备选数据库
    USE_SQLITE: bool = os.getenv("USE_SQLITE", "true").lower() == "true"
    # 开发环境使用项目目录，生产环境使用 /tmp
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", 
        f"{WORKSPACE_PATH}/data/geothermal.db" if os.getenv("COZE_PROJECT_ENV") == "DEV" else "/tmp/geothermal.db")
    
    # GemPy 配置
    GRID_RESOLUTION: int = 50  # 网格分辨率
    
    @property
    def DATABASE_URL(self) -> str:
        """数据库连接URL"""
        if self.USE_SQLITE:
            return f"sqlite:///{self.SQLITE_DB_PATH}"
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量


settings = Settings()
