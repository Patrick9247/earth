"""
网格计算表单数据管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from ..database import get_db
from ..models import GridCalculation
from ..schemas import (
    GridCalculationFormCreate,
    GridCalculationFormUpdate,
    GridCalculationFormResponse,
    MessageResponse
)

router = APIRouter(prefix="/api/grid-calculations", tags=["网格计算表单"])
logger = logging.getLogger(__name__)


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
        lifetime_years=request.lifetime_years,
        grids=request.grids
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
    
    # 更新字段
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
    if request.grids is not None:
        db_calc.grids = request.grids
    
    db.commit()
    db.refresh(db_calc)
    return db_calc


@router.delete("/{calc_id}", response_model=MessageResponse)
async def delete_grid_calculation(calc_id: int, db: Session = Depends(get_db)):
    """删除网格计算表单"""
    db_calc = db.query(GridCalculation).filter(GridCalculation.id == calc_id).first()
    if not db_calc:
        raise HTTPException(status_code=404, detail="网格计算表单未找到")
    
    db.delete(db_calc)
    db.commit()
    return MessageResponse(success=True, message="删除成功")
