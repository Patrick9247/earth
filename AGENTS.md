# AGENTS.md

## 项目概览

地热流体资源建模系统 - 基于 FastAPI + Vue3 + GemPy 的全栈应用，用于三维地质建模和地热资源计算。

## 技术栈

### 后端
- **框架**: FastAPI 0.109.0
- **ORM**: SQLAlchemy 2.0.25
- **数据库**: MySQL (通过 PyMySQL 连接)
- **地质建模**: GemPy (模拟模式支持)
- **数据验证**: Pydantic 2.5.3
- **数据处理**: NumPy, Pandas, SciPy

### 前端
- **框架**: Vue 3.4
- **语言**: TypeScript 5.3
- **构建工具**: Vite 5.1
- **UI库**: Element Plus 2.5
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **样式**: Tailwind CSS 3.4

## 项目结构

```
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── routers/         # API 路由
│   │   │   ├── geological.py    # 地质层管理
│   │   │   ├── drill_holes.py   # 钻孔数据
│   │   │   ├── model_configs.py # 模型配置
│   │   │   ├── gempy.py         # GemPy建模与计算
│   │   │   └── export.py        # 数据导出
│   │   ├── config.py        # 应用配置
│   │   ├── database.py      # 数据库连接
│   │   ├── models.py        # SQLAlchemy 模型
│   │   ├── schemas.py       # Pydantic 模型
│   │   ├── gempy_service.py # GemPy 服务
│   │   └── utils.py         # 工具函数
│   ├── main.py              # FastAPI 入口
│   ├── init_db.py           # 数据库初始化
│   ├── static/              # 前端构建产物
│   └── requirements.txt     # Python 依赖
│
├── frontend/                # Vue3 前端
│   ├── src/
│   │   ├── api/             # API 请求
│   │   ├── components/      # 组件
│   │   ├── views/           # 页面视图
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── types/           # TypeScript 类型
│   │   ├── utils/           # 工具函数
│   │   └── assets/          # 静态资源
│   ├── package.json
│   └── vite.config.ts
│
└── .coze                    # Coze 配置
```

## 构建和运行命令

### 开发环境
```bash
# 构建并启动
coze dev

# 或手动启动
cd backend && pip install -r requirements.txt
cd ../frontend && pnpm install && pnpm build
cd ../backend && python main.py
```

### 生产环境
```bash
coze build && coze start
```

## API 接口

### 地质层管理
- `GET /api/layers/` - 获取所有地质层
- `POST /api/layers/` - 创建地质层
- `PUT /api/layers/{id}` - 更新地质层
- `DELETE /api/layers/{id}` - 删除地质层

### 钻孔数据
- `GET /api/drill-holes/` - 获取所有钻孔
- `POST /api/drill-holes/` - 创建钻孔
- `POST /api/drill-holes/batch` - 批量创建

### 模型配置
- `GET /api/model-configs/` - 获取所有配置
- `POST /api/model-configs/` - 创建配置

### GemPy 建模
- `POST /api/gempy/model/create` - 创建地质模型
- `POST /api/gempy/calculate` - 计算地热资源
- `GET /api/gempy/quick-calc` - 快速估算
- `GET /api/gempy/results` - 获取计算结果

### 数据导出
- `GET /api/export/layers/csv` - 导出地质层(CSV)
- `GET /api/export/drill-holes/csv` - 导出钻孔数据(CSV)
- `GET /api/export/results/csv` - 导出计算结果(CSV)
- `GET /api/export/all/json` - 导出所有数据(JSON)
- `GET /api/export/report` - 生成汇总报告

### 系统接口
- `GET /api/health` - 健康检查
- `GET /api/info` - 系统信息

## 核心功能模块

### 1. 地质层管理 (`backend/app/routers/geological.py`)
- 管理地层数据（名称、深度、物性参数）
- 支持孔隙度、渗透率、热导率等参数

### 2. 钻孔数据管理 (`backend/app/routers/drill_holes.py`)
- 钻孔位置坐标
- 温度和地温梯度数据
- 批量导入支持

### 3. GemPy 地质建模 (`backend/app/gempy_service.py`)
- 三维地质结构建模
- 支持 GemPy 或模拟模式
- 地热资源计算核心算法

### 4. 数据导出 (`backend/app/routers/export.py`)
- CSV/JSON 格式导出
- 汇总报告生成
- 支持模拟数据模式

### 5. 工具函数 (`backend/app/utils.py`)
- 温度插值计算
- 热流密度计算
- 采收率估算
- 合成数据生成
- 单位转换

### 6. 前端页面
- **首页**: 系统概览、快速计算
- **地质层管理**: CRUD 操作
- **钻孔数据**: 数据管理和位置可视化
- **地质建模**: 模型参数配置
- **资源计算**: 详细参数计算
- **计算结果**: 历史记录管理
- **系统设置**: 参数配置、数据导出

## 数据库配置

需要配置 MySQL 数据库：

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=geothermal_db
```

## 代码风格指南

### Python
- 使用 Pydantic 进行数据验证
- SQLAlchemy ORM 模型
- FastAPI 路由函数使用 async def
- 所有新模型字段避免使用 `metadata` (SQLAlchemy保留字)

### TypeScript/Vue
- Vue 3 Composition API
- TypeScript 类型定义
- Element Plus UI 组件
- 使用 `computed` 处理 v-model 的复杂表达式

## 常见问题

### MySQL 连接失败
- 应用会在数据库不可用时继续运行（模拟模式）
- 前端和导出API会使用模拟数据

### GemPy 不可用
- 服务会自动切换到模拟模式
- 计算结果仍然有效

### 前端构建错误
- 检查 TypeScript 类型定义
- v-model 不能使用复杂表达式，改用 computed

## 访问地址

- 前端页面: http://localhost:5000
- API 文档: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc
