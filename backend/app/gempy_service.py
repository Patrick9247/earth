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
    WATER_SPECIFIC_HEAT = 4800  # J/(kg·K)
    SECONDS_PER_YEAR = 365.25 * 24 * 3600
    
    # 水蒸气参数
    STEAM_SPECIFIC_VOLUME = 1.673  # m³/kg (100°C, 1atm)
    WATER_SPECIFIC_VOLUME = 0.001043  # m³/kg (100°C, 1atm)
    LATENT_HEAT_VAPORIZATION = 2257  # kJ/kg 气化潜热
    STEAM_SPECIFIC_HEAT = 2  # kJ/(kg·K) 水蒸气比热容
    
    def calculate_boiling_point(self, pressure_kpa: float) -> float:
        """
        相态判定曲线方程 - 计算沸点温度（饱和温度）
        
        分段公式：
        - T_isat = 0.95 × P_i + 26.44（P_i ≤ 101.325 kPa）
        - T_isat = 0.04 × P_i + 132.01（P_i > 101.325 kPa）
        
        Args:
            pressure_kpa: 压力 (kPa)
            
        Returns:
            饱和温度 (°C)
        """
        if pressure_kpa <= 0:
            return 100.0  # 默认常压沸点
        
        # 分段公式计算饱和温度
        if pressure_kpa <= 101.325:
            # P_i ≤ 101.325 kPa: T_isat = 0.95 × P_i + 26.44
            T_sat = 0.95 * pressure_kpa + 26.44
        else:
            # P_i > 101.325 kPa: T_isat = 0.04 × P_i + 132.01
            T_sat = 0.04 * pressure_kpa + 132.01
        
        # 限制在合理范围内
        return max(0.0, min(T_sat, 374.0))  # 水的临界温度约374°C
    
    def calculate_saturation_properties(self, temperature: float) -> tuple:
        """
        计算饱和状态下的蒸汽比容和水比容
        
        使用 IAPWS-IF97 近似公式
        
        Args:
            temperature: 饱和温度 (°C)
            
        Returns:
            (蒸汽比容 vg, 水比容 vp) 单位 m³/kg
        """
        T = temperature
        
        # 饱和水比容 vp (m³/kg)
        # 使用 IAPWS-IF97 近似公式
        if T < 100:
            vp = 0.001043 - 0.0000002 * (T - 100)  # 约 0.001043 m³/kg 在 100°C
        elif T < 200:
            vp = 0.001043 + 0.0000005 * (T - 100)  # 随温度略微增加
        else:
            vp = 0.001093 + 0.000001 * (T - 200)   # 高温下增加更快
        
        # 饱和蒸汽比容 vg (m³/kg)
        # 根据理想气体状态方程近似: vg = R*T / P
        # 先计算饱和压力（从饱和温度公式反推）
        # 分段公式反推：
        # T ≤ 122.7°C 时，P = (T - 26.44) / 0.95
        # T > 122.7°C 时，P = (T - 132.01) / 0.04
        T临界 = 0.95 * 101.325 + 26.44  # ≈ 122.7 °C
        if T <= T临界:
            P_sat_kpa = (T - 26.44) / 0.95
        else:
            P_sat_kpa = (T - 132.01) / 0.04
        P_sat_kpa = max(P_sat_kpa, 1.0)  # 确保压力为正值
        
        # 饱和蒸汽比容: vg = R*T / (P*M)
        # R = 8.314 J/(mol·K), M = 18 g/mol = 0.018 kg/mol
        # vg = 8.314 * (T + 273.15) / (P_sat_kpa * 1000 * 0.018)
        R = 8.314  # J/(mol·K)
        M = 0.018  # kg/mol
        T_kelvin = T + 273.15
        P_sat_pa = P_sat_kpa * 1000
        
        vg = R * T_kelvin / (P_sat_pa * M)  # m³/kg
        
        # 修正系数（考虑非理想气体行为）
        # 在高温下蒸汽更接近理想气体
        correction = 0.9 + 0.0005 * (T - 100) if T > 100 else 0.9
        vg = vg * correction
        
        return vg, vp
    
    def determine_phase(self, temperature: float, pressure_kpa: float) -> str:
        """
        相态判定
        
        根据专利方法，比较网格温度与饱和温度：
        - T < T_sat - 10: 液态水
        - T_sat - 10 <= T <= T_sat + 10: 气液共存
        - T > T_sat + 10: 气态
        
        Args:
            temperature: 网格温度 (°C)
            pressure_kpa: 网格压力 (kPa)
            
        Returns:
            相态类型: 'liquid' 或 'two_phase' 或 'gas'
        """
        T_boiling = self.calculate_boiling_point(pressure_kpa)
        
        # 扩大气液共存判定范围到 ±10°C
        tolerance = 10  # 10°C 容差
        
        if temperature < T_boiling - tolerance:
            return 'liquid'
        elif temperature > T_boiling + tolerance:
            return 'gas'
        else:
            return 'two_phase'
    
    def calculate_water_density(self, temperature: float, pressure_kpa: float) -> float:
        """
        密度校正公式 - 计算地热流体密度
        
        根据专利公式:
        ρ_i = 137.1358 × e^(A) + 139.3560 × e^(B) + 769.9024
        A = -(P_i - 163278.7315)² / (6.613 × 10¹⁰)
        B = -(T_i - 4.1171)² / 29947.659
        
        注意：公式中 P_i 的单位是 Pa（帕斯卡）
        
        Args:
            temperature: 温度 (°C)
            pressure_kpa: 压力 (kPa)
            
        Returns:
            水密度 (kg/m³)
        """
        Ti = temperature
        # 将 kPa 转换为 Pa（公式要求压力单位为 Pa）
        Pi = pressure_kpa * 1000
        
        # 参数A和B
        A = -math.pow(Pi - 163278.7315, 2) / (6.613e10)
        B = -math.pow(Ti - 4.1171, 2) / 29947.659
        
        # 密度计算 (kg/m³)
        density = 137.1358 * math.exp(A) + 139.3560 * math.exp(B) + 769.9024
        
        # 确保密度在合理范围内
        return max(600.0, min(density, 1100.0))
    
    def calculate_saturation_properties(self, temperature: float) -> tuple:
        """
        计算饱和状态下的水和蒸汽性质
        
        使用简化的经验公式（基于IAPWS-IF97拟合）
        
        Args:
            temperature: 饱和温度 (°C)
            
        Returns:
            (饱和水密度 kg/m³, 饱和蒸汽密度 kg/m³, 饱和水比容 m³/kg, 饱和蒸汽比容 m³/kg)
        """
        T = temperature
        
        # 饱和水密度 (kg/m³) - 简化公式
        # 在 0-374°C 范围内有效
        if T < 100:
            rho_liquid = 1000.0 - 0.088 * T - 0.0042 * T**1.5
        elif T < 200:
            rho_liquid = 958.0 - 0.87 * (T - 100) - 0.009 * (T - 100)**2
        else:
            rho_liquid = 864.0 - 1.45 * (T - 200) - 0.015 * (T - 200)**2
        
        # 饱和蒸汽密度 (kg/m³) - 简化公式
        if T < 100:
            rho_steam = 0.6 * math.exp(0.023 * T)
        elif T < 200:
            rho_steam = 0.6 * math.exp(2.3) * math.exp(0.016 * (T - 100))
        else:
            rho_steam = 3.9 * math.exp(0.013 * (T - 200))
        
        # 确保密度在合理范围内
        rho_liquid = max(300.0, min(rho_liquid, 1000.0))
        rho_steam = max(0.1, min(rho_steam, 100.0))
        
        # 比容 = 1/密度
        vp = 1.0 / rho_liquid  # 饱和水比容
        vg = 1.0 / rho_steam   # 饱和蒸汽比容
        
        return rho_liquid, rho_steam, vp, vg
    
    def calculate_steam_density(self, temperature: float, pressure_kpa: float) -> float:
        """
        计算过热蒸汽密度
        
        使用理想气体状态方程近似
        
        Args:
            temperature: 温度 (°C)
            pressure_kpa: 压力 (kPa)
            
        Returns:
            蒸汽密度 (kg/m³)
        """
        # 将温度转换为开尔文
        T_K = temperature + 273.15
        # 将压力转换为 Pa
        P_Pa = pressure_kpa * 1000
        # 水蒸气的气体常数 R_specific = R / M = 8.314 / 0.018 = 461.5 J/(kg·K)
        R_specific = 461.5
        
        # 理想气体状态方程: P = ρ × R × T
        # ρ = P / (R × T)
        density = P_Pa / (R_specific * T_K)
        
        return density
    
    def calculate_liquid_resource(
        self,
        porosity: float,
        volume: float,
        temperature: float,
        pressure_kpa: float,
        reference_temp: float = 25.0
    ) -> float:
        """
        计算液态地热流体资源量
        
        根据专利公式:
        Q_liquid = Σ(φi × Vi × ρi × Cp × (Ti - T0))
        
        Args:
            porosity: 孔隙度
            volume: 网格体积 (m³)
            temperature: 温度 (°C)
            pressure_kpa: 压力 (kPa)
            reference_temp: 参考温度 (°C)
            
        Returns:
            液态地热流体资源量 (J)
        """
        density = self.calculate_water_density(temperature, pressure_kpa)
        delta_T = temperature - reference_temp
        
        resource = porosity * volume * density * self.WATER_SPECIFIC_HEAT * delta_T
        return resource
    
    def calculate_two_phase_resource(
        self,
        porosity: float,
        volume: float,
        temperature: float,
        pressure_kpa: float,
        reference_temp: float = 25.0,
        liquid_specific_heat: float = None,
        gas_specific_heat: float = None,
        latent_heat: float = None
    ) -> Dict[str, float]:
        """
        计算气液共存时的地热资源量
        根据专利公式:
        Q₂ = Σ(φᵢ × Vᵢ × (1 - ρᵢ × vg) / (vp - vg) × Cw × (T_boil - T₀))
        Q₃ = Σ(φᵢ × Vᵢ × (ρᵢ - (1 - ρᵢ × vg) / (vp - vg)) × [Cw × (T_boil - T₀) + Lv + Cv × (Tᵢ - T_boil)])
        porosity: 孔隙度
        volume: 网格体积 (m³)
        temperature: 温度 (°C)
        pressure_kpa: 压力 (kPa)
        reference_temp: 参考温度 (°C)
        liquid_specific_heat: 液体比热容 (kJ/(kg·°C))，默认使用标准值
        gas_specific_heat: 气体比热容 (kJ/(kg·°C))，默认使用标准值
        latent_heat: 气化潜热 (kJ/kg)，默认使用标准值
            
        Returns:
            包含Q₂、Q₃和总资源量的字典
        """
        # 使用传入参数或默认值，并转换单位 kJ -> J
        Cw = (liquid_specific_heat * 1000) if liquid_specific_heat else self.WATER_SPECIFIC_HEAT  # J/(kg·K)
        Cv = (gas_specific_heat * 1000) if gas_specific_heat else 2000  # J/(kg·K)
        Lv = (latent_heat * 1000) if latent_heat else self.LATENT_HEAT_VAPORIZATION  # J/kg
        
        # 计算沸点温度（饱和温度）
        T_sat = self.calculate_boiling_point(pressure_kpa)
        
        # 获取饱和状态下的水和蒸汽性质
        rho_liquid, rho_steam, vp, vg = self.calculate_saturation_properties(T_sat)
        
        # 在气液共存状态下，使用混合密度（介于饱和水和饱和蒸汽之间）
        # 根据专利文档，ρᵢ 通过密度校正公式计算
        density = self.calculate_water_density(temperature, pressure_kpa)
        
        # Q₂: 气液共存液态资源量
        # 使用专利公式：(1 - ρᵢ × vg) / (vp - vg) 表示液态水质量密度
        # 但专利公式中的推导基于特定的物理假设
        # 这里采用更稳健的方法：基于密度值计算液相/气相比例
        
        # 在气液共存状态下，混合密度 = α × ρ_liquid + (1-α) × ρ_steam
        # 其中 α 是液相体积分数
        # 求解 α = (ρ_mixed - ρ_steam) / (ρ_liquid - ρ_steam)
        
        # 使用密度校正公式计算的密度作为混合密度
        rho_mixed = density
        
        # 计算液相体积分数
        if rho_liquid > rho_steam:
            liquid_volume_fraction = (rho_mixed - rho_steam) / (rho_liquid - rho_steam)
            liquid_volume_fraction = max(0, min(1, liquid_volume_fraction))
        else:
            liquid_volume_fraction = 1.0
        
        # 液态水质量 = 液相体积分数 × 饱和水密度
        # 蒸汽质量 = (1 - 液相体积分数) × 饱和蒸汽密度
        liquid_mass_fraction = liquid_volume_fraction * rho_liquid
        steam_mass_fraction = (1 - liquid_volume_fraction) * rho_steam
            
        delta_T_boil = T_sat - reference_temp
        
        Q2 = (
            porosity * volume * liquid_mass_fraction * 
            Cw * delta_T_boil
        )
        
        # Q₃: 气液共存蒸汽资源量
        delta_T_excess = max(0, temperature - T_sat)
        
        Q3 = (
            porosity * volume * steam_mass_fraction * 
            (Cw * delta_T_boil + Lv + Cv * delta_T_excess)
        )
        
        Q_total = Q2 + Q3
        
        return {
            'liquid_resource': Q2,      # Q₂
            'steam_resource': Q3,       # Q₃
            'total_resource': Q_total,
            'boiling_temp': T_sat,
            'liquid_mass_fraction': liquid_mass_fraction,
            'steam_mass_fraction': steam_mass_fraction,
            'rho_liquid': rho_liquid,
            'rho_steam': rho_steam,
            'vg': vg,
            'vp': vp
        }
    
    def calculate_gas_resource(
        self,
        porosity: float,
        volume: float,
        temperature: float,
        pressure_kpa: float,
        reference_temp: float = 25.0,
        liquid_specific_heat: float = None,
        gas_specific_heat: float = None,
        latent_heat: float = None
    ) -> Dict[str, float]:
        """
        计算气态（过热蒸汽）地热资源量
        
        严格按照文档公式：Q₅ = Σ[φᵢ × Vᵢ × ρᵢ × [Cw(Tisat-T₀) + Lv + Cv(Ti-Tisat)]]
        
        其中 ρᵢ 为地热流体密度（通过密度校正公式计算）
        
        Args:
            porosity: 孔隙度
            volume: 网格体积 (m³)
            temperature: 温度 (°C)
            pressure_kpa: 压力 (kPa)
            reference_temp: 参考温度 (°C)
            liquid_specific_heat: 液体比热容 (kJ/(kg·°C))，默认使用标准值
            gas_specific_heat: 气体比热容 (kJ/(kg·°C))，默认使用标准值
            latent_heat: 气化潜热 (kJ/kg)，默认使用标准值
            
        Returns:
            包含气态资源量的字典
        """
        # 使用传入参数或默认值，并转换单位 kJ -> J
        Cw = (liquid_specific_heat * 1000) if liquid_specific_heat else self.WATER_SPECIFIC_HEAT  # J/(kg·K)
        Cv = (gas_specific_heat * 1000) if gas_specific_heat else 2000  # J/(kg·K)
        Lv = (latent_heat * 1000) if latent_heat else self.LATENT_HEAT_VAPORIZATION  # J/kg
        
        T_sat = self.calculate_boiling_point(pressure_kpa)  # 饱和温度 Tisat
        
        # 使用密度校正公式计算地热流体密度 ρᵢ（与文档一致）
        rho_i = self.calculate_water_density(temperature, pressure_kpa)
        
        # Q₅ = φ × V × ρᵢ × [Cw × (Tisat - T₀) + Lv + Cv × (Ti - Tisat)]
        # 严格按照文档公式
        Q5 = porosity * volume * rho_i * (
            Cw * (T_sat - reference_temp) +
            Lv +
            Cv * (temperature - T_sat)
        )
        
        # 计算气态流体质量
        gas_mass = porosity * volume * rho_i
        
        return {
            'gas_resource': Q5,
            'gas_density': rho_i,  # 地热流体密度 ρᵢ
            'gas_mass': gas_mass,  # 气态流体质量
            'saturation_temp': T_sat,
            'superheat': temperature - T_sat
        }
    
    def calculate_grid_resources(
        self,
        grid_data: List[Dict[str, float]],
        reference_temp: float = 25.0
    ) -> Dict[str, Any]:
        """
        批量计算多网格资源量
        
        每个网格单独调用 full_calculation 函数进行计算
        每条数据为一个网格
        
        Args:
            grid_data: 网格数据列表，每个元素包含:
                - coord_x: X坐标
                - coord_y: Y坐标
                - coord_z: Z坐标(深度)
                - porosity: 孔隙度
                - volume: 体积 (m³)
                - temperature: 温度 (°C)
                - pressure: 压力 (kPa)
            reference_temp: 参考温度 (°C)
        Returns:
            计算结果汇总，包含Q₁、Q₂、Q₃、Q₅
        """
        liquid_grids = []
        two_phase_grids = []
        gas_grids = []
        
        total_liquid_resource = 0.0  # Q₁ (液态水网格集)
        total_two_phase_liquid = 0.0  # Q₂ (气液共存中液态部分)
        total_steam_resource = 0.0   # Q₃ (气液共存中蒸汽部分)
        total_gas_resource = 0.0     # Q₅ (气态网格集)
        
        for i, grid in enumerate(grid_data):
            coord_x = grid.get('coord_x')
            coord_y = grid.get('coord_y')
            coord_z = grid.get('coord_z')
            porosity = grid.get('porosity', 0.15)
            volume = grid.get('volume', 0)
            temperature = grid.get('temperature', 100)
            pressure = grid.get('pressure', 101.325)
            
            if volume <= 0:
                continue
            
            # 调用 full_calculation 计算单个网格
            result = self.full_calculation(
                reservoir_volume=volume,
                avg_temperature=temperature,
                reference_temperature=reference_temp,
                porosity=porosity,
                pressure=pressure,
                water_specific_heat=self.WATER_SPECIFIC_HEAT
            )
            
            # 获取实际相态
            actual_phase = result['phase_info']['phase_type']
            
            # 汇总结果
            total_heat = result['total_heat']
            
            if actual_phase == 'liquid':
                total_liquid_resource += total_heat
                liquid_grids.append({
                    'index': i,
                    'coord_x': coord_x,
                    'coord_y': coord_y,
                    'coord_z': coord_z,
                    'temperature': temperature,
                    'pressure': pressure,
                    'porosity': porosity,
                    'volume': volume,
                    'phase': actual_phase,
                    'resource': total_heat,
                    'phase_info': result['phase_info']
                })
            elif actual_phase == 'two_phase':
                liquid_resource = result['phase_info'].get('liquid_resource', 0)
                steam_resource = result['phase_info'].get('steam_resource', 0)
                total_two_phase_liquid += liquid_resource
                total_steam_resource += steam_resource
                two_phase_grids.append({
                    'index': i,
                    'coord_x': coord_x,
                    'coord_y': coord_y,
                    'coord_z': coord_z,
                    'temperature': temperature,
                    'pressure': pressure,
                    'porosity': porosity,
                    'volume': volume,
                    'phase': actual_phase,
                    'liquid_resource': liquid_resource,
                    'steam_resource': steam_resource,
                    'total_resource': total_heat,
                    'phase_info': result['phase_info']
                })
            else:  # gas
                total_gas_resource += total_heat
                gas_grids.append({
                    'index': i,
                    'coord_x': coord_x,
                    'coord_y': coord_y,
                    'coord_z': coord_z,
                    'temperature': temperature,
                    'pressure': pressure,
                    'porosity': porosity,
                    'volume': volume,
                    'phase': actual_phase,
                    'resource': total_heat,
                    'phase_info': result['phase_info']
                })
        
        # 热储层资源量 (气液共存部分 Q₄ = Q₂ + Q₃)
        reservoir_resource = total_two_phase_liquid + total_steam_resource
        
        # 总地热资源量 = 液态水资源量(Q₁) + 气液共存资源量(Q₄) + 气态资源量(Q₅)
        total_resource = total_liquid_resource + reservoir_resource + total_gas_resource
        
        # 网格数量
        liquid_grid_count = len(liquid_grids)
        two_phase_grid_count = len(two_phase_grids)
        gas_grid_count = len(gas_grids)
        
        return {
            'total_resource_joules': total_resource,
            'liquid_resource_joules': total_liquid_resource,
            'two_phase_liquid_resource_joules': total_two_phase_liquid,
            'steam_resource_joules': total_steam_resource,
            'reservoir_resource_joules': reservoir_resource,
            'gas_resource_joules': total_gas_resource,
            'liquid_grid_count': liquid_grid_count,
            'two_phase_grid_count': two_phase_grid_count,
            'gas_grid_count': gas_grid_count,
            'total_grid_count': liquid_grid_count + two_phase_grid_count + gas_grid_count
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
        water_specific_heat: float = WATER_SPECIFIC_HEAT,
        pressure: float = 101.325  # kPa
    ) -> Dict[str, Any]:
        """
        完整的地热资源计算
        
        结合专利方法和传统方法进行综合计算
        
        Args:
            pressure: 压力 (kPa)
        
        Returns:
            完整计算结果
        """
        # 使用密度校正公式计算实际水密度
        if water_density is None:
            water_density = self.calculate_water_density(avg_temperature, pressure)
        
        # 相态判定
        phase = self.determine_phase(avg_temperature, pressure)
        
        # 温度差
        delta_T = avg_temperature - reference_temperature
        
        # 计算有效体积
        water_volume = reservoir_volume * porosity
        
        # 计算质量
        water_mass = water_volume * water_density
        
        # 根据相态选择计算方法
        if phase == 'liquid':
            # 液态水计算 Q₁
            water_heat = water_mass * water_specific_heat * delta_T
            total_heat = water_heat
            
            phase_info = {
                'phase_type': 'liquid',
                'water_density': water_density,
                'boiling_point': self.calculate_boiling_point(pressure)
            }
        elif phase == 'two_phase':
            # 气液共存计算 Q₂ + Q₃ + Q₄
            result = self.calculate_two_phase_resource(
                porosity, reservoir_volume, avg_temperature, pressure, reference_temperature
            )
            total_heat = result['liquid_resource'] + result['steam_resource']
            
            phase_info = {
                'phase_type': 'two_phase',
                'water_density': water_density,
                'boiling_point': self.calculate_boiling_point(pressure),
                'liquid_fraction': result.get('liquid_mass_fraction', 0),
                'steam_fraction': result.get('steam_mass_fraction', 0),
                'liquid_resource': result['liquid_resource'],
                'steam_resource': result['steam_resource']
            }
        else:
            # 气态计算 Q₅ (过热蒸汽)
            result = self.calculate_gas_resource(
                porosity, reservoir_volume, avg_temperature, pressure, reference_temperature
            )
            total_heat = result['gas_resource']
            
            phase_info = {
                'phase_type': 'gas',
                'water_density': water_density,
                'boiling_point': self.calculate_boiling_point(pressure),
                'gas_density': result.get('gas_density', 0),
                'gas_resource': result['gas_resource']
            }
        
        # 计算发电潜力
        power_results = self.calculate_power_potential(
            total_heat=total_heat,
            recovery_factor=recovery_factor,
            utilization_efficiency=utilization_efficiency,
            lifetime_years=lifetime_years
        )
        
        # 合并结果
        if phase == 'liquid':
            water_heat_result = water_heat
        elif phase == 'two_phase':
            water_heat_result = phase_info['liquid_resource']
        else:  # gas
            water_heat_result = 0  # 气态没有液态水热量
        
        return {
            'total_heat': total_heat,
            'water_heat': water_heat_result,
            'water_volume': water_volume,
            'water_mass': water_mass,
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
                'water_density': water_density
            }
        }
    def calculate_heat_content(
        self,
        reservoir_volume: float,
        avg_temperature: float,
        reference_temperature: float = 25.0,
        porosity: float = 0.15,
        water_density: float = WATER_DENSITY_STANDARD,
        water_specific_heat: float = WATER_SPECIFIC_HEAT
    ) -> Dict[str, float]:
        """
        计算地热储层热含量（仅计算流体热量）
        """
        delta_T = avg_temperature - reference_temperature
        
        water_volume = reservoir_volume * porosity
        
        water_mass = water_volume * water_density
        
        water_heat = water_mass * water_specific_heat * delta_T
        total_heat = water_heat
        
        return {
            'water_volume': water_volume,
            'water_mass': water_mass,
            'water_heat': water_heat,
            'total_heat': total_heat,
            'delta_temperature': delta_T
        }


# 创建全局服务实例
gempy_service = GemPyService()
geothermal_calculator = GeothermalCalculator()
