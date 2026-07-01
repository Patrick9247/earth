"""
GemPy 建模和地热资源计算 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from ..database import get_db
from ..models import GeothermalResource
from ..schemas import (
    GemPyModelRequest,
    GemPyModelResponse,
    GeothermalCalculationRequest,
    GeothermalCalculationResponse,
    GeothermalResourceResponse,
    GeothermalResourceListItem,
    GridCalculationRequest,
    GridCalculationResponse,
    MessageResponse
)
from ..gempy_service import geothermal_calculator

router = APIRouter(prefix="/api/gempy", tags=["GemPy建模与资源计算"])
logger = logging.getLogger(__name__)

@router.post("/calculate", response_model=GeothermalCalculationResponse)
async def calculate_geothermal_resource(
    request: GeothermalCalculationRequest,
    db: Session = Depends(get_db)
):
    """
    计算地热资源
    """
    try:
        # 执行计算
        results = geothermal_calculator.full_calculation(
            reservoir_volume=request.reservoir_volume,
            avg_temperature=request.avg_temperature,
            reference_temperature=request.reference_temperature,
            porosity=request.porosity,
            recovery_factor=request.recovery_factor,
            utilization_efficiency=request.utilization_efficiency,
            lifetime_years=request.lifetime_years,
            water_density=request.water_density,
            water_specific_heat=request.water_specific_heat,
            pressure=request.pressure
        )
        
        # 保存结果到数据库
        db_resource = GeothermalResource(
            name=f"计算结果_{request.model_id}",
            model_type="geothermal_resource",
            volume=request.reservoir_volume,
            temperature_avg=request.avg_temperature,
            temperature_max=request.avg_temperature,
            heat_content=results['total_heat'],
            power_potential=results['power_potential_mw'],
            lifetime_years=request.lifetime_years,
            parameters=results['parameters'],
            result_data=results
        )
        db.add(db_resource)
        db.commit()
        db.refresh(db_resource)
        
        return GeothermalCalculationResponse(
            success=True,
            message="地热资源计算完成",
            result=GeothermalResourceResponse.model_validate(db_resource)
        )
        
    except Exception as e:
        logger.error(f"Failed to calculate resource: {str(e)}")
        return GeothermalCalculationResponse(
            success=False,
            message=f"计算出错: {str(e)}"
        )


@router.get("/results", response_model=List[GeothermalResourceListItem])
async def get_calculation_results(db: Session = Depends(get_db)):
    """获取所有计算结果（简化列表，不含大数据字段）"""
    results = db.query(GeothermalResource).order_by(GeothermalResource.created_at.desc()).all()
    return results


@router.get("/results/count")
async def get_calculation_results_count(db: Session = Depends(get_db)):
    """获取计算结果总数"""
    try:
        count = db.query(GeothermalResource).count()
        return {"count": count}
    except Exception as e:
        logger.error(f"Failed to query calculation result count: {e}")
        raise HTTPException(status_code=500, detail="查询计算结果总数失败")


@router.get("/results/{result_id}", response_model=GeothermalResourceResponse)
async def get_calculation_result(result_id: int, db: Session = Depends(get_db)):
    """获取单个计算结果"""
    result = db.query(GeothermalResource).filter(GeothermalResource.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="计算结果未找到")
    return result


@router.delete("/results/{result_id}", response_model=MessageResponse)
async def delete_calculation_result(result_id: int, db: Session = Depends(get_db)):
    """删除计算结果"""
    result = db.query(GeothermalResource).filter(GeothermalResource.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="计算结果未找到")
    
    db.delete(result)
    db.commit()
    return MessageResponse(success=True, message="计算结果删除成功")


@router.get("/quick-calc")
async def quick_calculation(
    reservoir_volume: float,
    avg_temperature: float,
    porosity: float = 0.15,
    recovery_factor: float = 0.25
):
    """
    快速计算地热资源（简化版）
    
    用于快速估算，无需保存结果
    """
    results = geothermal_calculator.full_calculation(
        reservoir_volume=reservoir_volume,
        avg_temperature=avg_temperature,
        porosity=porosity,
        recovery_factor=recovery_factor
    )
    
    return {
        "success": True,
        "data": {
            "total_heat_joules": results['total_heat'],
            "power_potential_mw": results['power_potential_mw'],
            "summary": f"储层体积 {reservoir_volume:.2e} m³，平均温度 {avg_temperature}°C，"
                      f"预估发电潜力 {results['power_potential_mw']:.2f} MW"
        }
    }


@router.post("/calculate-grid", response_model=GridCalculationResponse)
async def calculate_grid_resources(
    request: GridCalculationRequest,
    db: Session = Depends(get_db)
):
    """
    网格资源计算 - 基于专利方法
    
    根据专利《一种不规则热储层多相态地热流体资源量计算方法》实现：
    1. 相态判定：比较网格温度与沸点温度，划分为气液共存网格集和液态水网格集
    2. 密度校正：根据温度计算地热流体密度
    3. 资源量计算：分别计算液态和气液共存资源量
    """
    try:
        # 转换网格数据
        grid_data = [grid.model_dump() for grid in request.grids]
        
        # 调试日志：打印接收到的网格数据
        logger.info(f"[网格计算] 接收到 {len(grid_data)} 条网格数据")
        for i, g in enumerate(grid_data):
            logger.info(f"[网格计算] 网格{i+1}: coord=({g.get('coord_x')}, {g.get('coord_y')}, {g.get('coord_z')}), volume={g.get('volume')}, temperature={g.get('temperature')}, phase={g.get('phase')}")
        
        # 执行网格资源计算
        results = geothermal_calculator.calculate_grid_resources(
            grid_data=grid_data,
            reference_temp=request.reference_temperature
        )
        
        # 计算发电潜力
        power_results = geothermal_calculator.calculate_power_potential(
            total_heat=results['total_resource_joules'],
            recovery_factor=request.recovery_factor,
            utilization_efficiency=request.utilization_efficiency,
            lifetime_years=request.lifetime_years
        )
        
        # 合并结果
        final_results = {
            **results,
            **power_results,
            'parameters': {
                'grid_count': results['total_grid_count'],
                'reference_temperature': request.reference_temperature,
                'recovery_factor': request.recovery_factor,
                'utilization_efficiency': request.utilization_efficiency,
                'lifetime_years': request.lifetime_years
            }
        }
        
        # 尝试保存结果到数据库
        try:
            # 构建包含原始网格数据的参数
            save_params = {
                'grid_count': results['total_grid_count'],
                'reference_temperature': request.reference_temperature,
                'recovery_factor': request.recovery_factor,
                'utilization_efficiency': request.utilization_efficiency,
                'lifetime_years': request.lifetime_years,
                'original_grids': [
                    {
                        'porosity': g.porosity,
                        'volume': g.volume,
                        'temperature': g.temperature,
                        'pressure': g.pressure
                    } for g in request.grids
                ]
            }
            
            db_resource = GeothermalResource(
                name=f"网格计算_{results['total_grid_count']}个网格",
                model_type="grid_calculation",
                volume=sum(g.volume for g in request.grids),
                temperature_avg=sum(g.temperature for g in request.grids) / len(request.grids),
                temperature_max=max(g.temperature for g in request.grids),
                heat_content=results['total_resource_joules'],
                power_potential=power_results['power_potential_mw'],
                lifetime_years=request.lifetime_years,
                parameters=save_params,
                result_data=final_results
            )
            db.add(db_resource)
            db.commit()
        except Exception as db_error:
            logger.warning(f"Database save failed: {db_error}")
            # 数据库保存失败不影响返回结果
        
        return GridCalculationResponse(
            success=True,
            message=f"网格资源计算完成，共{results['total_grid_count']}个网格",
            data=final_results
        )
        
    except Exception as e:
        logger.error(f"Failed to calculate grid resources: {str(e)}")
        return GridCalculationResponse(
            success=False,
            message=f"计算出错: {str(e)}"
        )


@router.get("/phase-determination")
async def determine_phase(
    temperature: float,
    pressure: float
):
    """
    相态判定接口
    """
    try:
        T_boiling = geothermal_calculator.calculate_boiling_point(pressure)
        phase = geothermal_calculator.determine_phase(temperature, pressure)
        density = geothermal_calculator.calculate_water_density(temperature)
        
        return {
            "success": True,
            "data": {
                "temperature": temperature,
                "pressure": pressure,
                "boiling_point": T_boiling,
                "phase_type": phase,
                "phase_description": "液态水" if phase == 'liquid' else "气液共存",
                "water_density": density,
                "is_boiling": temperature >= T_boiling
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
