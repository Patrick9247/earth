"""
应用配置
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""
    
    # pydantic-settings 配置（兼容新旧版本）
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # 忽略未定义的环境变量
    )

    # 应用基础配置
    APP_NAME: str = "地热流体资源建模系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "root")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "earthheat")
    
    # SQLite 作为备选数据库
    USE_SQLITE: bool = True  # 设为False启用MySQL
    SQLITE_DB_PATH: str = ""
    
    # GemPy 配置
    GRID_RESOLUTION: int = 50  # 网格分辨率
    
    # 环境变量（显式定义避免验证错误）
    COZE_WORKSPACE_PATH: str = ""
    COZE_PROJECT_ENV: str = "DEV"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 动态设置 SQLite 数据库路径
        if not self.SQLITE_DB_PATH:
            workspace = self.COZE_WORKSPACE_PATH or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if self.COZE_PROJECT_ENV == "DEV":
                self.SQLITE_DB_PATH = f"{workspace}/data/geothermal.db"
            else:
                self.SQLITE_DB_PATH = "/tmp/geothermal.db"

    @property
    def DATABASE_URL(self) -> str:
        """数据库连接URL"""
        if self.USE_SQLITE:
            return f"sqlite:///{self.SQLITE_DB_PATH}"
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"


settings = Settings()
