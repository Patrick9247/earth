# 地热流体资源建模系统

基于 FastAPI + Vue3 + GemPy 的地热流体资源建模与计算系统。

## 项目结构

```
.
├── backend/                # 后端 FastAPI 项目
│   ├── app/
│   │   ├── routers/        # API 路由
│   │   ├── config.py       # 配置管理
│   │   ├── database.py     # 数据库连接
│   │   ├── models.py       # SQLAlchemy 模型
│   │   ├── schemas.py      # Pydantic 模型
│   │   └── gempy_service.py # GemPy 服务
│   ├── main.py             # FastAPI 入口
│   └── requirements.txt    # Python 依赖
│
├── frontend/               # 前端 Vue3 项目
│   ├── src/
│   │   ├── api/            # API 请求
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面视图
│   │   ├── router/         # 路由配置
│   │   └── assets/         # 静态资源
│   ├── package.json
│   └── vite.config.ts
│
└── .coze                   # Coze 配置文件
```

## 核心功能

### 1. 地质层管理
- 地质层数据的 CRUD 操作
- 物性参数管理（孔隙度、渗透率、热导率）

### 2. 钻孔数据管理
- 钻孔位置和深度数据
- 温度和地温梯度测量

### 3. 三维地质建模
- 基于 GemPy 构建地质模型
- 模型参数配置

### 4. 地热资源计算
- 热含量计算
- 发电潜力评估
- 快速资源估算

### 5. 计算结果管理
- 历史计算记录
- 结果统计和分析

## 技术栈

### 后端
- **FastAPI**: 现代 Python Web 框架
- **SQLAlchemy**: ORM
- **MySQL**: 数据库
- **GemPy**: 三维地质建模
- **Pydantic**: 数据验证

### 前端
- **Vue 3**: 前端框架
- **TypeScript**: 类型安全
- **Element Plus**: UI 组件库
- **Vite**: 构建工具
- **Axios**: HTTP 客户端

## 开发指南

### 环境要求
- Python 3.11+
- Node.js 20+
- MySQL 8.0+

### 数据库配置
创建 `.env` 文件：
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=geothermal_db
```

### 运行项目

```bash
# 安装依赖并启动（使用 coze cli）
coze dev

# 或手动启动
cd backend && pip install -r requirements.txt
cd ../frontend && pnpm install && pnpm build
cd ../backend && python main.py
```

### 访问地址
- 前端页面: http://localhost:5000
- API 文档: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

## API 接口

### 地质层
- `GET /api/layers/` - 获取所有地质层
- `POST /api/layers/` - 创建地质层
- `PUT /api/layers/{id}` - 更新地质层
- `DELETE /api/layers/{id}` - 删除地质层

### 钻孔数据
- `GET /api/drill-holes/` - 获取所有钻孔
- `POST /api/drill-holes/` - 创建钻孔
- `POST /api/drill-holes/batch` - 批量创建

### GemPy 建模
- `POST /api/gempy/model/create` - 创建地质模型
- `POST /api/gempy/calculate` - 计算地热资源
- `GET /api/gempy/quick-calc` - 快速估算

## 地热资源计算方法

### 热含量计算
```
Q = [(1-φ)ρrCpr + φρwCpw] × V × ΔT
```
- Q: 热含量 (J)
- φ: 孔隙度
- ρr, ρw: 岩石和水密度 (kg/m³)
- Cpr, Cpw: 岩石和水比热容 (J/kg·K)
- V: 储层体积 (m³)
- ΔT: 温度差 (K)

### 发电潜力
```
P = (Q × R × η) / (t × 365.25 × 24 × 3600 × 10^6) MW
```
- P: 发电潜力 (MW)
- R: 采收率
- η: 利用效率
- t: 开采年限

## 许可证

MIT License
