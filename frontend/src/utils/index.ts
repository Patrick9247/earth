/**
 * 工具函数
 */

/**
 * 格式化数字（科学计数法）
 */
export function formatScientific(value: number, decimals: number = 2): string {
  if (value === 0) return '0'
  const absValue = Math.abs(value)
  if (absValue >= 1e6 || absValue < 1e-3) {
    return value.toExponential(decimals)
  }
  return value.toFixed(decimals)
}

/**
 * 格式化大数字（带单位）
 */
export function formatLargeNumber(value: number): string {
  const units = ['', 'K', 'M', 'G', 'T', 'P', 'E']
  let unitIndex = 0
  let absValue = Math.abs(value)
  
  while (absValue >= 1000 && unitIndex < units.length - 1) {
    absValue /= 1000
    unitIndex++
  }
  
  return `${absValue.toFixed(2)} ${units[unitIndex]}`
}

/**
 * 格式化能量值（J -> EJ）
 */
export function formatEnergy(joules: number): string {
  const ej = joules / 1e18
  if (ej >= 1) {
    return `${ej.toFixed(2)} EJ`
  }
  const pj = joules / 1e15
  if (pj >= 1) {
    return `${pj.toFixed(2)} PJ`
  }
  const tj = joules / 1e12
  return `${tj.toFixed(2)} TJ`
}

/**
 * 格式化功率值（W -> MW）
 */
export function formatPower(watts: number): string {
  const mw = watts / 1e6
  if (mw >= 1) {
    return `${mw.toFixed(2)} MW`
  }
  const kw = watts / 1e3
  return `${kw.toFixed(2)} kW`
}

/**
 * 格式化体积值（m³）
 */
export function formatVolume(m3: number): string {
  if (m3 >= 1e9) {
    return `${(m3 / 1e9).toFixed(2)} km³`
  }
  if (m3 >= 1e6) {
    return `${(m3 / 1e6).toFixed(2)} × 10⁶ m³`
  }
  return `${m3.toFixed(2)} m³`
}

/**
 * 格式化温度值
 */
export function formatTemperature(celsius: number): string {
  return `${celsius.toFixed(1)}°C`
}

/**
 * 格式化百分比
 */
export function formatPercent(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * 计算地温梯度
 */
export function calculateGradient(
  surfaceTemp: number,
  bottomTemp: number,
  depth: number
): number {
  if (depth <= 0) return 0
  return ((bottomTemp - surfaceTemp) / depth) * 100
}

/**
 * 估算地热资源（简化公式）
 */
export function estimateGeothermalResource(params: {
  volume: number
  temperature: number
  referenceTemp?: number
  porosity?: number
  recoveryFactor?: number
}): {
  heatContent: number
  extractableHeat: number
  powerPotential: number
} {
  const {
    volume,
    temperature,
    referenceTemp = 25,
    porosity = 0.15,
    recoveryFactor = 0.25
  } = params

  const deltaT = temperature - referenceTemp
  
  // 物理常数
  const waterDensity = 1000 // kg/m³
  const rockDensity = 2600 // kg/m³
  const waterSpecificHeat = 4186 // J/(kg·K)
  const rockSpecificHeat = 880 // J/(kg·K)
  
  // 计算热含量
  const waterVolume = volume * porosity
  const rockVolume = volume * (1 - porosity)
  const waterMass = waterVolume * waterDensity
  const rockMass = rockVolume * rockDensity
  
  const heatContent = 
    (waterMass * waterSpecificHeat + rockMass * rockSpecificHeat) * deltaT
  
  const extractableHeat = heatContent * recoveryFactor
  
  // 假设30年开采期，10%利用效率
  const lifetimeYears = 30
  const utilizationEfficiency = 0.1
  const secondsPerYear = 365.25 * 24 * 3600
  
  const annualEnergy = extractableHeat * utilizationEfficiency / lifetimeYears
  const powerPotential = annualEnergy / secondsPerYear / 1e6 // MW
  
  return {
    heatContent,
    extractableHeat,
    powerPotential
  }
}

/**
 * 颜色插值（根据温度）
 */
export function getTemperatureColor(temperature: number): string {
  if (temperature < 100) return '#67c23a' // 绿色 - 低温
  if (temperature < 150) return '#e6a23c' // 橙色 - 中温
  if (temperature < 200) return '#f56c6c' // 红色 - 高温
  return '#c45656' // 深红色 - 超高温
}

/**
 * 生成随机颜色
 */
export function randomColor(): string {
  const colors = [
    '#409eff', '#67c23a', '#e6a23c', '#f56c6c',
    '#909399', '#00d4aa', '#9b59b6', '#3498db'
  ]
  return colors[Math.floor(Math.random() * colors.length)]
}

/**
 * 深拷贝
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}

/**
 * 防抖函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null
  
  return function (this: any, ...args: Parameters<T>) {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func.apply(this, args), wait)
  }
}

/**
 * 节流函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false
  
  return function (this: any, ...args: Parameters<T>) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}
