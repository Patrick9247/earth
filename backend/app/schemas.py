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


# ==================== CSV导入 Schemas ====================
class CsvImportResult(BaseModel):
    """CSV导入结果"""
    success: bool
    message: str
    total_rows: int = 0
    success_rows: int = 0
    failed_rows: int = 0
    errors: Optional[List[Dict[str, Any]]] = None
    record_id: Optional[int] = None


class CsvPreviewResponse(BaseModel):
    """CSV预览响应"""
    success: bool
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    message: Optional[str] = None


# ==================== 地热资源 Schemas ====================
class GeothermalResourceBase(BaseModel):
    name: str = Field(..., description="模型名称")
    model_type: Optional[str] = Field(None, description="模型类型")
    volume: Optional[float] = Field(None, ge=0, description="资源体积(m³)")
    temperature_avg: Optional[float] = Field(None, description="平均温度(°C)")
    temperature_max: Optional[float] = Field(None, description="最高温度(°C)")
    heat_content: Optional[float] = Field(None, ge=0, description="热含量(J)")
    power_potential: Optional[float] = Field(None, ge=0, description="发电潜力(MW)")
    lifetime_years: Optional[int] = Field(None, ge=0, description="开采年限(年)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="计算参数")
    result_data: Optional[Dict[str, Any]] = Field(None, description="详细结果数据")


class GeothermalResourceResponse(GeothermalResourceBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class GeothermalResourceListItem(BaseModel):
    """用于列表显示的简化响应模型"""
    id: int
    name: str
    model_type: Optional[str] = None
    volume: Optional[float] = None
    temperature_avg: Optional[float] = None
    temperature_max: Optional[float] = None
    heat_content: Optional[float] = None
    power_potential: Optional[float] = None
    lifetime_years: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None  # 包含网格数据等参数
    created_at: datetime
    
    class Config:
        from_attributes = True



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
    water_specific_heat: float = Field(4186, description="水比热容(J/kg·K)")
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
    """单个网格数据 - 每条数据为一个网格"""
    coord_x: Optional[float] = Field(None, description="X坐标")
    coord_y: Optional[float] = Field(None, description="Y坐标")
    coord_z: Optional[float] = Field(None, description="Z坐标(深度)")
    porosity: float = Field(0.15, ge=0, le=1, description="孔隙度")
    volume: float = Field(..., gt=0, description="体积(m³)")
    temperature: float = Field(..., gt=0, description="温度(°C)")
    pressure: float = Field(101.325, gt=0, description="压力(kPa)")
    phase: str = Field("liquid", description="相态: liquid(液态), two_phase(气液共存), gas(气态)")
    liquid_specific_heat: Optional[float] = Field(None, description="液体比热容(kJ/(kg·°C))")
    gas_specific_heat: Optional[float] = Field(None, description="气体比热容(kJ/(kg·°C))")
    latent_heat: Optional[float] = Field(None, description="气化潜热(kJ/kg)")


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


# ==================== 网格计算表单数据 Schemas ====================
class GridCalculationFormBase(BaseModel):
    """网格计算表单基础模型"""
    name: str = Field(..., description="计算名称")
    reference_temperature: float = Field(25, description="参考温度(°C)")
    recovery_factor: float = Field(0.25, ge=0, le=1, description="采收率")
    utilization_efficiency: float = Field(0.1, ge=0, le=1, description="利用效率")
    lifetime_years: int = Field(30, ge=1, description="开采年限(年)")


class GridCalculationFormCreate(GridCalculationFormBase):
    """创建网格计算表单"""
    pass


class GridCalculationFormUpdate(BaseModel):
    """更新网格计算表单"""
    name: Optional[str] = None
    reference_temperature: Optional[float] = None
    recovery_factor: Optional[float] = None
    utilization_efficiency: Optional[float] = None
    lifetime_years: Optional[int] = None


class GridCalculationFormResponse(GridCalculationFormBase):
    """网格计算表单响应"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== 地层分层数据 Schemas ====================
class StratigraphicLayerBase(BaseModel):
    """地层分层数据基础模型"""
    hole_name: str = Field(..., description="钻孔名称")
    depth_top: float = Field(..., description="顶部深度(m)")
    depth_bottom: float = Field(..., description="底部深度(m)")
    layer_type: str = Field(..., description="地层类型(盖层/热储层/基层)")


class StratigraphicLayerCreate(StratigraphicLayerBase):
    """创建地层分层数据"""
    pass


class StratigraphicLayerUpdate(BaseModel):
    """更新地层分层数据"""
    hole_name: Optional[str] = None
    depth_top: Optional[float] = None
    depth_bottom: Optional[float] = None
    layer_type: Optional[str] = None


class StratigraphicLayerResponse(StratigraphicLayerBase):
    """地层分层数据响应"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== 单个网格数据 Schemas ====================
class GridItemBase(BaseModel):
    """单个网格基础模型"""
    calc_id: int = Field(..., description="所属计算ID")
    coord_x: Optional[float] = Field(None, description="X坐标")
    coord_y: Optional[float] = Field(None, description="Y坐标")
    coord_z: Optional[float] = Field(None, description="Z坐标(深度)")
    porosity: Optional[float] = Field(None, ge=0, le=1, description="孔隙度")
    volume: Optional[float] = Field(None, gt=0, description="体积(m³)")
    temperature: Optional[float] = Field(None, description="温度(°C)")
    pressure: Optional[float] = Field(None, description="压力(kPa)")
    liquid_specific_heat: Optional[float] = Field(None, description="液体比热容(kJ/(kg·°C))")
    gas_specific_heat: Optional[float] = Field(None, description="气体比热容(kJ/(kg·°C))")
    latent_heat: Optional[float] = Field(None, description="气化潜热(kJ/kg)")
    sort_order: Optional[int] = Field(0, description="排序顺序")


class GridItemCreate(GridItemBase):
    """创建网格"""
    pass


class GridItemUpdate(BaseModel):
    """更新网格"""
    coord_x: Optional[float] = None
    coord_y: Optional[float] = None
    coord_z: Optional[float] = None
    porosity: Optional[float] = None
    volume: Optional[float] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    liquid_specific_heat: Optional[float] = None
    gas_specific_heat: Optional[float] = None
    latent_heat: Optional[float] = None
    sort_order: Optional[int] = None


class GridItemResponse(GridItemBase):
    """网格响应"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
