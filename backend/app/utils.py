"""
后端工具函数
"""
import numpy as np
from typing import List, Dict, Any, Tuple


def calculate_distance(
    point1: Tuple[float, float, float],
    point2: Tuple[float, float, float]
) -> float:
    """计算两点之间的欧几里得距离"""
    return np.sqrt(
        (point1[0] - point2[0]) ** 2 +
        (point1[1] - point2[1]) ** 2 +
        (point1[2] - point2[2]) ** 2
    )


def interpolate_temperature(
    depth: float,
    gradient: float,
    surface_temp: float = 25.0
) -> float:
    """
    根据地温梯度插值计算温度
    
    Args:
        depth: 深度 (m)
        gradient: 地温梯度 (°C/100m)
        surface_temp: 地表温度 (°C)
    
    Returns:
        该深度的温度 (°C)
    """
    return surface_temp + (depth / 100) * gradient


def calculate_heat_flow(
    temperature_gradient: float,
    thermal_conductivity: float
) -> float:
    """
    计算热流密度
    
    Args:
        temperature_gradient: 温度梯度 (K/m)
        thermal_conductivity: 热导率 (W/m·K)
    
    Returns:
        热流密度 (W/m²)
    """
    return abs(temperature_gradient) * thermal_conductivity


def estimate_reservoir_volume(
    area: float,
    thickness: float
) -> float:
    """
    估算储层体积
    
    Args:
        area: 储层面积 (m²)
        thickness: 储层厚度 (m)
    
    Returns:
        储层体积 (m³)
    """
    return area * thickness


def calculate_stored_heat(
    volume: float,
    porosity: float,
    temperature: float,
    reference_temp: float = 25.0,
    water_density: float = 1000.0,
    rock_density: float = 2600.0,
    water_specific_heat: float = 4186.0,
    rock_specific_heat: float = 880.0
) -> Dict[str, float]:
    """
    计算储层储存的热量
    
    Returns:
        包含各项热含量的字典
    """
    delta_t = temperature - reference_temp
    
    water_volume = volume * porosity
    rock_volume = volume * (1 - porosity)
    
    water_mass = water_volume * water_density
    rock_mass = rock_volume * rock_density
    
    water_heat = water_mass * water_specific_heat * delta_t
    rock_heat = rock_mass * rock_specific_heat * delta_t
    total_heat = water_heat + rock_heat
    
    return {
        'water_volume': water_volume,
        'rock_volume': rock_volume,
        'water_mass': water_mass,
        'rock_mass': rock_mass,
        'water_heat': water_heat,
        'rock_heat': rock_heat,
        'total_heat': total_heat
    }


def calculate_recovery_factor(
    porosity: float,
    permeability: float,
    reservoir_depth: float
) -> float:
    """
    根据储层参数估算采收率
    
    Args:
        porosity: 孔隙度 (0-1)
        permeability: 渗透率 (mD)
        reservoir_depth: 储层深度 (m)
    
    Returns:
        采收率 (0-1)
    """
    # 基础采收率
    base_recovery = 0.15
    
    # 孔隙度修正
    porosity_factor = porosity / 0.15
    
    # 渗透率修正（对数）
    permeability_factor = min(np.log10(permeability + 1) / 3, 1.5)
    
    # 深度修正（越深采收率越低）
    depth_factor = max(1 - reservoir_depth / 5000, 0.5)
    
    recovery = base_recovery * porosity_factor * permeability_factor * depth_factor
    
    return min(max(recovery, 0.1), 0.4)


def generate_synthetic_drill_data(
    num_holes: int,
    extent: Tuple[float, float, float, float],
    depth_range: Tuple[float, float] = (500, 2000),
    gradient_range: Tuple[float, float] = (5, 8)
) -> List[Dict[str, Any]]:
    """
    生成合成钻孔数据（用于测试和演示）
    
    Args:
        num_holes: 钻孔数量
        extent: 范围 (x_min, y_min, x_max, y_max)
        depth_range: 深度范围 (m)
        gradient_range: 地温梯度范围 (°C/100m)
    
    Returns:
        钻孔数据列表
    """
    np.random.seed(42)
    
    x_coords = np.random.uniform(extent[0], extent[2], num_holes)
    y_coords = np.random.uniform(extent[1], extent[3], num_holes)
    depths = np.random.uniform(depth_range[0], depth_range[1], num_holes)
    gradients = np.random.uniform(gradient_range[0], gradient_range[1], num_holes)
    
    drill_holes = []
    for i in range(num_holes):
        depth = depths[i]
        gradient = gradients[i]
        surface_temp = 25.0
        bottom_temp = interpolate_temperature(depth, gradient, surface_temp)
        
        drill_holes.append({
            'name': f'ZK-{str(i+1).zfill(3)}',
            'location_x': float(x_coords[i]),
            'location_y': float(y_coords[i]),
            'location_z': float(np.random.uniform(40, 60)),
            'depth': float(depth),
            'temperature': float((surface_temp + bottom_temp) / 2),
            'gradient': float(gradient),
            'description': f'合成钻孔数据 #{i+1}'
        })
    
    return drill_holes


def generate_layer_surfaces(
    extent: Tuple[float, float, float, float, float, float],
    resolution: int = 50
) -> Dict[str, np.ndarray]:
    """
    生成层界面网格数据
    
    Args:
        extent: 范围 (x_min, x_max, y_min, y_max, z_min, z_max)
        resolution: 网格分辨率
    
    Returns:
        各层界面的网格数据
    """
    x = np.linspace(extent[0], extent[1], resolution)
    y = np.linspace(extent[2], extent[3], resolution)
    X, Y = np.meshgrid(x, y)
    
    layers = {}
    
    # 地表
    layers['surface'] = np.zeros_like(X)
    
    # 第一层界面
    layers['layer1'] = -500 + 50 * np.sin(X / 200) * np.cos(Y / 200)
    
    # 第二层界面
    layers['layer2'] = -1000 + 80 * np.sin(X / 150) * np.cos(Y / 150)
    
    # 第三层界面
    layers['layer3'] = -1500 + 100 * np.sin(X / 100) * np.cos(Y / 100)
    
    return layers


def format_number_scientific(value: float, decimals: int = 2) -> str:
    """科学计数法格式化数字"""
    if value == 0:
        return "0"
    return f"{value:.{decimals}e}"


def convert_units(
    value: float,
    from_unit: str,
    to_unit: str
) -> float:
    """
    单位转换
    
    支持的单位:
    - 长度: m, km
    - 体积: m3, km3
    - 能量: J, kJ, MJ, GJ, TJ, PJ, EJ
    - 功率: W, kW, MW, GW
    """
    conversions = {
        # 长度
        ('m', 'km'): 1e-3,
        ('km', 'm'): 1e3,
        # 体积
        ('m3', 'km3'): 1e-9,
        ('km3', 'm3'): 1e9,
        # 能量
        ('J', 'kJ'): 1e-3,
        ('J', 'MJ'): 1e-6,
        ('J', 'GJ'): 1e-9,
        ('J', 'TJ'): 1e-12,
        ('J', 'PJ'): 1e-15,
        ('J', 'EJ'): 1e-18,
        ('kJ', 'J'): 1e3,
        ('MJ', 'J'): 1e6,
        ('GJ', 'J'): 1e9,
        ('TJ', 'J'): 1e12,
        ('PJ', 'J'): 1e15,
        ('EJ', 'J'): 1e18,
        # 功率
        ('W', 'kW'): 1e-3,
        ('W', 'MW'): 1e-6,
        ('W', 'GW'): 1e-9,
        ('kW', 'W'): 1e3,
        ('MW', 'W'): 1e6,
        ('GW', 'W'): 1e9,
    }
    
    if from_unit == to_unit:
        return value
    
    key = (from_unit, to_unit)
    if key in conversions:
        return value * conversions[key]
    
    raise ValueError(f"Unknown conversion: {from_unit} -> {to_unit}")
