"""
网格计算表单数据管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from ..database import get_db
from ..models import GridCalculation, GridItem
from ..schemas import (
    GridCalculationFormCreate,
    GridCalculationFormUpdate,
    GridCalculationFormResponse,
    GridItemCreate,
    GridItemUpdate,
    GridItemResponse,
    MessageResponse
)

router = APIRouter(prefix="/api/grid-calculations", tags=["网格计算表单"])
logger = logging.getLogger(__name__)


# ==================== 计算表单 CRUD ====================
@router.get("/", response_model=List[GridCalculationFormResponse])
async def get_all_grid_calculations(db: Session = Depends(get_db)):
    """获取所有网格计算表单"""
    results = db.query(GridCalculation).order_by(GridCalculation.updated_at.desc().nullslast(), GridCalculation.created_at.desc()).all()
    return results


@router.get("/{calc_id}", response_model=GridCalculationFormResponse)
async def get_grid_calculation(calc_id: int, db: Session = Depends(get_db)):
    """获取单个网格计算表单"""
    result = db.query(GridCalculation).filter(GridCalculation.id == calc_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="网格计算表单未找到")
    return result


@router.post("/", response_model=GridCalculationFormResponse)
async def create_grid_calculation(
    request: GridCalculationFormCreate,
    db: Session = Depends(get_db)
):
    """创建网格计算表单"""
    db_calc = GridCalculation(
        name=request.name,
        reference_temperature=request.reference_temperature,
        recovery_factor=request.recovery_factor,
        utilization_efficiency=request.utilization_efficiency,
        lifetime_years=request.lifetime_years
    )
    db.add(db_calc)
    db.commit()
    db.refresh(db_calc)
    return db_calc


@router.put("/{calc_id}", response_model=GridCalculationFormResponse)
async def update_grid_calculation(
    calc_id: int,
    request: GridCalculationFormUpdate,
    db: Session = Depends(get_db)
):
    """更新网格计算表单"""
    db_calc = db.query(GridCalculation).filter(GridCalculation.id == calc_id).first()
    if not db_calc:
        raise HTTPException(status_code=404, detail="网格计算表单未找到")
    
    if request.name is not None:
        db_calc.name = request.name
    if request.reference_temperature is not None:
        db_calc.reference_temperature = request.reference_temperature
    if request.recovery_factor is not None:
        db_calc.recovery_factor = request.recovery_factor
    if request.utilization_efficiency is not None:
        db_calc.utilization_efficiency = request.utilization_efficiency
    if request.lifetime_years is not None:
        db_calc.lifetime_years = request.lifetime_years
    
    db.commit()
    db.refresh(db_calc)
    return db_calc


@router.delete("/{calc_id}", response_model=MessageResponse)
async def delete_grid_calculation(calc_id: int, db: Session = Depends(get_db)):
    """删除网格计算表单（同时删除关联的网格）"""
    db_calc = db.query(GridCalculation).filter(GridCalculation.id == calc_id).first()
    if not db_calc:
        raise HTTPException(status_code=404, detail="网格计算表单未找到")
    
    # 删除关联的网格
    db.query(GridItem).filter(GridItem.calc_id == calc_id).delete()
    
    db.delete(db_calc)
    db.commit()
    return MessageResponse(success=True, message="删除成功")


# ==================== 网格数据 CRUD ====================
@router.get("/{calc_id}/grids", response_model=List[GridItemResponse])
async def get_grids_by_calc(calc_id: int, db: Session = Depends(get_db)):
    """获取指定计算的所有网格"""
    grids = db.query(GridItem).filter(GridItem.calc_id == calc_id).order_by(GridItem.sort_order).all()
    return grids


@router.post("/{calc_id}/grids", response_model=GridItemResponse)
async def create_grid_item(
    calc_id: int,
    request: GridItemCreate,
    db: Session = Depends(get_db)
):
    """为指定计算添加网格"""
    # 检查计算是否存在
    calc = db.query(GridCalculation).filter(GridCalculation.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="网格计算表单未找到")
    
    db_item = GridItem(
        calc_id=calc_id,
        grid_count=request.grid_count,
        porosity=request.porosity,
        volume=request.volume,
        temperature=request.temperature,
        pressure=request.pressure,
        sort_order=request.sort_order or 0
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/{calc_id}/grids/{item_id}", response_model=GridItemResponse)
async def update_grid_item(
    calc_id: int,
    item_id: int,
    request: GridItemUpdate,
    db: Session = Depends(get_db)
):
    """更新网格"""
    db_item = db.query(GridItem).filter(GridItem.id == item_id, GridItem.calc_id == calc_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="网格未找到")
    
    if request.grid_count is not None:
        db_item.grid_count = request.grid_count
    if request.porosity is not None:
        db_item.porosity = request.porosity
    if request.volume is not None:
        db_item.volume = request.volume
    if request.temperature is not None:
        db_item.temperature = request.temperature
    if request.pressure is not None:
        db_item.pressure = request.pressure
    if request.sort_order is not None:
        db_item.sort_order = request.sort_order
    
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{calc_id}/grids/{item_id}", response_model=MessageResponse)
async def delete_grid_item(
    calc_id: int,
    item_id: int,
    db: Session = Depends(get_db)
):
    """删除网格"""
    db_item = db.query(GridItem).filter(GridItem.id == item_id, GridItem.calc_id == calc_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="网格未找到")
    
    db.delete(db_item)
    db.commit()
    return MessageResponse(success=True, message="删除成功")
