"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime


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
    """钻孔基本信息表 - 空间信息"""
    __tablename__ = "drill_holes"
    
    id = Column(Integer, primary_key=True, index=True)
    # 钻孔编号
    hole_id = Column(String(50), unique=True, nullable=False, comment="钻孔编号")
    hole_name = Column(String(100), comment="钻孔名称")
    # 空间坐标
    location_x = Column(Float, nullable=False, comment="X坐标(m)")
    location_y = Column(Float, nullable=False, comment="Y坐标(m)")
    elevation = Column(Float, default=0, comment="地面高程(m)")
    # 钻孔信息
    total_depth = Column(Float, comment="钻孔总深度(m)")
    final_depth = Column(Float, comment="终孔深度(m)")
    diameter = Column(Float, comment="孔径(mm)")
    # 施工信息
    drill_company = Column(String(200), comment="施工单位")
    drill_start_date = Column(String(20), comment="开孔日期")
    drill_end_date = Column(String(20), comment="终孔日期")
    # 状态
    status = Column(String(50), default="完成", comment="钻孔状态")
    description = Column(Text, comment="备注说明")
    # 元数据
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    layers = relationship("DrillLayer", back_populates="drill_hole", cascade="all, delete-orphan")
    temperature_curves = relationship("DrillTemperatureCurve", back_populates="drill_hole", cascade="all, delete-orphan")
    pressure_data = relationship("DrillPressureData", back_populates="drill_hole", cascade="all, delete-orphan")
    porosity_data = relationship("DrillPorosityData", back_populates="drill_hole", cascade="all, delete-orphan")


class DrillLayer(Base):
    """热储层分层数据表"""
    __tablename__ = "drill_layers"
    
    id = Column(Integer, primary_key=True, index=True)
    drill_hole_id = Column(Integer, ForeignKey("drill_holes.id"), nullable=False, comment="钻孔ID")
    
    # 分层信息
    layer_no = Column(Integer, comment="层序号")
    layer_name = Column(String(100), comment="地层名称")
    layer_type = Column(String(50), comment="地层类型(储层/盖层/基底等)")
    
    # 深度范围
    depth_top = Column(Float, comment="层顶深度(m)")
    depth_bottom = Column(Float, comment="层底深度(m)")
    thickness = Column(Float, comment="层厚度(m)")
    
    # 岩性信息
    lithology = Column(String(200), comment="岩性描述")
    rock_type = Column(String(100), comment="岩石类型")
    color = Column(String(50), comment="岩石颜色")
    
    # 物性参数
    porosity = Column(Float, comment="孔隙度")
    permeability = Column(Float, comment="渗透率(mD)")
    density = Column(Float, comment="岩石密度(g/cm³)")
    thermal_conductivity = Column(Float, comment="热导率(W/m·K)")
    
    # 含水层信息
    aquifer_type = Column(String(50), comment="含水层类型")
    water_bearing = Column(String(50), comment="富水性")
    
    # 其他
    description = Column(Text, comment="备注说明")
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联
    drill_hole = relationship("DrillHole", back_populates="layers")


class DrillTemperatureCurve(Base):
    """钻孔测温曲线数据表"""
    __tablename__ = "drill_temperature_curves"
    
    id = Column(Integer, primary_key=True, index=True)
    drill_hole_id = Column(Integer, ForeignKey("drill_holes.id"), nullable=False, comment="钻孔ID")
    
    # 测量信息
    measure_no = Column(Integer, comment="测点序号")
    measure_date = Column(String(20), comment="测量日期")
    measure_type = Column(String(50), default="稳态测温", comment="测量类型(稳态/非稳态)")
    
    # 深度和温度
    depth = Column(Float, comment="测量深度(m)")
    temperature = Column(Float, comment="测量温度(°C)")
    
    # 校正信息
    corrected_temp = Column(Float, comment="校正后温度(°C)")
    correction_method = Column(String(100), comment="校正方法")
    
    # 温度梯度
    gradient = Column(Float, comment="地温梯度(°C/100m)")
    
    # 其他
    instrument = Column(String(100), comment="测量仪器")
    accuracy = Column(Float, comment="测量精度(°C)")
    description = Column(Text, comment="备注")
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联
    drill_hole = relationship("DrillHole", back_populates="temperature_curves")


class DrillPressureData(Base):
    """孔口压力数据表"""
    __tablename__ = "drill_pressure_data"
    
    id = Column(Integer, primary_key=True, index=True)
    drill_hole_id = Column(Integer, ForeignKey("drill_holes.id"), nullable=False, comment="钻孔ID")
    # 测量信息
    measure_no = Column(Integer, comment="测点序号")
    measure_date = Column(String(20), comment="测量日期")
    measure_time = Column(String(20), comment="测量时间")
    # 压力数据
    wellhead_pressure = Column(Float, comment="井口压力(MPa)")
    reservoir_pressure = Column(Float, comment="储层压力(MPa)")
    flowing_pressure = Column(Float, comment="流动压力(MPa)")
    shut_in_pressure = Column(Float, comment="关井压力(MPa)")
    # 压力梯度
    pressure_gradient = Column(Float, comment="压力梯度(MPa/100m)")
    # 深度信息
    measure_depth = Column(Float, comment="测量深度(m)")
    # 流量相关
    flow_rate = Column(Float, comment="流量(m³/h)")
    water_level = Column(Float, comment="动水位(m)")
    # 其他
    instrument = Column(String(100), comment="测量仪器")
    description = Column(Text, comment="备注")
    created_at = Column(DateTime, server_default=func.now())
    # 关联
    drill_hole = relationship("DrillHole", back_populates="pressure_data")


class DrillPorosityData(Base):
    """岩石孔隙度数据表"""
    __tablename__ = "drill_porosity_data"
    id = Column(Integer, primary_key=True, index=True)
    drill_hole_id = Column(Integer, ForeignKey("drill_holes.id"), nullable=False, comment="钻孔ID")
    
    # 采样信息
    sample_no = Column(String(50), comment="样品编号")
    sample_date = Column(String(20), comment="采样日期")
    
    # 深度信息
    depth_top = Column(Float, comment="样品顶深(m)")
    depth_bottom = Column(Float, comment="样品底深(m)")
    depth = Column(Float, comment="取样深度(m)")
    
    # 岩性信息
    lithology = Column(String(200), comment="岩性描述")
    rock_type = Column(String(100), comment="岩石类型")
    
    # 孔隙度数据
    porosity_total = Column(Float, comment="总孔隙度(%)")
    porosity_effective = Column(Float, comment="有效孔隙度(%)")
    
    # 渗透性数据
    permeability = Column(Float, comment="渗透率(mD)")
    permeability_horizontal = Column(Float, comment="水平渗透率(mD)")
    permeability_vertical = Column(Float, comment="垂直渗透率(mD)")
    
    # 其他物性
    density_bulk = Column(Float, comment="体密度(g/cm³)")
    density_grain = Column(Float, comment="颗粒密度(g/cm³)")
    water_saturation = Column(Float, comment="含水饱和度(%)")
    
    # 测试信息
    test_method = Column(String(100), comment="测试方法")
    laboratory = Column(String(200), comment="测试单位")
    
    # 其他
    description = Column(Text, comment="备注")
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联
    drill_hole = relationship("DrillHole", back_populates="porosity_data")


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
    grid_count = Column(Integer, default=1, comment="网格数量")
    porosity = Column(Float, comment="孔隙度")
    volume = Column(Float, comment="体积(m³)")
    temperature = Column(Float, comment="温度(°C)")
    pressure = Column(Float, comment="压力(MPa)")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
