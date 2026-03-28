import axios from 'axios'
import type { AxiosInstance, AxiosResponse } from 'axios'

// 创建 axios 实例
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ==================== 地质层 API ====================
export const layersApi = {
  getAll: () => api.get('/layers/'),
  getOne: (id: number) => api.get(`/layers/${id}`),
  create: (data: any) => api.post('/layers/', data),
  update: (id: number, data: any) => api.put(`/layers/${id}`, data),
  delete: (id: number) => api.delete(`/layers/${id}`)
}

// ==================== 钻孔数据 API ====================
export const drillHolesApi = {
  getAll: () => api.get('/drill-holes/'),
  getOne: (id: number) => api.get(`/drill-holes/${id}`),
  create: (data: any) => api.post('/drill-holes/', data),
  batchCreate: (data: any[]) => api.post('/drill-holes/batch', data),
  update: (id: number, data: any) => api.put(`/drill-holes/${id}`, data),
  delete: (id: number) => api.delete(`/drill-holes/${id}`)
}

// ==================== 模型配置 API ====================
export const modelConfigsApi = {
  getAll: () => api.get('/model-configs/'),
  getOne: (id: number) => api.get(`/model-configs/${id}`),
  create: (data: any) => api.post('/model-configs/', data),
  update: (id: number, data: any) => api.put(`/model-configs/${id}`, data),
  delete: (id: number) => api.delete(`/model-configs/${id}`)
}

// ==================== GemPy 建模 API ====================
export const gempyApi = {
  createModel: (data: any) => api.post('/gempy/model/create', data),
  calculate: (data: any) => api.post('/gempy/calculate', data),
  calculateGrid: (data: any) => api.post('/gempy/calculate-grid', data),
  getResults: () => api.get('/gempy/results'),
  getResult: (id: number) => api.get(`/gempy/results/${id}`),
  deleteResult: (id: number) => api.delete(`/gempy/results/${id}`),
  quickCalc: (params: any) => api.get('/gempy/quick-calc', { params }),
  phaseDetermination: (temperature: number, pressure: number) => 
    api.get('/gempy/phase-determination', { params: { temperature, pressure } })
}

export default api
