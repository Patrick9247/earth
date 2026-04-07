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
    DrillHoleWithDetailsCreate,
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
    
    # 为每个钻孔添加平均温度
    result = []
    for dh in drill_holes:
        dh_dict = {
            "id": dh.id,
            "hole_id": dh.hole_id,
            "hole_name": dh.hole_name,
            "location_x": dh.location_x,
            "location_y": dh.location_y,
            "elevation": dh.elevation,
            "total_depth": dh.total_depth,
            "final_depth": dh.final_depth,
            "diameter": dh.diameter,
            "drill_company": dh.drill_company,
            "drill_start_date": dh.drill_start_date,
            "drill_end_date": dh.drill_end_date,
            "status": dh.status,
            "description": dh.description,
            "created_at": dh.created_at,
            "updated_at": dh.updated_at,
        }
        
        # 获取温度数据并计算平均温度
        temp_data = db.query(DrillTemperatureCurve).filter(
            DrillTemperatureCurve.drill_hole_id == dh.id
        ).all()
        
        if temp_data:
            temps = [t.corrected_temp or t.temperature for t in temp_data if t.corrected_temp or t.temperature]
            if temps:
                dh_dict["temperature"] = sum(temps) / len(temps)
            else:
                # 根据深度估算温度 (假设地温梯度 30°C/km，地表温度 15°C)
                dh_dict["temperature"] = 15 + (dh.total_depth or 500) * 0.03
        else:
            # 没有温度数据时，根据深度估算
            dh_dict["temperature"] = 15 + (dh.total_depth or 500) * 0.03
        
        result.append(dh_dict)
    
    return result


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


@router.post("/with-details")
async def create_drill_hole_with_details(data: DrillHoleWithDetailsCreate, db: Session = Depends(get_db)):
    """创建钻孔及其关联数据（分层、测温、压力、孔隙度）"""
    # 检查hole_id是否已存在
    existing = db.query(DrillHole).filter(DrillHole.hole_id == data.drill_hole.hole_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"钻孔编号 {data.drill_hole.hole_id} 已存在")
    
    # 创建钻孔基本信息
    db_drill_hole = DrillHole(**data.drill_hole.model_dump())
    db.add(db_drill_hole)
    db.commit()
    db.refresh(db_drill_hole)
    
    drill_hole_id = db_drill_hole.id
    
    # 创建分层数据
    if data.layers:
        for layer_data in data.layers:
            layer_data["drill_hole_id"] = drill_hole_id
            # 计算厚度
            if "depth_top" in layer_data and "depth_bottom" in layer_data:
                layer_data["thickness"] = layer_data["depth_bottom"] - layer_data["depth_top"]
            db_layer = DrillLayer(**layer_data)
            db.add(db_layer)
    
    # 创建测温数据
    if data.temperature_curves:
        for temp_data in data.temperature_curves:
            temp_data["drill_hole_id"] = drill_hole_id
            db_temp = DrillTemperatureCurve(**temp_data)
            db.add(db_temp)
    
    # 创建压力数据
    if data.pressure_data:
        for pressure_data in data.pressure_data:
            pressure_data["drill_hole_id"] = drill_hole_id
            db_pressure = DrillPressureData(**pressure_data)
            db.add(db_pressure)
    
    # 创建孔隙度数据
    if data.porosity_data:
        for porosity_data in data.porosity_data:
            porosity_data["drill_hole_id"] = drill_hole_id
            db_porosity = DrillPorosityData(**porosity_data)
            db.add(db_porosity)
    
    db.commit()
    db.refresh(db_drill_hole)
    
    return {
        "success": True,
        "message": "钻孔及其关联数据创建成功",
        "drill_hole": db_drill_hole
    }


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
