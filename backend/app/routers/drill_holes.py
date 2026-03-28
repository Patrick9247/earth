"""
钻孔数据管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import DrillHole
from ..schemas import (
    DrillHoleCreate,
    DrillHoleResponse,
    MessageResponse
)

router = APIRouter(prefix="/api/drill-holes", tags=["钻孔数据管理"])


@router.get("/", response_model=List[DrillHoleResponse])
async def get_drill_holes(db: Session = Depends(get_db)):
    """获取所有钻孔数据"""
    drill_holes = db.query(DrillHole).all()
    return drill_holes


@router.get("/{drill_hole_id}", response_model=DrillHoleResponse)
async def get_drill_hole(drill_hole_id: int, db: Session = Depends(get_db)):
    """获取单个钻孔数据"""
    drill_hole = db.query(DrillHole).filter(DrillHole.id == drill_hole_id).first()
    if not drill_hole:
        raise HTTPException(status_code=404, detail="钻孔数据未找到")
    return drill_hole


@router.post("/", response_model=DrillHoleResponse)
async def create_drill_hole(drill_hole: DrillHoleCreate, db: Session = Depends(get_db)):
    """创建钻孔数据"""
    db_drill_hole = DrillHole(**drill_hole.model_dump())
    db.add(db_drill_hole)
    db.commit()
    db.refresh(db_drill_hole)
    return db_drill_hole


@router.post("/batch", response_model=List[DrillHoleResponse])
async def create_drill_holes_batch(
    drill_holes: List[DrillHoleCreate],
    db: Session = Depends(get_db)
):
    """批量创建钻孔数据"""
    db_drill_holes = [DrillHole(**dh.model_dump()) for dh in drill_holes]
    db.add_all(db_drill_holes)
    db.commit()
    return db_drill_holes


@router.put("/{drill_hole_id}", response_model=DrillHoleResponse)
async def update_drill_hole(
    drill_hole_id: int,
    drill_hole: DrillHoleCreate,
    db: Session = Depends(get_db)
):
    """更新钻孔数据"""
    db_drill_hole = db.query(DrillHole).filter(DrillHole.id == drill_hole_id).first()
    if not db_drill_hole:
        raise HTTPException(status_code=404, detail="钻孔数据未找到")
    
    for key, value in drill_hole.model_dump().items():
        setattr(db_drill_hole, key, value)
    
    db.commit()
    db.refresh(db_drill_hole)
    return db_drill_hole


@router.delete("/{drill_hole_id}", response_model=MessageResponse)
async def delete_drill_hole(drill_hole_id: int, db: Session = Depends(get_db)):
    """删除钻孔数据"""
    db_drill_hole = db.query(DrillHole).filter(DrillHole.id == drill_hole_id).first()
    if not db_drill_hole:
        raise HTTPException(status_code=404, detail="钻孔数据未找到")
    
    db.delete(db_drill_hole)
    db.commit()
    return MessageResponse(success=True, message="钻孔数据删除成功")
