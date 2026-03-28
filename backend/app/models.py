"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from .database import Base


class GeologicalLayer(Base):
    """地质层模型"""
    __tablename__ = "geological_layers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="地层名称")
    layer_type = Column(String(50), comment="地层类型")
    depth_top = Column(Float, comment="顶部深度(m)")
    depth_bottom = Column(Float, comment="底部深度(m)")
    porosity = Column(Float, comment="孔隙度")
    permeability = Column(Float, comment="渗透率(mD)")
    thermal_conductivity = Column(Float, comment="热导率(W/m·K)")
    color = Column(String(20), comment="可视化颜色")
    layer_metadata = Column(JSON, comment="元数据")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DrillHole(Base):
    """钻孔数据模型"""
    __tablename__ = "drill_holes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="钻孔名称")
    location_x = Column(Float, comment="X坐标")
    location_y = Column(Float, comment="Y坐标")
    location_z = Column(Float, default=0, comment="地面高程(m)")
    depth = Column(Float, comment="钻孔深度(m)")
    temperature = Column(Float, comment="测量温度(°C)")
    gradient = Column(Float, comment="地温梯度(°C/100m)")
    description = Column(Text, comment="描述")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class GeothermalResource(Base):
    """地热资源计算结果"""
    __tablename__ = "geothermal_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="模型名称")
    model_type = Column(String(50), comment="模型类型")
    volume = Column(Float, comment="资源体积(m³)")
    temperature_avg = Column(Float, comment="平均温度(°C)")
    temperature_max = Column(Float, comment="最高温度(°C)")
    heat_content = Column(Float, comment="热含量(J)")
    extractable_heat = Column(Float, comment="可采热量(J)")
    power_potential = Column(Float, comment="发电潜力(MW)")
    lifetime_years = Column(Integer, comment="开采年限(年)")
    parameters = Column(JSON, comment="计算参数")
    result_data = Column(JSON, comment="详细结果数据")
    created_at = Column(DateTime, server_default=func.now())


class ModelConfig(Base):
    """模型配置"""
    __tablename__ = "model_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    grid_resolution = Column(Integer, default=50, comment="网格分辨率")
    extent_x_min = Column(Float, comment="X范围最小值")
    extent_x_max = Column(Float, comment="X范围最大值")
    extent_y_min = Column(Float, comment="Y范围最小值")
    extent_y_max = Column(Float, comment="Y范围最大值")
    extent_z_min = Column(Float, comment="Z范围最小值")
    extent_z_max = Column(Float, comment="Z范围最大值")
    config_data = Column(JSON, comment="完整配置数据")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
