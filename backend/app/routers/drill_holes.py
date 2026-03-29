"""
钻孔数据管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import DrillHole, DrillLayer, DrillTemperatureCurve, DrillPressureData, DrillPorosityData
from ..schemas import (
    DrillHoleCreate,
    DrillHoleResponse,
    MessageResponse
)

router = APIRouter(prefix="/api/drill-holes", tags=["钻孔数据管理"])


@router.get("/", response_model=List[DrillHoleResponse])
async def get_drill_holes(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """获取所有钻孔数据"""
    drill_holes = db.query(DrillHole).offset(skip).limit(limit).all()
    return drill_holes


@router.get("/{drill_hole_id}", response_model=DrillHoleResponse)
async def get_drill_hole(drill_hole_id: int, db: Session = Depends(get_db)):
    """获取单个钻孔数据"""
    drill_hole = db.query(DrillHole).filter(DrillHole.id == drill_hole_id).first()
    if not drill_hole:
        raise HTTPException(status_code=404, detail="钻孔数据未找到")
    return drill_hole


@router.get("/{drill_hole_id}/detail")
async def get_drill_hole_detail(drill_hole_id: int, db: Session = Depends(get_db)):
    """获取钻孔详细信息，包含关联数据"""
    drill_hole = db.query(DrillHole).filter(DrillHole.id == drill_hole_id).first()
    if not drill_hole:
        raise HTTPException(status_code=404, detail="钻孔数据未找到")
    
    return {
        "drill_hole": drill_hole,
        "layers": db.query(DrillLayer).filter(DrillLayer.drill_hole_id == drill_hole_id).all(),
        "temperature_curves": db.query(DrillTemperatureCurve).filter(DrillTemperatureCurve.drill_hole_id == drill_hole_id).order_by(DrillTemperatureCurve.depth).all(),
        "pressure_data": db.query(DrillPressureData).filter(DrillPressureData.drill_hole_id == drill_hole_id).all(),
        "porosity_data": db.query(DrillPorosityData).filter(DrillPorosityData.drill_hole_id == drill_hole_id).all()
    }


@router.post("/", response_model=DrillHoleResponse)
async def create_drill_hole(drill_hole: DrillHoleCreate, db: Session = Depends(get_db)):
    """创建钻孔数据"""
    # 检查hole_id是否已存在
    existing = db.query(DrillHole).filter(DrillHole.hole_id == drill_hole.hole_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"钻孔编号 {drill_hole.hole_id} 已存在")
    
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
    db_drill_holes = []
    for dh in drill_holes:
        existing = db.query(DrillHole).filter(DrillHole.hole_id == dh.hole_id).first()
        if not existing:
            db_drill_holes.append(DrillHole(**dh.model_dump()))
    
    if db_drill_holes:
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
