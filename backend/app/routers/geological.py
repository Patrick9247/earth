"""
地质层管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import GeologicalLayer
from ..schemas import (
    GeologicalLayerCreate,
    GeologicalLayerResponse,
    MessageResponse
)

router = APIRouter(prefix="/api/layers", tags=["地质层管理"])


@router.get("/", response_model=List[GeologicalLayerResponse])
async def get_layers(db: Session = Depends(get_db)):
    """获取所有地质层"""
    layers = db.query(GeologicalLayer).all()
    return layers


@router.get("/{layer_id}", response_model=GeologicalLayerResponse)
async def get_layer(layer_id: int, db: Session = Depends(get_db)):
    """获取单个地质层"""
    layer = db.query(GeologicalLayer).filter(GeologicalLayer.id == layer_id).first()
    if not layer:
        raise HTTPException(status_code=404, detail="地质层未找到")
    return layer


@router.post("/", response_model=GeologicalLayerResponse)
async def create_layer(layer: GeologicalLayerCreate, db: Session = Depends(get_db)):
    """创建地质层"""
    db_layer = GeologicalLayer(**layer.model_dump())
    db.add(db_layer)
    db.commit()
    db.refresh(db_layer)
    return db_layer


@router.put("/{layer_id}", response_model=GeologicalLayerResponse)
async def update_layer(
    layer_id: int,
    layer: GeologicalLayerCreate,
    db: Session = Depends(get_db)
):
    """更新地质层"""
    db_layer = db.query(GeologicalLayer).filter(GeologicalLayer.id == layer_id).first()
    if not db_layer:
        raise HTTPException(status_code=404, detail="地质层未找到")
    
    for key, value in layer.model_dump().items():
        setattr(db_layer, key, value)
    
    db.commit()
    db.refresh(db_layer)
    return db_layer


@router.delete("/{layer_id}", response_model=MessageResponse)
async def delete_layer(layer_id: int, db: Session = Depends(get_db)):
    """删除地质层"""
    db_layer = db.query(GeologicalLayer).filter(GeologicalLayer.id == layer_id).first()
    if not db_layer:
        raise HTTPException(status_code=404, detail="地质层未找到")
    
    db.delete(db_layer)
    db.commit()
    return MessageResponse(success=True, message="地质层删除成功")
