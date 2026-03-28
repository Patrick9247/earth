/**
 * 地热资源相关类型定义
 */

// 地质层
export interface GeologicalLayer {
  id: number
  name: string
  layer_type?: string
  depth_top?: number
  depth_bottom?: number
  porosity?: number
  permeability?: number
  thermal_conductivity?: number
  color?: string
  layer_metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

// 钻孔数据
export interface DrillHole {
  id: number
  name: string
  location_x: number
  location_y: number
  location_z?: number
  depth: number
  temperature?: number
  gradient?: number
  description?: string
  created_at: string
  updated_at: string
}

// 地热资源计算结果
export interface GeothermalResource {
  id: number
  name: string
  model_type?: string
  volume?: number
  temperature_avg?: number
  temperature_max?: number
  heat_content?: number
  extractable_heat?: number
  power_potential?: number
  lifetime_years?: number
  parameters?: Record<string, any>
  result_data?: Record<string, any>
  created_at: string
}

// 模型配置
export interface ModelConfig {
  id: number
  name: string
  grid_resolution: number
  extent_x_min: number
  extent_x_max: number
  extent_y_min: number
  extent_y_max: number
  extent_z_min: number
  extent_z_max: number
  config_data?: Record<string, any>
  created_at: string
  updated_at: string
}

// GemPy 模型请求
export interface GemPyModelRequest {
  config_id?: number
  layers: Partial<GeologicalLayer>[]
  drill_holes: Partial<DrillHole>[]
  grid_resolution: number
}

// GemPy 模型响应
export interface GemPyModelResponse {
  success: boolean
  message: string
  model_id?: number
  mesh_data?: Record<string, any>
  statistics?: Record<string, any>
}

// 地热计算请求
export interface GeothermalCalculationRequest {
  model_id: number
  reservoir_volume: number
  avg_temperature: number
  reference_temperature?: number
  porosity?: number
  water_density?: number
  rock_density?: number
  water_specific_heat?: number
  rock_specific_heat?: number
  recovery_factor?: number
  utilization_efficiency?: number
  lifetime_years?: number
}

// API 响应
export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
}
