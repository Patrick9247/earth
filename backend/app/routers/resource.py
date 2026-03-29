"""
地热流体资源计算模块
基于专利文献中的公式实现
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import math
import logging

router = APIRouter(prefix="/api/resource", tags=["资源计算"])
logger = logging.getLogger(__name__)


# ==================== 物理参数模型 ====================

class GridCell(BaseModel):
    """单个网格单元"""
    id: int
    x: float  # x坐标 (m)
    y: float  # y坐标 (m)
    z: float  # z坐标 (深度，m，负值)
    volume: float  # 网格体积 (m³)
    porosity: float  # 孔隙度 φi
    pressure: float  # 压力 Pi (MPa)
    temperature: float  # 温度 Ti (°C)
    layer_id: Optional[int] = None  # 所属地层ID


class GridParameters(BaseModel):
    """网格参数配置"""
    x_min: float = 0
    x_max: float = 1000
    y_min: float = 0
    y_max: float = 1000
    z_min: float = -2000  # 深度（负值）
    z_max: float = 0
    nx: int = 20  # x方向网格数
    ny: int = 20  # y方向网格数
    nz: int = 40  # z方向网格数


class DrillHoleData(BaseModel):
    """钻孔数据"""
    id: int
    name: str
    location_x: float
    location_y: float
    location_z: float  # 地面高程
    depth: float
    temperature: float  # 底部温度 (°C)
    gradient: float  # 地温梯度 (°C/100m)


class LayerData(BaseModel):
    """地质层数据"""
    id: int
    name: str
    layer_type: str
    depth_top: float  # 顶部深度 (m)
    depth_bottom: float  # 底部深度 (m)
    porosity: float  # 孔隙度
    permeability: float  # 渗透率 (mD)
    thermal_conductivity: float  # 热导率 (W/m·K)
    color: str


class ResourceCalculationRequest(BaseModel):
    """资源计算请求"""
    grid_params: GridParameters
    drill_holes: List[DrillHoleData]
    layers: List[LayerData]
    surface_temperature: float = 15.0  # 地表温度 (°C)
    reference_pressure: float = 0.101325  # 参考压力 (MPa)


class GridCellResult(BaseModel):
    """网格计算结果"""
    id: int
    x: float
    y: float
    z: float
    volume: float
    porosity: float
    pressure: float
    temperature: float
    boiling_point: float  # 沸点温度 (°C)
    phase_state: str  # 相态: "liquid" 或 "two_phase"
    density: float  # 流体密度 (kg/m³)
    water_density: float  # 水密度 (kg/m³)
    steam_density: float  # 蒸汽密度 (kg/m³)
    steam_fraction: float  # 蒸汽质量分数
    resource_amount: float  # 资源量 (J)
    layer_id: Optional[int] = None


class ResourceSummary(BaseModel):
    """资源汇总"""
    total_resource: float  # 总资源量 (J)
    liquid_resource: float  # 纯液态资源量 (J)
    two_phase_resource: float  # 气液共存资源量 (J)
    total_volume: float  # 总体积 (m³)
    pore_volume: float  # 孔隙体积 (m³)
    liquid_cells: int  # 纯液态网格数
    two_phase_cells: int  # 气液共存网格数


class ResourceCalculationResponse(BaseModel):
    """资源计算响应"""
    grid_cells: List[GridCellResult]
    summary: ResourceSummary
    grid_params: GridParameters


# ==================== 物理计算函数 ====================

def calculate_boiling_point(pressure: float) -> float:
    """
    根据压力计算沸点温度
    使用改进的饱和蒸汽压公式
    
    公式来源：国际水蒸气性质表
    T = 100 * (P / 0.101325)^(0.25) 近似
    
    更精确的公式：
    ln(P) = A - B/(T + C)  (Antoine公式)
    对于水：A=8.07131, B=1730.63, C=233.426 (适用于1-100°C)
    或使用IF97标准
    """
    # 使用近似公式计算沸点
    # P (MPa) -> T (°C)
    # 在标准大气压(0.101325 MPa)下，沸点为100°C
    if pressure <= 0:
        return 100.0
    
    # 使用IF97近似公式
    # T = 179.89 * P^0.25 (粗略近似)
    # 更精确：使用饱和蒸汽表数据拟合
    P_bar = pressure * 10  # MPa -> bar
    
    # 使用多项式拟合（基于饱和蒸汽表）
    # 适用范围：0.1-20 MPa
    if P_bar < 0.1:
        P_bar = 0.1
    
    # 饱和温度近似公式
    T_sat = 100 * (P_bar / 1.01325) ** 0.25
    
    # 对于更高压力，使用更精确的公式
    if P_bar > 1:
        # 使用改进公式
        T_sat = 100 + 28.64 * math.log(P_bar) + 8.2 * math.log(P_bar) ** 2
    
    return round(T_sat, 2)


def calculate_water_density(temperature: float, pressure: float) -> float:
    """
    计算水的密度
    温度：°C，压力：MPa
    """
    T = temperature + 273.15  # 转换为开尔文
    P = pressure * 1e6  # MPa -> Pa
    
    # 使用简化公式
    # ρ = ρ0 * (1 - β*(T-T0) + κ*(P-P0))
    # ρ0 = 1000 kg/m³ at 4°C, 1 atm
    # β ≈ 2.1e-4 /K (热膨胀系数)
    # κ ≈ 4.6e-10 /Pa (等温压缩系数)
    
    rho_0 = 1000  # kg/m³
    T_0 = 277.15  # 4°C in K
    P_0 = 101325  # 1 atm in Pa
    
    beta = 2.1e-4  # 热膨胀系数
    kappa = 4.6e-10  # 等温压缩系数
    
    # 考虑温度和压力效应
    rho = rho_0 * (1 - beta * (T - T_0) + kappa * (P - P_0))
    
    # 高温修正
    if temperature > 100:
        # 高温时密度下降更快
        rho = rho * (1 - 0.0005 * (temperature - 100))
    
    return max(rho, 800)  # 最低不低于800 kg/m³


def calculate_steam_density(temperature: float, pressure: float) -> float:
    """
    计算饱和蒸汽密度
    温度：°C，压力：MPa
    """
    T = temperature + 273.15  # K
    P = pressure * 1e6  # Pa
    
    # 使用理想气体近似：ρ = PM/(RT)
    # M = 18.015 g/mol (水的摩尔质量)
    # R = 8.314 J/(mol·K)
    M = 18.015
    R = 8.314
    
    # 实际气体修正因子（近似）
    Z = 1.0
    if pressure > 1:
        Z = 0.95 - 0.02 * (pressure - 1)  # 高压修正
    
    rho = (P * M) / (Z * R * T)
    
    return rho


def calculate_steam_fraction(temperature: float, pressure: float, boiling_point: float) -> float:
    """
    计算蒸汽质量分数（干度）
    在气液共存区
    """
    if temperature <= boiling_point:
        return 0.0
    
    # 使用简化的热力学模型
    # x = (h - h_f) / h_fg
    # 其中 h 为比焓，h_f 为饱和液体比焓，h_fg 为汽化潜热
    
    # 汽化潜热近似：h_fg = 2257 - 2.0 * (T_sat - 100) kJ/kg
    h_fg = 2257 - 2.0 * (boiling_point - 100)  # kJ/kg
    h_fg = max(h_fg, 1000)  # 最小值
    
    # 过热度
    superheat = temperature - boiling_point
    
    # 蒸汽分数近似
    # 假设过热蒸汽的比热容约为 2.0 kJ/(kg·K)
    x = min(1.0, (superheat * 2.0) / h_fg + 0.1)
    
    return round(x, 4)


def calculate_phase_state(temperature: float, boiling_point: float) -> str:
    """
    判断相态
    返回 "liquid" 或 "two_phase"
    """
    if temperature < boiling_point:
        return "liquid"
    else:
        return "two_phase"


def calculate_mixture_density(
    water_density: float,
    steam_density: float,
    steam_fraction: float
) -> float:
    """
    计算气液混合物密度
    ρ_m = 1 / (x/ρ_g + (1-x)/ρ_l)
    """
    if steam_fraction <= 0:
        return water_density
    if steam_fraction >= 1:
        return steam_density
    
    # 混合密度
    rho_m = 1.0 / (steam_fraction / steam_density + (1 - steam_fraction) / water_density)
    
    return rho_m


def calculate_resource_amount(
    volume: float,
    porosity: float,
    density: float,
    temperature: float,
    reference_temp: float = 15.0
) -> float:
    """
    计算单个网格的资源量
    
    资源量 = V * φ * ρ * Cp * (T - T0)
    
    其中：
    - V: 网格体积 (m³)
    - φ: 孔隙度
    - ρ: 流体密度 (kg/m³)
    - Cp: 比热容 (J/(kg·K))，水约为 4186
    - T: 温度 (°C)
    - T0: 参考温度 (°C)
    """
    Cp = 4186  # 水的比热容 J/(kg·K)
    
    # 孔隙体积
    pore_volume = volume * porosity
    
    # 流体质量
    fluid_mass = pore_volume * density
    
    # 热能
    delta_T = max(0, temperature - reference_temp)
    energy = fluid_mass * Cp * delta_T
    
    return energy


def interpolate_3d(
    x: float, y: float, z: float,
    drill_holes: List[DrillHoleData],
    layers: List[LayerData],
    surface_temp: float
) -> tuple:
    """
    三维插值计算网格点的温度和压力
    
    返回：(temperature, pressure, layer_id)
    """
    # 计算深度
    depth = abs(z)
    
    # 确定所属地层
    layer_id = None
    layer_porosity = 0.15  # 默认孔隙度
    for layer in layers:
        if layer.depth_top <= depth <= layer.depth_bottom:
            layer_id = layer.id
            layer_porosity = layer.porosity
            break
    
    if layer_id is None and layers:
        # 使用最深地层
        layer_id = layers[-1].id
        layer_porosity = layers[-1].porosity
    
    # 基于钻孔数据插值温度
    temperature = surface_temp
    
    if drill_holes:
        # 使用反距离加权插值
        total_weight = 0
        weighted_temp = 0
        
        for hole in drill_holes:
            # 计算到钻孔的水平距离
            dist = math.sqrt((x - hole.location_x) ** 2 + (y - hole.location_y) ** 2)
            
            if dist < 1:
                # 如果非常接近钻孔，直接使用钻孔数据
                # 温度随深度变化
                temp_at_depth = surface_temp + hole.gradient * depth / 100
                temperature = min(temp_at_depth, hole.temperature)
                break
            
            # 反距离权重
            weight = 1.0 / (dist ** 2)
            
            # 钻孔在该深度的温度
            temp_at_depth = surface_temp + hole.gradient * depth / 100
            temp_at_depth = min(temp_at_depth, hole.temperature)
            
            weighted_temp += weight * temp_at_depth
            total_weight += weight
        
        if total_weight > 0:
            temperature = weighted_temp / total_weight
    
    # 计算压力
    # 静水压力：P = ρ * g * h
    # 假设水密度 1000 kg/m³，g = 9.81 m/s²
    # P (MPa) = 1000 * 9.81 * depth / 1e6 = 0.00981 * depth
    # 加上大气压
    pressure = 0.101325 + 0.00981 * depth
    
    return temperature, pressure, layer_id, layer_porosity


# ==================== API 端点 ====================

@router.post("/calculate", response_model=ResourceCalculationResponse)
async def calculate_resource(request: ResourceCalculationRequest):
    """
    计算地热流体资源量
    
    基于以下步骤：
    1. 建立三维网格模型
    2. 插值计算每个网格的温度和压力
    3. 根据压力计算沸点温度
    4. 判断相态（纯液态/气液共存）
    5. 计算流体密度
    6. 计算资源量
    """
    try:
        gp = request.grid_params
        dx = (gp.x_max - gp.x_min) / gp.nx
        dy = (gp.y_max - gp.y_min) / gp.ny
        dz = (gp.z_max - gp.z_min) / gp.nz
        
        cell_volume = dx * dy * dz
        
        grid_cells = []
        cell_id = 0
        
        # 用于统计
        total_resource = 0
        liquid_resource = 0
        two_phase_resource = 0
        total_pore_volume = 0
        liquid_cells = 0
        two_phase_cells = 0
        
        # 遍历所有网格
        for i in range(gp.nx):
            x = gp.x_min + dx * (i + 0.5)
            for j in range(gp.ny):
                y = gp.y_min + dy * (j + 0.5)
                for k in range(gp.nz):
                    z = gp.z_min + dz * (k + 0.5)  # 深度为负值
                    
                    # 插值计算温度和压力
                    temp, press, layer_id, porosity = interpolate_3d(
                        x, y, z,
                        request.drill_holes,
                        request.layers,
                        request.surface_temperature
                    )
                    
                    # 计算沸点
                    boiling_point = calculate_boiling_point(press)
                    
                    # 判断相态
                    phase_state = calculate_phase_state(temp, boiling_point)
                    
                    # 计算密度
                    water_density = calculate_water_density(temp, press)
                    steam_density = calculate_steam_density(temp, press)
                    
                    if phase_state == "liquid":
                        density = water_density
                        steam_fraction = 0
                    else:
                        steam_fraction = calculate_steam_fraction(temp, press, boiling_point)
                        density = calculate_mixture_density(water_density, steam_density, steam_fraction)
                    
                    # 计算资源量
                    resource = calculate_resource_amount(
                        cell_volume, porosity, density, temp, request.surface_temperature
                    )
                    
                    # 统计
                    total_resource += resource
                    total_pore_volume += cell_volume * porosity
                    
                    if phase_state == "liquid":
                        liquid_resource += resource
                        liquid_cells += 1
                    else:
                        two_phase_resource += resource
                        two_phase_cells += 1
                    
                    # 存储结果
                    grid_cells.append(GridCellResult(
                        id=cell_id,
                        x=round(x, 2),
                        y=round(y, 2),
                        z=round(z, 2),
                        volume=round(cell_volume, 2),
                        porosity=round(porosity, 4),
                        pressure=round(press, 4),
                        temperature=round(temp, 2),
                        boiling_point=boiling_point,
                        phase_state=phase_state,
                        density=round(density, 2),
                        water_density=round(water_density, 2),
                        steam_density=round(steam_density, 4),
                        steam_fraction=steam_fraction,
                        resource_amount=round(resource, 2),
                        layer_id=layer_id
                    ))
                    
                    cell_id += 1
        
        # 构建响应
        summary = ResourceSummary(
            total_resource=round(total_resource, 2),
            liquid_resource=round(liquid_resource, 2),
            two_phase_resource=round(two_phase_resource, 2),
            total_volume=round(gp.nx * gp.ny * gp.nz * cell_volume, 2),
            pore_volume=round(total_pore_volume, 2),
            liquid_cells=liquid_cells,
            two_phase_cells=two_phase_cells
        )
        
        return ResourceCalculationResponse(
            grid_cells=grid_cells,
            summary=summary,
            grid_params=gp
        )
        
    except Exception as e:
        logger.error(f"Resource calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/boiling-point/{pressure}")
async def get_boiling_point(pressure: float):
    """
    获取指定压力下的沸点温度
    
    参数：
    - pressure: 压力 (MPa)
    """
    bp = calculate_boiling_point(pressure)
    return {
        "pressure_mpa": pressure,
        "boiling_point_celsius": bp
    }


@router.get("/density")
async def get_density(
    temperature: float,
    pressure: float,
    phase: str = "liquid"
):
    """
    获取流体密度
    
    参数：
    - temperature: 温度 (°C)
    - pressure: 压力 (MPa)
    - phase: 相态 ("liquid" 或 "steam")
    """
    water_density = calculate_water_density(temperature, pressure)
    steam_density = calculate_steam_density(temperature, pressure)
    
    return {
        "temperature_celsius": temperature,
        "pressure_mpa": pressure,
        "water_density_kg_m3": round(water_density, 2),
        "steam_density_kg_m3": round(steam_density, 4)
    }
