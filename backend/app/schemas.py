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


# ==================== 钻孔基本信息 Schemas ====================
class DrillHoleBase(BaseModel):
    hole_id: str = Field(..., description="钻孔编号")
    hole_name: Optional[str] = Field(None, description="钻孔名称")
    location_x: float = Field(..., description="X坐标(m)")
    location_y: float = Field(..., description="Y坐标(m)")
    elevation: Optional[float] = Field(0, description="地面高程(m)")
    total_depth: Optional[float] = Field(None, description="钻孔总深度(m)")
    final_depth: Optional[float] = Field(None, description="终孔深度(m)")
    diameter: Optional[float] = Field(None, description="孔径(mm)")
    drill_company: Optional[str] = Field(None, description="施工单位")
    drill_start_date: Optional[str] = Field(None, description="开孔日期")
    drill_end_date: Optional[str] = Field(None, description="终孔日期")
    status: Optional[str] = Field("完成", description="钻孔状态")
    description: Optional[str] = Field(None, description="备注说明")


class DrillHoleCreate(DrillHoleBase):
    pass


class DrillHoleResponse(DrillHoleBase):
    id: int
    temperature: Optional[float] = Field(None, description="平均温度(°C)")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 热储层分层 Schemas ====================
class DrillLayerBase(BaseModel):
    drill_hole_id: int = Field(..., description="钻孔ID")
    layer_no: Optional[int] = Field(None, description="层序号")
    layer_name: Optional[str] = Field(None, description="地层名称")
    layer_type: Optional[str] = Field(None, description="地层类型")
    depth_top: Optional[float] = Field(None, description="层顶深度(m)")
    depth_bottom: Optional[float] = Field(None, description="层底深度(m)")
    thickness: Optional[float] = Field(None, description="层厚度(m)")
    lithology: Optional[str] = Field(None, description="岩性描述")
    rock_type: Optional[str] = Field(None, description="岩石类型")
    color: Optional[str] = Field(None, description="岩石颜色")
    porosity: Optional[float] = Field(None, description="孔隙度")
    permeability: Optional[float] = Field(None, description="渗透率(mD)")
    density: Optional[float] = Field(None, description="岩石密度(g/cm³)")
    thermal_conductivity: Optional[float] = Field(None, description="热导率(W/m·K)")
    aquifer_type: Optional[str] = Field(None, description="含水层类型")
    water_bearing: Optional[str] = Field(None, description="富水性")
    description: Optional[str] = Field(None, description="备注说明")


class DrillLayerCreate(DrillLayerBase):
    pass


class DrillLayerResponse(DrillLayerBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 测温曲线 Schemas ====================
class DrillTemperatureCurveBase(BaseModel):
    drill_hole_id: int = Field(..., description="钻孔ID")
    measure_no: Optional[int] = Field(None, description="测点序号")
    measure_date: Optional[str] = Field(None, description="测量日期")
    measure_type: Optional[str] = Field("稳态测温", description="测量类型")
    depth: float = Field(..., description="测量深度(m)")
    temperature: float = Field(..., description="测量温度(°C)")
    corrected_temp: Optional[float] = Field(None, description="校正后温度(°C)")
    correction_method: Optional[str] = Field(None, description="校正方法")
    gradient: Optional[float] = Field(None, description="地温梯度(°C/100m)")
    instrument: Optional[str] = Field(None, description="测量仪器")
    accuracy: Optional[float] = Field(None, description="测量精度(°C)")
    description: Optional[str] = Field(None, description="备注")


class DrillTemperatureCurveCreate(DrillTemperatureCurveBase):
    pass


class DrillTemperatureCurveResponse(DrillTemperatureCurveBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 孔口压力 Schemas ====================
class DrillPressureDataBase(BaseModel):
    drill_hole_id: int = Field(..., description="钻孔ID")
    measure_no: Optional[int] = Field(None, description="测点序号")
    measure_date: Optional[str] = Field(None, description="测量日期")
    measure_time: Optional[str] = Field(None, description="测量时间")
    wellhead_pressure: Optional[float] = Field(None, description="井口压力(MPa)")
    reservoir_pressure: Optional[float] = Field(None, description="储层压力(MPa)")
    flowing_pressure: Optional[float] = Field(None, description="流动压力(MPa)")
    shut_in_pressure: Optional[float] = Field(None, description="关井压力(MPa)")
    pressure_gradient: Optional[float] = Field(None, description="压力梯度(MPa/100m)")
    measure_depth: Optional[float] = Field(None, description="测量深度(m)")
    flow_rate: Optional[float] = Field(None, description="流量(m³/h)")
    water_level: Optional[float] = Field(None, description="动水位(m)")
    instrument: Optional[str] = Field(None, description="测量仪器")
    description: Optional[str] = Field(None, description="备注")


class DrillPressureDataCreate(DrillPressureDataBase):
    pass


class DrillPressureDataResponse(DrillPressureDataBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 孔隙度数据 Schemas ====================
class DrillPorosityDataBase(BaseModel):
    drill_hole_id: int = Field(..., description="钻孔ID")
    sample_no: Optional[str] = Field(None, description="样品编号")
    sample_date: Optional[str] = Field(None, description="采样日期")
    depth_top: Optional[float] = Field(None, description="样品顶深(m)")
    depth_bottom: Optional[float] = Field(None, description="样品底深(m)")
    depth: Optional[float] = Field(None, description="取样深度(m)")
    lithology: Optional[str] = Field(None, description="岩性描述")
    rock_type: Optional[str] = Field(None, description="岩石类型")
    porosity_total: Optional[float] = Field(None, description="总孔隙度(%)")
    porosity_effective: Optional[float] = Field(None, description="有效孔隙度(%)")
    permeability: Optional[float] = Field(None, description="渗透率(mD)")
    permeability_horizontal: Optional[float] = Field(None, description="水平渗透率(mD)")
    permeability_vertical: Optional[float] = Field(None, description="垂直渗透率(mD)")
    density_bulk: Optional[float] = Field(None, description="体密度(g/cm³)")
    density_grain: Optional[float] = Field(None, description="颗粒密度(g/cm³)")
    water_saturation: Optional[float] = Field(None, description="含水饱和度(%)")
    test_method: Optional[str] = Field(None, description="测试方法")
    laboratory: Optional[str] = Field(None, description="测试单位")
    description: Optional[str] = Field(None, description="备注")


class DrillPorosityDataCreate(DrillPorosityDataBase):
    pass


class DrillPorosityDataResponse(DrillPorosityDataBase):
    id: int
    created_at: datetime
    
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
