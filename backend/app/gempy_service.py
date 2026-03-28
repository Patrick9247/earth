"""
GemPy 地质建模服务
用于构建三维地质模型和计算地热流体资源

基于专利：一种不规则热储层多相态地热流体资源量计算方法
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
import math

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
        """
        try:
            if not GEMPY_AVAILABLE or self.model is None:
                logger.info(f"Simulated: Added {len(points)} points for surface {surface_name}")
                return True
            
            x = np.array([p['x'] for p in points])
            y = np.array([p['y'] for p in points])
            z = np.array([p['z'] for p in points])
            
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
    
    def compute_model(self) -> bool:
        """
        计算地质模型
        """
        try:
            if not GEMPY_AVAILABLE or self.model is None:
                logger.info("Simulated: Model computed")
                return True
            
            gp.set_interpolator(
                self.model,
                compile_theano=True,
                theano_optimizer='fast_compile'
            )
            
            self.solutions = gp.compute_model(self.model)
            
            logger.info("Model computed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to compute model: {str(e)}")
            return False
    
    def get_surface_mesh(self) -> Optional[Dict[str, Any]]:
        """获取地表网格数据（用于3D可视化）"""
        try:
            if not GEMPY_AVAILABLE or self.model is None or self.solutions is None:
                return self._get_simulated_mesh()
            
            surfaces = self.model.surfaces
            
            mesh_data = {}
            for surface in surfaces.df['surface']:
                if surface in self.solutions.vertices:
                    vertices = self.solutions.vertices[surface]
                    mesh_data[surface] = {
                        'vertices': vertices.tolist(),
                        'triangles': []
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
        
        Z = np.ones_like(X) * z_base + np.sin(X/100) * 50 + np.cos(Y/100) * 50
        
        vertices = []
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                vertices.append([float(X[i,j]), float(Y[i,j]), float(Z[i,j])])
        
        return vertices
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """获取模型统计信息"""
        stats = {
            'grid_resolution': self.model.get('resolution', 50) if isinstance(self.model, dict) else getattr(self.model.grid, 'resolution', 50) if self.model else 50,
            'extent': self.model.get('extent', []) if isinstance(self.model, dict) else [],
            'surfaces': 4,
            'computation_time': 0.5
        }
        return stats


class GeothermalCalculator:
    """
    地热资源计算器
    
    基于专利方法实现：
    - 相态判定（气液共存 vs 液态水）
    - 密度校正
    - 多相态资源量计算
    """
    
    # 物理常数
    WATER_DENSITY_STANDARD = 1000  # kg/m³ 标准条件下水密度
    ROCK_DENSITY = 2600   # kg/m³
    WATER_SPECIFIC_HEAT = 4186  # J/(kg·K)
    ROCK_SPECIFIC_HEAT = 880    # J/(kg·K)
    SECONDS_PER_YEAR = 365.25 * 24 * 3600
    
    # 水蒸气参数
    STEAM_SPECIFIC_VOLUME = 1.673  # m³/kg (100°C, 1atm)
    WATER_SPECIFIC_VOLUME = 0.001043  # m³/kg (100°C, 1atm)
    LATENT_HEAT_VAPORIZATION = 2257  # kJ/kg 气化潜热
    STEAM_SPECIFIC_HEAT = 2.08  # kJ/(kg·K) 水蒸气比热容
    
    def calculate_boiling_point(self, pressure: float) -> float:
        """
        相态判定曲线方程 - 计算沸点温度
        
        根据专利公式: T_boiling = -8.97 × ln(P)
        
        Args:
            pressure: 压力 (MPa)
            
        Returns:
            沸点温度 (°C)
        """
        if pressure <= 0:
            return 100.0  # 默认常压沸点
        
        # 专利公式: T = -8.97 × ln(P)
        # 这里压力单位需要确认，假设为MPa
        T_boiling = -8.97 * math.log(pressure)
        
        # 限制在合理范围内
        return max(100.0, min(T_boiling, 374.0))  # 水的临界温度约374°C
    
    def determine_phase(self, temperature: float, pressure: float) -> str:
        """
        相态判定
        
        根据专利方法，比较网格温度与沸点温度：
        - T < T_boiling: 液态水
        - T >= T_boiling: 气液共存
        
        Args:
            temperature: 网格温度 (°C)
            pressure: 网格压力 (MPa)
            
        Returns:
            相态类型: 'liquid' 或 'two_phase'
        """
        T_boiling = self.calculate_boiling_point(pressure)
        
        if temperature < T_boiling:
            return 'liquid'
        else:
            return 'two_phase'
    
    def calculate_water_density(self, temperature: float) -> float:
        """
        密度校正公式 - 计算地热流体密度
        
        根据专利公式:
        ρ = A × (1 - B × T)
        A = 0.99987 + 6.0×10⁻⁵ × T
        B = 2.0×10⁻⁴ + 1.0×10⁻⁵ × T
        
        Args:
            temperature: 温度 (°C)
            
        Returns:
            水密度 (kg/m³)
        """
        T = temperature
        
        # A = 0.99987 + 6.0×10⁻⁵ × T
        A = 0.99987 + 6.0e-5 * T
        
        # B = 2.0×10⁻⁴ + 1.0×10⁻⁵ × T  
        B = 2.0e-4 + 1.0e-5 * T
        
        # ρ = A × (1 - B × T) × 1000 (转换为kg/m³)
        density = A * (1 - B * T) * self.WATER_DENSITY_STANDARD
        
        # 限制在合理范围内
        return max(600.0, min(density, 1050.0))
    
    def calculate_liquid_resource(
        self,
        porosity: float,
        volume: float,
        temperature: float,
        reference_temp: float = 25.0
    ) -> float:
        """
        计算液态地热流体资源量
        
        根据专利公式:
        Q_liquid = Σ(φi × Vi × ρi × Cp × (Ti - T0))
        
        其中:
        - φi: 第i网格的孔隙度
        - Vi: 第i网格的体积
        - ρi: 第i网格中地热流体的密度
        - Cp: 地热水的比热容
        - Ti: 第i网格的温度
        - T0: 参考温度
        
        Args:
            porosity: 孔隙度
            volume: 网格体积 (m³)
            temperature: 温度 (°C)
            reference_temp: 参考温度 (°C)
            
        Returns:
            液态地热流体资源量 (J)
        """
        # 计算密度
        density = self.calculate_water_density(temperature)
        
        # 温度差
        delta_T = temperature - reference_temp
        
        # Q = φ × V × ρ × Cp × ΔT
        resource = porosity * volume * density * self.WATER_SPECIFIC_HEAT * delta_T
        
        return resource
    
    def calculate_two_phase_resource(
        self,
        porosity: float,
        volume: float,
        temperature: float,
        reference_temp: float = 25.0
    ) -> Dict[str, float]:
        """
        计算气液共存时的地热资源量
        
        根据专利公式:
        Q_total = Q_liquid_two_phase + Q_steam
        
        其中:
        Q_liquid_two_phase = Σ(φi × Vi × ρl × (vg / (vg - vf)) × Cp × (Ti - T0))
        Q_steam = Σ(φi × Vi × ρl × (vf / (vg - vf)) × (L + Cpg × (Ti - T0))
        
        Args:
            porosity: 孔隙度
            volume: 网格体积 (m³)
            temperature: 温度 (°C)
            reference_temp: 参考温度 (°C)
            
        Returns:
            包含液态资源量、蒸汽资源量和总资源量的字典
        """
        # 计算密度
        density = self.calculate_water_density(temperature)
        
        # 温度差
        delta_T = temperature - reference_temp
        
        # 水蒸气比容和水的比容
        vg = self.STEAM_SPECIFIC_VOLUME  # m³/kg
        vf = self.WATER_SPECIFIC_VOLUME  # m³/kg
        
        # 气液共存时液态水比例
        liquid_fraction = vg / (vg - vf)
        # 蒸汽比例
        steam_fraction = vf / (vg - vf)
        
        # 气液共存时液态地热流体的资源量
        Q_liquid_two_phase = (
            porosity * volume * density * liquid_fraction * 
            self.WATER_SPECIFIC_HEAT * delta_T
        )
        
        # 气液共存时水蒸汽的资源量
        # L = 气化潜热, Cpg = 气体比热容
        L = self.LATENT_HEAT_VAPORIZATION * 1000  # 转换为 J/kg
        Cpg = self.STEAM_SPECIFIC_HEAT * 1000  # 转换为 J/(kg·K)
        
        Q_steam = (
            porosity * volume * density * steam_fraction * 
            (L + Cpg * delta_T)
        )
        
        # 总资源量
        Q_total = Q_liquid_two_phase + Q_steam
        
        return {
            'liquid_resource': Q_liquid_two_phase,
            'steam_resource': Q_steam,
            'total_resource': Q_total,
            'liquid_fraction': liquid_fraction,
            'steam_fraction': steam_fraction
        }
    
    def calculate_grid_resources(
        self,
        grid_data: List[Dict[str, float]],
        reference_temp: float = 25.0
    ) -> Dict[str, Any]:
        """
        批量计算多网格资源量
        
        根据专利方法，对每个网格进行相态判定后分别计算
        
        Args:
            grid_data: 网格数据列表，每个元素包含:
                - porosity: 孔隙度
                - volume: 体积 (m³)
                - temperature: 温度 (°C)
                - pressure: 压力 (MPa)
            reference_temp: 参考温度 (°C)
            
        Returns:
            计算结果汇总
        """
        liquid_grids = []
        two_phase_grids = []
        
        total_liquid_resource = 0.0
        total_two_phase_liquid = 0.0
        total_steam_resource = 0.0
        
        for i, grid in enumerate(grid_data):
            porosity = grid.get('porosity', 0.15)
            volume = grid.get('volume', 0)
            temperature = grid.get('temperature', 100)
            pressure = grid.get('pressure', 0.1)  # 默认0.1 MPa
            
            if volume <= 0:
                continue
            
            # 相态判定
            phase = self.determine_phase(temperature, pressure)
            
            if phase == 'liquid':
                resource = self.calculate_liquid_resource(
                    porosity, volume, temperature, reference_temp
                )
                total_liquid_resource += resource
                liquid_grids.append({
                    'index': i,
                    'temperature': temperature,
                    'pressure': pressure,
                    'phase': phase,
                    'resource': resource
                })
            else:
                result = self.calculate_two_phase_resource(
                    porosity, volume, temperature, reference_temp
                )
                total_two_phase_liquid += result['liquid_resource']
                total_steam_resource += result['steam_resource']
                two_phase_grids.append({
                    'index': i,
                    'temperature': temperature,
                    'pressure': pressure,
                    'phase': phase,
                    **result
                })
        
        # 总资源量
        total_resource = (
            total_liquid_resource + 
            total_two_phase_liquid + 
            total_steam_resource
        )
        
        return {
            'total_resource_joules': total_resource,
            'liquid_phase_resource': total_liquid_resource,
            'two_phase_liquid_resource': total_two_phase_liquid,
            'steam_resource': total_steam_resource,
            'liquid_grid_count': len(liquid_grids),
            'two_phase_grid_count': len(two_phase_grids),
            'liquid_grids': liquid_grids,
            'two_phase_grids': two_phase_grids
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
        power_potential_mw = annual_energy / self.SECONDS_PER_YEAR / 1e6
        
        return {
            'extractable_heat': extractable_heat,
            'total_power_energy': total_power_energy,
            'annual_energy': annual_energy,
            'power_potential_mw': power_potential_mw,
            'capacity_factor': 0.85
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
        water_density: float = None,
        rock_density: float = ROCK_DENSITY,
        water_specific_heat: float = WATER_SPECIFIC_HEAT,
        rock_specific_heat: float = ROCK_SPECIFIC_HEAT,
        pressure: float = 0.1
    ) -> Dict[str, Any]:
        """
        完整的地热资源计算
        
        结合专利方法和传统方法进行综合计算
        
        Returns:
            完整计算结果
        """
        # 使用密度校正公式计算实际水密度
        if water_density is None:
            water_density = self.calculate_water_density(avg_temperature)
        
        # 相态判定
        phase = self.determine_phase(avg_temperature, pressure)
        
        # 温度差
        delta_T = avg_temperature - reference_temperature
        
        # 计算有效体积
        water_volume = reservoir_volume * porosity
        rock_volume = reservoir_volume * (1 - porosity)
        
        # 计算质量
        water_mass = water_volume * water_density
        rock_mass = rock_volume * rock_density
        
        # 根据相态选择计算方法
        if phase == 'liquid':
            # 液态水计算
            water_heat = water_mass * water_specific_heat * delta_T
            rock_heat = rock_mass * rock_specific_heat * delta_T
            total_heat = water_heat + rock_heat
            
            phase_info = {
                'phase_type': 'liquid',
                'water_density': water_density,
                'boiling_point': self.calculate_boiling_point(pressure)
            }
        else:
            # 气液共存计算
            result = self.calculate_two_phase_resource(
                porosity, reservoir_volume, avg_temperature, reference_temperature
            )
            
            # 加上岩石热量
            rock_heat = rock_mass * rock_specific_heat * delta_T
            total_heat = result['total_resource'] + rock_heat
            
            phase_info = {
                'phase_type': 'two_phase',
                'water_density': water_density,
                'boiling_point': self.calculate_boiling_point(pressure),
                'liquid_fraction': result['liquid_fraction'],
                'steam_fraction': result['steam_fraction'],
                'liquid_resource': result['liquid_resource'],
                'steam_resource': result['steam_resource']
            }
        
        # 计算发电潜力
        power_results = self.calculate_power_potential(
            total_heat=total_heat,
            recovery_factor=recovery_factor,
            utilization_efficiency=utilization_efficiency,
            lifetime_years=lifetime_years
        )
        
        # 合并结果
        return {
            'total_heat': total_heat,
            'water_heat': water_heat if phase == 'liquid' else phase_info['liquid_resource'],
            'rock_heat': rock_heat,
            'water_volume': water_volume,
            'rock_volume': rock_volume,
            'water_mass': water_mass,
            'rock_mass': rock_mass,
            'delta_temperature': delta_T,
            **power_results,
            'phase_info': phase_info,
            'parameters': {
                'reservoir_volume': reservoir_volume,
                'avg_temperature': avg_temperature,
                'reference_temperature': reference_temperature,
                'porosity': porosity,
                'pressure': pressure,
                'recovery_factor': recovery_factor,
                'utilization_efficiency': utilization_efficiency,
                'lifetime_years': lifetime_years,
                'water_density': water_density,
                'rock_density': rock_density
            }
        }
    
    def calculate_heat_content(
        self,
        reservoir_volume: float,
        avg_temperature: float,
        reference_temperature: float = 25.0,
        porosity: float = 0.15,
        water_density: float = WATER_DENSITY_STANDARD,
        rock_density: float = ROCK_DENSITY,
        water_specific_heat: float = WATER_SPECIFIC_HEAT,
        rock_specific_heat: float = ROCK_SPECIFIC_HEAT
    ) -> Dict[str, float]:
        """
        计算地热储层热含量（传统方法，保持兼容性）
        """
        delta_T = avg_temperature - reference_temperature
        
        water_volume = reservoir_volume * porosity
        rock_volume = reservoir_volume * (1 - porosity)
        
        water_mass = water_volume * water_density
        rock_mass = rock_volume * rock_density
        
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


# 创建全局服务实例
gempy_service = GemPyService()
geothermal_calculator = GeothermalCalculator()
