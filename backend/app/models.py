"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    hashed_password = Column(String(255), nullable=False, comment="密码哈希")
    role = Column(String(20), nullable=False, default="ADMIN", comment="角色: SUPER(超级管理员), ADMIN(普通管理员)")
    email = Column(String(100), comment="邮箱")
    full_name = Column(String(100), comment="姓名")
    phone = Column(String(20), comment="联系电话")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class StratigraphicLayer(Base):
    """地层分层数据表 - 按Excel模板设计"""
    __tablename__ = "stratigraphic_layers"
    
    id = Column(Integer, primary_key=True, index=True)
    hole_name = Column(String(100), nullable=False, index=True, comment="钻孔名称")
    depth_top = Column(Float, nullable=False, comment="顶部深度(m)")
    depth_bottom = Column(Float, nullable=False, comment="底部深度(m)")
    layer_type = Column(String(50), nullable=False, comment="地层类型(盖层/热储层/基层)")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


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
    power_potential = Column(Float, comment="发电潜力(MW)")
    lifetime_years = Column(Integer, comment="开采年限(年)")
    parameters = Column(JSON, comment="计算参数")
    result_data = Column(JSON, comment="详细结果数据")
    created_at = Column(DateTime, default=datetime.now())


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


class CsvImportRecord(Base):
    """CSV导入记录表"""
    __tablename__ = "csv_import_records"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), comment="文件名")
    import_type = Column(String(50), comment="导入类型(drill_info/layers/temperature/pressure/porosity)")
    total_rows = Column(Integer, comment="总行数")
    success_rows = Column(Integer, comment="成功行数")
    failed_rows = Column(Integer, comment="失败行数")
    error_details = Column(JSON, comment="错误详情")
    status = Column(String(50), default="处理中", comment="导入状态")
    created_at = Column(DateTime, server_default=func.now())


class GridCalculation(Base):
    """网格资源计算表单数据（专利方法）"""
    __tablename__ = "grid_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="计算名称")
    reference_temperature = Column(Float, default=25, comment="参考温度(°C)")
    recovery_factor = Column(Float, default=0.25, comment="采收率")
    utilization_efficiency = Column(Float, default=0.1, comment="利用效率")
    lifetime_years = Column(Integer, default=30, comment="开采年限(年)")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class GridItem(Base):
    """单个网格数据"""
    __tablename__ = "grid_items"
    
    id = Column(Integer, primary_key=True, index=True)
    calc_id = Column(Integer, nullable=False, index=True, comment="所属计算ID")
    coord_x = Column(Float, comment="X坐标")
    coord_y = Column(Float, comment="Y坐标")
    coord_z = Column(Float, comment="Z坐标(深度)")
    porosity = Column(Float, comment="孔隙度")
    volume = Column(Float, comment="体积(m³)")
    temperature = Column(Float, comment="温度(°C)")
    pressure = Column(Float, comment="压力(kPa)")
    liquid_specific_heat = Column(Float, comment="液体比热容(kJ/(kg·°C))")
    gas_specific_heat = Column(Float, comment="气体比热容(kJ/(kg·°C))")
    latent_heat = Column(Float, comment="气化潜热(kJ/kg)")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
