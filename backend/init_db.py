"""
数据库初始化脚本
用于创建表结构和初始数据
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import GeologicalLayer, DrillHole, ModelConfig
from app.utils import generate_synthetic_drill_data


def create_tables():
    """创建所有表"""
    # 确保数据库目录存在
    if settings.USE_SQLITE:
        db_dir = os.path.dirname(settings.SQLITE_DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created database directory: {db_dir}")
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def insert_sample_data():
    """插入示例数据"""
    db = SessionLocal()
    
    try:
        # 检查是否已有数据
        if db.query(GeologicalLayer).count() > 0:
            print("Sample data already exists, skipping...")
            return
        
        print("Inserting sample data...")
        
        # 插入地质层数据
        layers = [
            GeologicalLayer(
                name="第四系覆盖层",
                layer_type="沉积层",
                depth_top=0,
                depth_bottom=50,
                porosity=0.25,
                permeability=100,
                thermal_conductivity=1.8,
                color="#90EE90"
            ),
            GeologicalLayer(
                name="砂岩储层",
                layer_type="储层",
                depth_top=50,
                depth_bottom=500,
                porosity=0.18,
                permeability=50,
                thermal_conductivity=2.5,
                color="#FFD700"
            ),
            GeologicalLayer(
                name="泥岩盖层",
                layer_type="盖层",
                depth_top=500,
                depth_bottom=800,
                porosity=0.08,
                permeability=1,
                thermal_conductivity=2.0,
                color="#87CEEB"
            ),
            GeologicalLayer(
                name="花岗岩基底",
                layer_type="基岩",
                depth_top=800,
                depth_bottom=2000,
                porosity=0.05,
                permeability=0.5,
                thermal_conductivity=3.2,
                color="#CD5C5C"
            ),
        ]
        
        db.add_all(layers)
        
        # 插入钻孔数据
        drill_holes_data = generate_synthetic_drill_data(
            num_holes=10,
            extent=(0, 0, 1000, 1000),
            depth_range=(600, 1500),
            gradient_range=(5.5, 7.5)
        )
        
        drill_holes = [DrillHole(**dh) for dh in drill_holes_data]
        db.add_all(drill_holes)
        
        # 插入模型配置
        config = ModelConfig(
            name="默认配置",
            grid_resolution=50,
            extent_x_min=0,
            extent_x_max=1000,
            extent_y_min=0,
            extent_y_max=1000,
            extent_z_min=-2000,
            extent_z_max=100
        )
        db.add(config)
        
        db.commit()
        print("Sample data inserted successfully!")
        
    except Exception as e:
        print(f"Error inserting sample data: {e}")
        db.rollback()
    finally:
        db.close()


def init_database():
    """初始化数据库"""
    create_tables()
    insert_sample_data()


if __name__ == "__main__":
    init_database()
