"""
Pydantic 数据模型（用于API请求和响应）
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== 地质层 Schemas ====================
class GeologicalLayerBase(BaseModel):
    name: str = Field(..., description="地层名称")
    layer_type: Optional[str] = Field(None, description="地层类型")
    depth_top: Optional[float] = Field(None, description="顶部深度(m)")
    depth_bottom: Optional[float] = Field(None, description="底部深度(m)")
    porosity: Optional[float] = Field(None, ge=0, le=1, description="孔隙度")
    permeability: Optional[float] = Field(None, ge=0, description="渗透率(mD)")
    thermal_conductivity: Optional[float] = Field(None, ge=0, description="热导率(W/m·K)")
    color: Optional[str] = Field(None, description="可视化颜色")
    layer_metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class GeologicalLayerCreate(GeologicalLayerBase):
    pass


class GeologicalLayerResponse(GeologicalLayerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 钻孔数据 Schemas ====================
class DrillHoleBase(BaseModel):
    name: str = Field(..., description="钻孔名称")
    location_x: float = Field(..., description="X坐标")
    location_y: float = Field(..., description="Y坐标")
    location_z: Optional[float] = Field(0, description="地面高程(m)")
    depth: float = Field(..., ge=0, description="钻孔深度(m)")
    temperature: Optional[float] = Field(None, description="测量温度(°C)")
    gradient: Optional[float] = Field(None, description="地温梯度(°C/100m)")
    description: Optional[str] = Field(None, description="描述")


class DrillHoleCreate(DrillHoleBase):
    pass


class DrillHoleResponse(DrillHoleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 地热资源 Schemas ====================
class GeothermalResourceBase(BaseModel):
    name: str = Field(..., description="模型名称")
    model_type: Optional[str] = Field(None, description="模型类型")
    volume: Optional[float] = Field(None, ge=0, description="资源体积(m³)")
    temperature_avg: Optional[float] = Field(None, description="平均温度(°C)")
    temperature_max: Optional[float] = Field(None, description="最高温度(°C)")
    heat_content: Optional[float] = Field(None, ge=0, description="热含量(J)")
    extractable_heat: Optional[float] = Field(None, ge=0, description="可采热量(J)")
    power_potential: Optional[float] = Field(None, ge=0, description="发电潜力(MW)")
    lifetime_years: Optional[int] = Field(None, ge=0, description="开采年限(年)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="计算参数")
    result_data: Optional[Dict[str, Any]] = Field(None, description="详细结果数据")


class GeothermalResourceResponse(GeothermalResourceBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 模型配置 Schemas ====================
class ModelConfigBase(BaseModel):
    name: str = Field(..., description="配置名称")
    grid_resolution: int = Field(50, ge=10, le=200, description="网格分辨率")
    extent_x_min: float = Field(0, description="X范围最小值")
    extent_x_max: float = Field(1000, description="X范围最大值")
    extent_y_min: float = Field(0, description="Y范围最小值")
    extent_y_max: float = Field(1000, description="Y范围最大值")
    extent_z_min: float = Field(-2000, description="Z范围最小值")
    extent_z_max: float = Field(0, description="Z范围最大值")
    config_data: Optional[Dict[str, Any]] = Field(None, description="完整配置数据")


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigResponse(ModelConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== GemPy 建模请求 Schemas ====================
class GemPyModelRequest(BaseModel):
    """GemPy 建模请求"""
    config_id: Optional[int] = Field(None, description="配置ID")
    layers: List[GeologicalLayerCreate] = Field(..., description="地质层数据")
    drill_holes: List[DrillHoleCreate] = Field(..., description="钻孔数据")
    grid_resolution: int = Field(50, ge=10, le=200, description="网格分辨率")


class GemPyModelResponse(BaseModel):
    """GemPy 建模响应"""
    success: bool
    message: str
    model_id: Optional[int] = None
    mesh_data: Optional[Dict[str, Any]] = None
    statistics: Optional[Dict[str, Any]] = None


# ==================== 地热资源计算请求 Schemas ====================
class GeothermalCalculationRequest(BaseModel):
    """地热资源计算请求"""
    model_id: int = Field(..., description="模型ID")
    reservoir_volume: float = Field(..., gt=0, description="储层体积(m³)")
    avg_temperature: float = Field(..., gt=0, description="平均温度(°C)")
    reference_temperature: float = Field(25, description="参考温度(°C)")
    porosity: float = Field(0.15, ge=0, le=1, description="有效孔隙度")
    pressure: float = Field(0.1, gt=0, description="储层压力(MPa)")
    water_density: Optional[float] = Field(None, description="水密度(kg/m³)，留空自动计算")
    rock_density: float = Field(2600, description="岩石密度(kg/m³)")
    water_specific_heat: float = Field(4186, description="水比热容(J/kg·K)")
    rock_specific_heat: float = Field(880, description="岩石比热容(J/kg·K)")
    recovery_factor: float = Field(0.25, ge=0, le=1, description="采收率")
    utilization_efficiency: float = Field(0.1, ge=0, le=1, description="利用效率")
    lifetime_years: int = Field(30, ge=1, description="开采年限(年)")


class GeothermalCalculationResponse(BaseModel):
    """地热资源计算响应"""
    success: bool
    message: str
    result: Optional[GeothermalResourceResponse] = None


# ==================== 网格资源计算请求 Schemas ====================
class GridDataItem(BaseModel):
    """单个网格数据"""
    porosity: float = Field(0.15, ge=0, le=1, description="孔隙度")
    volume: float = Field(..., gt=0, description="体积(m³)")
    temperature: float = Field(..., gt=0, description="温度(°C)")
    pressure: float = Field(0.1, gt=0, description="压力(MPa)")


class GridCalculationRequest(BaseModel):
    """网格资源计算请求 - 基于专利方法"""
    grids: List[GridDataItem] = Field(..., description="网格数据列表")
    reference_temperature: float = Field(25, description="参考温度(°C)")
    recovery_factor: float = Field(0.25, ge=0, le=1, description="采收率")
    utilization_efficiency: float = Field(0.1, ge=0, le=1, description="利用效率")
    lifetime_years: int = Field(30, ge=1, description="开采年限(年)")


class GridCalculationResponse(BaseModel):
    """网格资源计算响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# ==================== 通用响应 ====================
class MessageResponse(BaseModel):
    """通用消息响应"""
    success: bool
    message: str
