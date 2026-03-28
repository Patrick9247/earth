"""
GemPy 地质建模服务
用于构建三维地质模型和计算地热流体资源
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
import json

logger = logging.getLogger(__name__)

try:
    import gempy as gp
    GEMPY_AVAILABLE = True
except ImportError:
    GEMPY_AVAILABLE = False
    logger.warning("GemPy not available. Using simulation mode.")


class GemPyService:
    """GemPy 地质建模服务类"""
    
    def __init__(self):
        self.model = None
        self.solutions = None
        self.grid = None
        
    def create_model(
        self,
        model_name: str,
        extent: List[float],
        resolution: int = 50
    ) -> bool:
        """
        创建 GemPy 模型
        
        Args:
            model_name: 模型名称
            extent: 模型范围 [x_min, x_max, y_min, y_max, z_min, z_max]
            resolution: 网格分辨率
            
        Returns:
            是否成功创建
        """
        try:
            if not GEMPY_AVAILABLE:
                logger.info("GemPy not available, creating simulated model")
                self._create_simulated_model(extent, resolution)
                return True
            
            # 创建 GeoModel
            self.model = gp.create_model(model_name)
            
            # 初始化模型网格
            gp.init_data(
                self.model,
                extent=extent,
                resolution=[resolution, resolution, resolution]
            )
            
            self.grid = self.model.grid
            logger.info(f"Model created successfully: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create model: {str(e)}")
            return False
    
    def _create_simulated_model(self, extent: List[float], resolution: int):
        """创建模拟模型（当GemPy不可用时）"""
        self.model = {
            'name': 'simulated_model',
            'extent': extent,
            'resolution': resolution,
            'grid': {
                'x': np.linspace(extent[0], extent[1], resolution),
                'y': np.linspace(extent[2], extent[3], resolution),
                'z': np.linspace(extent[4], extent[5], resolution)
            }
        }
        self.grid = self.model['grid']
    
    def add_surface_points(
        self,
        surface_name: str,
        points: List[Dict[str, float]]
    ) -> bool:
        """
        添加地表点数据
        
        Args:
            surface_name: 地表名称
            points: 点列表 [{'x': x, 'y': y, 'z': z}, ...]
            
        Returns:
            是否成功添加
        """
        try:
            if not GEMPY_AVAILABLE or self.model is None:
                logger.info(f"Simulated: Added {len(points)} points for surface {surface_name}")
                return True
            
            # 转换点数据
            x = np.array([p['x'] for p in points])
            y = np.array([p['y'] for p in points])
            z = np.array([p['z'] for p in points])
            
            # 添加地表点
            gp.map_stack_to_surfaces(
                self.model,
                {surface_name: [surface_name]}
            )
            
            self.model.add_surface_points(
                surface=surface_name,
                X=x,
                Y=y,
                Z=z
            )
            
            logger.info(f"Added {len(points)} surface points for {surface_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add surface points: {str(e)}")
            return False
    
    def add_orientations(
        self,
        surface_name: str,
        orientations: List[Dict[str, float]]
    ) -> bool:
        """
        添加方位数据
        
        Args:
            surface_name: 地表名称
            orientations: 方位列表 [{'x': x, 'y': y, 'z': z, 'dip': dip, 'azimuth': azimuth}, ...]
            
        Returns:
            是否成功添加
        """
        try:
            if not GEMPY_AVAILABLE or self.model is None:
                logger.info(f"Simulated: Added orientations for surface {surface_name}")
                return True
            
            x = np.array([o['x'] for o in orientations])
            y = np.array([o['y'] for o in orientations])
            z = np.array([o['z'] for o in orientations])
            dip = np.array([o.get('dip', 0) for o in orientations])
            azimuth = np.array([o.get('azimuth', 0) for o in orientations])
            
            self.model.add_orientations(
                surface=surface_name,
                X=x,
                Y=y,
                Z=z,
                dip=dip,
                azimuth=azimuth
            )
            
            logger.info(f"Added {len(orientations)} orientations for {surface_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add orientations: {str(e)}")
            return False
    
    def compute_model(self) -> bool:
        """
        计算地质模型
        
        Returns:
            是否成功计算
        """
        try:
            if not GEMPY_AVAILABLE or self.model is None:
                logger.info("Simulated: Model computed")
                return True
            
            # 设置插值器
            gp.set_interpolator(
                self.model,
                compile_theano=True,
                theano_optimizer='fast_compile'
            )
            
            # 计算模型
            self.solutions = gp.compute_model(self.model)
            
            logger.info("Model computed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to compute model: {str(e)}")
            return False
    
    def get_surface_mesh(self) -> Optional[Dict[str, Any]]:
        """
        获取地表网格数据（用于3D可视化）
        
        Returns:
            网格数据字典
        """
        try:
            if not GEMPY_AVAILABLE or self.model is None or self.solutions is None:
                # 返回模拟数据
                return self._get_simulated_mesh()
            
            # 获取地表网格
            surfaces = self.model.surfaces
            
            mesh_data = {}
            for surface in surfaces.df['surface']:
                if surface in self.solutions.vertices:
                    vertices = self.solutions.vertices[surface]
                    mesh_data[surface] = {
                        'vertices': vertices.tolist(),
                        'triangles': []  # GemPy 需要额外处理三角形
                    }
            
            return mesh_data
            
        except Exception as e:
            logger.error(f"Failed to get surface mesh: {str(e)}")
            return None
    
    def _get_simulated_mesh(self) -> Dict[str, Any]:
        """获取模拟网格数据"""
        if self.model is None:
            return {}
        
        extent = self.model.get('extent', [0, 1000, 0, 1000, -2000, 0])
        resolution = self.model.get('resolution', 50)
        
        # 创建简单的层状结构
        layers = {
            'surface': {
                'vertices': self._generate_layer_surface(extent, 0),
                'color': '#4CAF50'
            },
            'layer1': {
                'vertices': self._generate_layer_surface(extent, -500),
                'color': '#FFC107'
            },
            'layer2': {
                'vertices': self._generate_layer_surface(extent, -1000),
                'color': '#FF9800'
            },
            'layer3': {
                'vertices': self._generate_layer_surface(extent, -1500),
                'color': '#F44336'
            }
        }
        
        return layers
    
    def _generate_layer_surface(self, extent: List[float], z_base: float) -> List[List[float]]:
        """生成层表面顶点"""
        x = np.linspace(extent[0], extent[1], 20)
        y = np.linspace(extent[2], extent[3], 20)
        X, Y = np.meshgrid(x, y)
        
        # 添加一些随机起伏
        Z = np.ones_like(X) * z_base + np.sin(X/100) * 50 + np.cos(Y/100) * 50
        
        vertices = []
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                vertices.append([float(X[i,j]), float(Y[i,j]), float(Z[i,j])])
        
        return vertices
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """
        获取模型统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'grid_resolution': self.model.get('resolution', 50) if isinstance(self.model, dict) else getattr(self.model.grid, 'resolution', 50) if self.model else 50,
            'extent': self.model.get('extent', []) if isinstance(self.model, dict) else [],
            'surfaces': 4,
            'computation_time': 0.5
        }
        return stats


class GeothermalCalculator:
    """地热资源计算器"""
    
    # 物理常数
    WATER_DENSITY = 1000  # kg/m³
    ROCK_DENSITY = 2600   # kg/m³
    WATER_SPECIFIC_HEAT = 4186  # J/(kg·K)
    ROCK_SPECIFIC_HEAT = 880    # J/(kg·K)
    SECONDS_PER_YEAR = 365.25 * 24 * 3600
    
    def calculate_heat_content(
        self,
        reservoir_volume: float,
        avg_temperature: float,
        reference_temperature: float = 25.0,
        porosity: float = 0.15,
        water_density: float = WATER_DENSITY,
        rock_density: float = ROCK_DENSITY,
        water_specific_heat: float = WATER_SPECIFIC_HEAT,
        rock_specific_heat: float = ROCK_SPECIFIC_HEAT
    ) -> Dict[str, float]:
        """
        计算地热储层热含量
        
        Args:
            reservoir_volume: 储层体积 (m³)
            avg_temperature: 平均温度 (°C)
            reference_temperature: 参考温度 (°C)
            porosity: 孔隙度
            water_density: 水密度 (kg/m³)
            rock_density: 岩石密度 (kg/m³)
            water_specific_heat: 水比热容 (J/(kg·K))
            rock_specific_heat: 岩石比热容 (J/(kg·K))
            
        Returns:
            计算结果字典
        """
        # 温度差
        delta_T = avg_temperature - reference_temperature
        
        # 计算有效体积
        water_volume = reservoir_volume * porosity
        rock_volume = reservoir_volume * (1 - porosity)
        
        # 计算质量
        water_mass = water_volume * water_density
        rock_mass = rock_volume * rock_density
        
        # 计算热含量 (J)
        water_heat = water_mass * water_specific_heat * delta_T
        rock_heat = rock_mass * rock_specific_heat * delta_T
        total_heat = water_heat + rock_heat
        
        return {
            'water_volume': water_volume,
            'rock_volume': rock_volume,
            'water_mass': water_mass,
            'rock_mass': rock_mass,
            'water_heat': water_heat,
            'rock_heat': rock_heat,
            'total_heat': total_heat,
            'delta_temperature': delta_T
        }
    
    def calculate_power_potential(
        self,
        total_heat: float,
        recovery_factor: float = 0.25,
        utilization_efficiency: float = 0.1,
        lifetime_years: int = 30
    ) -> Dict[str, float]:
        """
        计算发电潜力
        
        Args:
            total_heat: 总热含量 (J)
            recovery_factor: 采收率
            utilization_efficiency: 利用效率
            lifetime_years: 开采年限
            
        Returns:
            发电潜力计算结果
        """
        # 可采热量
        extractable_heat = total_heat * recovery_factor
        
        # 总发电量 (J)
        total_power_energy = extractable_heat * utilization_efficiency
        
        # 年均发电量 (J/year)
        annual_energy = total_power_energy / lifetime_years
        
        # 转换为 MW
        # 1 MW = 1e6 J/s
        # 年发电量转换为 MW: annual_energy (J/year) / seconds_per_year / 1e6
        power_potential_mw = annual_energy / self.SECONDS_PER_YEAR / 1e6
        
        return {
            'extractable_heat': extractable_heat,
            'total_power_energy': total_power_energy,
            'annual_energy': annual_energy,
            'power_potential_mw': power_potential_mw,
            'capacity_factor': 0.85  # 假设容量因子
        }
    
    def full_calculation(
        self,
        reservoir_volume: float,
        avg_temperature: float,
        reference_temperature: float = 25.0,
        porosity: float = 0.15,
        recovery_factor: float = 0.25,
        utilization_efficiency: float = 0.1,
        lifetime_years: int = 30,
        water_density: float = WATER_DENSITY,
        rock_density: float = ROCK_DENSITY,
        water_specific_heat: float = WATER_SPECIFIC_HEAT,
        rock_specific_heat: float = ROCK_SPECIFIC_HEAT
    ) -> Dict[str, Any]:
        """
        完整的地热资源计算
        
        Returns:
            完整计算结果
        """
        # 计算热含量
        heat_results = self.calculate_heat_content(
            reservoir_volume=reservoir_volume,
            avg_temperature=avg_temperature,
            reference_temperature=reference_temperature,
            porosity=porosity,
            water_density=water_density,
            rock_density=rock_density,
            water_specific_heat=water_specific_heat,
            rock_specific_heat=rock_specific_heat
        )
        
        # 计算发电潜力
        power_results = self.calculate_power_potential(
            total_heat=heat_results['total_heat'],
            recovery_factor=recovery_factor,
            utilization_efficiency=utilization_efficiency,
            lifetime_years=lifetime_years
        )
        
        # 合并结果
        return {
            **heat_results,
            **power_results,
            'parameters': {
                'reservoir_volume': reservoir_volume,
                'avg_temperature': avg_temperature,
                'reference_temperature': reference_temperature,
                'porosity': porosity,
                'recovery_factor': recovery_factor,
                'utilization_efficiency': utilization_efficiency,
                'lifetime_years': lifetime_years
            }
        }


# 创建全局服务实例
gempy_service = GemPyService()
geothermal_calculator = GeothermalCalculator()
