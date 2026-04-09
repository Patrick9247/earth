"""
GemPy 建模和地热资源计算 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from ..database import get_db
from ..models import GeothermalResource, ModelConfig
from ..schemas import (
    GemPyModelRequest,
    GemPyModelResponse,
    GeothermalCalculationRequest,
    GeothermalCalculationResponse,
    GeothermalResourceResponse,
    GridCalculationRequest,
    GridCalculationResponse,
    MessageResponse
)
from ..gempy_service import gempy_service, geothermal_calculator

router = APIRouter(prefix="/api/gempy", tags=["GemPy建模与资源计算"])
logger = logging.getLogger(__name__)


@router.post("/model/create", response_model=GemPyModelResponse)
async def create_geological_model(
    request: GemPyModelRequest,
    db: Session = Depends(get_db)
):
    """
    创建地质模型
    
    使用 GemPy 根据地质层和钻孔数据创建三维地质模型
    """
    try:
        # 确定模型范围
        if request.config_id:
            config = db.query(ModelConfig).filter(ModelConfig.id == request.config_id).first()
            if not config:
                raise HTTPException(status_code=404, detail="模型配置未找到")
            extent = [
                config.extent_x_min, config.extent_x_max,
                config.extent_y_min, config.extent_y_max,
                config.extent_z_min, config.extent_z_max
            ]
            resolution = config.grid_resolution
        else:
            # 根据钻孔数据自动计算范围
            drill_holes = request.drill_holes
            x_coords = [dh.location_x for dh in drill_holes]
            y_coords = [dh.location_y for dh in drill_holes]
            depths = [dh.total_depth for dh in drill_holes if dh.total_depth]
            
            # 添加边界缓冲
            x_range = max(x_coords) - min(x_coords) if x_coords else 1000
            y_range = max(y_coords) - min(y_coords) if y_coords else 1000
            
            extent = [
                min(x_coords) - x_range * 0.2 if x_coords else 0,
                max(x_coords) + x_range * 0.2 if x_coords else 1000,
                min(y_coords) - y_range * 0.2 if y_coords else 0,
                max(y_coords) + y_range * 0.2 if y_coords else 1000,
                -max(depths) - 100 if depths else -2000,
                100
            ]
            resolution = request.grid_resolution
        
        # 创建 GemPy 模型
        success = gempy_service.create_model(
            model_name="geothermal_model",
            extent=extent,
            resolution=resolution
        )
        
        if not success:
            return GemPyModelResponse(
                success=False,
                message="模型创建失败"
            )
        
        # 添加地质层表面点
        for layer in request.layers:
            points = []
            # 从钻孔数据推断层界面点
            for dh in request.drill_holes:
                if layer.depth_top is not None and layer.depth_bottom is not None:
                    mid_depth = (layer.depth_top + layer.depth_bottom) / 2
                    # 使用 elevation 字段（地面高程），默认为 0
                    elevation = dh.elevation if dh.elevation else 0
                    points.append({
                        'x': dh.location_x,
                        'y': dh.location_y,
                        'z': elevation - mid_depth
                    })
            
            if points:
                gempy_service.add_surface_points(layer.name, points)
        
        # 计算模型
        success = gempy_service.compute_model()
        
        if not success:
            return GemPyModelResponse(
                success=False,
                message="模型计算失败"
            )
        
        # 获取网格数据
        mesh_data = gempy_service.get_surface_mesh()
        statistics = gempy_service.get_model_statistics()
        
        return GemPyModelResponse(
            success=True,
            message="地质模型创建成功",
            mesh_data=mesh_data,
            statistics=statistics
        )
        
    except Exception as e:
        logger.error(f"Failed to create model: {str(e)}")
        return GemPyModelResponse(
            success=False,
            message=f"模型创建出错: {str(e)}"
        )


@router.post("/calculate", response_model=GeothermalCalculationResponse)
async def calculate_geothermal_resource(
    request: GeothermalCalculationRequest,
    db: Session = Depends(get_db)
):
    """
    计算地热资源
    
    根据储层参数计算地热流体资源量和发电潜力
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
            rock_density=request.rock_density,
            water_specific_heat=request.water_specific_heat,
            rock_specific_heat=request.rock_specific_heat,
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
            extractable_heat=results['extractable_heat'],
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


@router.get("/results", response_model=List[GeothermalResourceResponse])
async def get_calculation_results(db: Session = Depends(get_db)):
    """获取所有计算结果"""
    results = db.query(GeothermalResource).all()
    return results


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
            "extractable_heat_joules": results['extractable_heat'],
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
                'grid_count': len(request.grids),
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
                'grid_count': len(request.grids),
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
                name=f"网格计算_{len(request.grids)}个网格",
                model_type="grid_calculation",
                volume=sum(g.volume for g in request.grids),
                temperature_avg=sum(g.temperature for g in request.grids) / len(request.grids),
                temperature_max=max(g.temperature for g in request.grids),
                heat_content=results['total_resource_joules'],
                extractable_heat=power_results['extractable_heat'],
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
            message=f"网格资源计算完成，共{len(request.grids)}个网格",
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
    
    根据专利方法，判断给定温度和压力下的相态
    - 返回沸点温度、相态类型、水密度等信息
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
