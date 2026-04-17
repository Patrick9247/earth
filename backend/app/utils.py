"""
后端工具函数
"""
import numpy as np
from typing import List, Dict, Any, Tuple



def interpolate_temperature(
    depth: float,
    gradient: float,
    surface_temp: float = 25.0
) -> float:
    """
    根据地温梯度插值计算温度
    depth: 深度 (m)
    gradient: 地温梯度 (°C/100m)
    surface_temp: 地表温度 (°C)
    
    Returns:
        该深度的温度 (°C)
    """
    return surface_temp + (depth / 100) * gradient



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
            'hole_id': f'ZK-{str(i+1).zfill(3)}',
            'hole_name': f'钻孔{str(i+1).zfill(3)}',
            'location_x': float(x_coords[i]),
            'location_y': float(y_coords[i]),
            'elevation': float(np.random.uniform(40, 60)),
            'total_depth': float(depth),
            'status': '完成',
            'description': f'合成钻孔数据 #{i+1}'
        })
    
    return drill_holes

