import axios from 'axios'
import type { AxiosInstance, AxiosResponse, AxiosError } from 'axios'
import router from '@/router'
// 创建 axios 实例
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 60000,  // 60秒超时，支持大量网格计算
  headers: {
    'Content-Type': 'application/json'
  }
})
// 请求拦截器 - 添加 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)
// 响应拦截器 - 处理 token 过期
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    const status = error.response?.status
    const detail = ((error.response?.data as any)?.detail) ?? ((error.response?.data as any)?.message) ?? ''
    // 如果是未授权、后端返回重定向，或返回的信息包含 Token 过期，清理登录信息并跳转登录页
    if (status === 401 || status === 307 || (typeof detail === 'string' && detail.includes('Token已过期'))) {
      try {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      } catch (e) {
        // ignore
      }
      // 使用路由跳转到登录页（SPA 中主动处理）
      try {
        router.push('/login')
      } catch (e) {
        // ignore
      }
    }
    return Promise.reject(error)
  }
)
//  地质层 API 
export const layersApi = {
  getAll: () => api.get('/layers/'),
  getOne: (id: number) => api.get(`/layers/${id}`),
  create: (data: any) => api.post('/layers/', data),
  update: (id: number, data: any) => api.put(`/layers/${id}`, data),
  delete: (id: number) => api.delete(`/layers/${id}`)
  ,
  // 获取不同名称的地质层数量
  getDistinctCount: () => api.get('/layers/distinct-count')
}
//  钻孔数据 API 
export const drillHolesApi = {
  getAll: () => api.get('/drill-holes/'),
  getOne: (id: number) => api.get(`/drill-holes/${id}`),
  create: (data: any) => api.post('/drill-holes/', data),
  batchCreate: (data: any[]) => api.post('/drill-holes/batch', data),
  update: (id: number, data: any) => api.put(`/drill-holes/${id}`, data),
  delete: (id: number) => api.delete(`/drill-holes/${id}`),
  createWithDetails: (data: any) => api.post('/drill-holes/with-details', data)
}
// 网格计算api
export const gempyApi = {
  calculate: (data: any) => api.post('/gempy/calculate', data),
  calculateGrid: (data: any) => api.post('/gempy/calculate-grid', data),
  getResults: () => api.get('/gempy/results'),
  getResult: (id: number) => api.get(`/gempy/results/${id}`),
  deleteResult: (id: number) => api.delete(`/gempy/results/${id}`),
  quickCalc: (params: any) => api.get('/gempy/quick-calc', { params }),
  phaseDetermination: (temperature: number, pressure: number) =>
    api.get('/gempy/phase-determination', { params: { temperature, pressure } }),
  getResultCount: () => api.get('/gempy/results/count')
}
//  网格计算表单 API 
export const gridCalcApi = {
  // 表单操作
  getAll: () => api.get('/grid-calculations/'),
  getOne: (id: number) => api.get(`/grid-calculations/${id}`),
  create: (data: any) => api.post('/grid-calculations/', data),
  update: (id: number, data: any) => api.put(`/grid-calculations/${id}`, data),
  delete: (id: number) => api.delete(`/grid-calculations/${id}`),
  // 网格操作
  getGrids: (calcId: number) => api.get(`/grid-calculations/${calcId}/grids`),
  addGrid: (calcId: number, data: any) => api.post(`/grid-calculations/${calcId}/grids`, data),
  updateGrid: (calcId: number, itemId: number, data: any) => api.put(`/grid-calculations/${calcId}/grids/${itemId}`, data),
  deleteGrid: (calcId: number, itemId: number) => api.delete(`/grid-calculations/${calcId}/grids/${itemId}`)
  ,
  // 获取所有网格项总数
  getTotalGridItems: () => api.get('/grid-calculations/grids/count')
}

//  钻孔详情 API 
export const drillHoleDetailApi = {
  getDetail: (id: number) => api.get(`/drill-holes/${id}/detail`)
}
//  用户管理 API 
export const usersApi = {
  login: (username: string, password: string) =>
    api.post('/users/login', { username, password }),
  register: (data: any) => api.post('/users/register', data),
  getMe: () => api.get('/users/me'),
  getAll: () => api.get('/users/'),
  getOne: (id: number) => api.get(`/users/${id}`),
  create: (data: any) => api.post('/users/', data),
  update: (id: number, data: any) => api.put(`/users/${id}`, data),
  delete: (id: number) => api.delete(`/users/${id}`),
  toggleActive: (id: number) => api.patch(`/users/${id}/toggle-active`)
}
//  地层分层数据 API 
export const stratigraphicApi = {
  getAll: (holeName?: string) => {
    const params = holeName ? `?hole_name=${encodeURIComponent(holeName)}` : ''
    return api.get(`/stratigraphic/list${params}`)
  },
  getHoles: () => api.get('/stratigraphic/holes'),
  getOne: (id: number) => api.get(`/stratigraphic/${id}`),
  create: (data: any) => api.post('/stratigraphic/create', data),
  update: (id: number, data: any) => api.put(`/stratigraphic/${id}`, data),
  delete: (id: number) => api.delete(`/stratigraphic/${id}`),
  deleteByHole: (holeName: string) => api.delete(`/stratigraphic/hole/${encodeURIComponent(holeName)}`),
  importCsv: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/stratigraphic/import-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  batchCreate: (layers: any[]) => api.post('/stratigraphic/batch-create', layers),
  clearAll: () => api.delete('/stratigraphic/clear-all')
}
export default api
