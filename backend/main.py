"""
地热流体资源建模系统
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import os
from app.config import settings
from app.database import init_db, SessionLocal
from app.models import GeologicalLayer
from app.routers import gempy, grid_calculations, users, stratigraphic

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
        
        # 检查是否有数据，没有则插入示例数据
        db = SessionLocal()
        try:
            if db.query(GeologicalLayer).count() == 0:
                
                # 插入地质层数据
                layers = [
                    GeologicalLayer(name="第四系覆盖层", layer_type="沉积层", depth_top=0, depth_bottom=50, porosity=0.25, permeability=100, thermal_conductivity=1.8, color="#90EE90"),
                    GeologicalLayer(name="砂岩储层", layer_type="储层", depth_top=50, depth_bottom=500, porosity=0.18, permeability=50, thermal_conductivity=2.5, color="#FFD700"),
                    GeologicalLayer(name="泥岩盖层", layer_type="盖层", depth_top=500, depth_bottom=800, porosity=0.08, permeability=1, thermal_conductivity=2.0, color="#87CEEB"),
                    GeologicalLayer(name="花岗岩基底", layer_type="基岩", depth_top=800, depth_bottom=2000, porosity=0.05, permeability=0.5, thermal_conductivity=3.2, color="#CD5C5C"),
                ]
                db.add_all(layers)
            
        except Exception as e:
            logger.warning(f"Failed to insert sample data: {e}")
        finally:
            db.close()       
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}. Running without database.")
    yield
    # 关闭时清理资源
    logger.info("Shutting down...")
# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""地热流体资源计算系统""",
    lifespan=lifespan
)

# 配置 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（用于服务前端）
frontend_dist = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

# 注册路由
app.include_router(gempy.router)
app.include_router(grid_calculations.router)
app.include_router(users.router)
app.include_router(stratigraphic.router)

@app.get("/")
async def root():
    """根路径 - 返回前端页面或API信息"""
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        from fastapi.responses import FileResponse
        return FileResponse(index_file)
    
    return {
        "message": f"欢迎使用{settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@app.get("/api/info")
async def get_app_info():
    """获取应用信息"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "features": [
            "geological_layers",
            "drill_holes",
            "gempy_modeling",
            "geothermal_calculation"
        ]
    }

# SPA fallback - 所有非 API 路由返回 index.html
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """SPA 路由回退 - 返回前端页面"""
    # 如果是 API 路由但没匹配到，返回 404
    if full_path.startswith("api/"):
        return {"detail": "Not Found"}
    # 返回前端 index.html
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"detail": "Frontend not found"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("DEPLOY_RUN_PORT", "5000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
