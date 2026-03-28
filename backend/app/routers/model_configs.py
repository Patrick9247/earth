"""
模型配置管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import ModelConfig
from ..schemas import (
    ModelConfigCreate,
    ModelConfigResponse,
    MessageResponse
)

router = APIRouter(prefix="/api/model-configs", tags=["模型配置管理"])


@router.get("/", response_model=List[ModelConfigResponse])
async def get_configs(db: Session = Depends(get_db)):
    """获取所有模型配置"""
    configs = db.query(ModelConfig).all()
    return configs


@router.get("/{config_id}", response_model=ModelConfigResponse)
async def get_config(config_id: int, db: Session = Depends(get_db)):
    """获取单个模型配置"""
    config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="模型配置未找到")
    return config


@router.post("/", response_model=ModelConfigResponse)
async def create_config(config: ModelConfigCreate, db: Session = Depends(get_db)):
    """创建模型配置"""
    db_config = ModelConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.put("/{config_id}", response_model=ModelConfigResponse)
async def update_config(
    config_id: int,
    config: ModelConfigCreate,
    db: Session = Depends(get_db)
):
    """更新模型配置"""
    db_config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="模型配置未找到")
    
    for key, value in config.model_dump().items():
        setattr(db_config, key, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config


@router.delete("/{config_id}", response_model=MessageResponse)
async def delete_config(config_id: int, db: Session = Depends(get_db)):
    """删除模型配置"""
    db_config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="模型配置未找到")
    
    db.delete(db_config)
    db.commit()
    return MessageResponse(success=True, message="模型配置删除成功")
