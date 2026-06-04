"""
地层分层数据 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import csv
import io
from datetime import datetime

from ..database import get_db
from ..models import StratigraphicLayer
from ..schemas import (
    StratigraphicLayerBase,
    StratigraphicLayerCreate,
    StratigraphicLayerUpdate,
    StratigraphicLayerResponse,
    MessageResponse
)

router = APIRouter(
    prefix="/api/stratigraphic",
    tags=["地层分层数据"]
)


@router.get("/list", response_model=List[StratigraphicLayerResponse])
def get_all_layers(
    hole_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取所有地层分层数据，可按钻孔名称筛选"""
    query = db.query(StratigraphicLayer)
    if hole_name:
        query = query.filter(StratigraphicLayer.hole_name == hole_name)
    return query.order_by(StratigraphicLayer.hole_name, StratigraphicLayer.depth_top).all()


@router.get("/holes", response_model=List[str])
def get_all_hole_names(db: Session = Depends(get_db)):
    """获取所有钻孔名称列表"""
    result = db.query(StratigraphicLayer.hole_name).distinct().all()
    return [r[0] for r in result]


@router.get("/{layer_id}", response_model=StratigraphicLayerResponse)
def get_layer(layer_id: int, db: Session = Depends(get_db)):
    """获取单条地层分层数据"""
    layer = db.query(StratigraphicLayer).filter(StratigraphicLayer.id == layer_id).first()
    if not layer:
        raise HTTPException(status_code=404, detail="地层分层数据不存在")
    return layer


@router.post("/create", response_model=StratigraphicLayerResponse)
def create_layer(layer: StratigraphicLayerCreate, db: Session = Depends(get_db)):
    """创建地层分层数据"""
    db_layer = StratigraphicLayer(**layer.model_dump())
    db.add(db_layer)
    db.commit()
    db.refresh(db_layer)
    return db_layer


@router.put("/{layer_id}", response_model=StratigraphicLayerResponse)
def update_layer(layer_id: int, layer: StratigraphicLayerUpdate, db: Session = Depends(get_db)):
    """更新地层分层数据"""
    db_layer = db.query(StratigraphicLayer).filter(StratigraphicLayer.id == layer_id).first()
    if not db_layer:
        raise HTTPException(status_code=404, detail="地层分层数据不存在")
    
    update_data = layer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_layer, key, value)
    
    db.commit()
    db.refresh(db_layer)
    return db_layer


@router.delete("/{layer_id}", response_model=MessageResponse)
def delete_layer(layer_id: int, db: Session = Depends(get_db)):
    """删除地层分层数据"""
    db_layer = db.query(StratigraphicLayer).filter(StratigraphicLayer.id == layer_id).first()
    if not db_layer:
        raise HTTPException(status_code=404, detail="地层分层数据不存在")
    
    db.delete(db_layer)
    db.commit()
    return MessageResponse(success=True, message="删除成功")


@router.delete("/hole/{hole_name}", response_model=MessageResponse)
def delete_by_hole(hole_name: str, db: Session = Depends(get_db)):
    """删除指定钻孔的所有地层分层数据"""
    count = db.query(StratigraphicLayer).filter(StratigraphicLayer.hole_name == hole_name).delete()
    db.commit()
    return MessageResponse(success=True, message=f"已删除 {count} 条数据")


@router.post("/import-csv", response_model=dict)
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """从CSV文件导入地层分层数据
    
    CSV格式：钻孔名称,顶部深度,底部深度,地层类型
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="请上传CSV文件")
    
    content = await file.read()
    try:
        # 尝试多种编码
        try:
            text = content.decode('utf-8-sig')
        except:
            text = content.decode('gbk')
        
        reader = csv.DictReader(io.StringIO(text))
        
        success_count = 0
        error_count = 0
        errors = []
        
        for i, row in enumerate(reader, start=2):
            try:
                # 解析数据
                hole_name = row.get('钻孔名称', '').strip()
                depth_top = float(row.get('顶部深度', 0))
                depth_bottom = float(row.get('底部深度', 0))
                layer_type = row.get('地层类型', '').strip()
                
                if not hole_name or not layer_type:
                    raise ValueError("钻孔名称和地层类型不能为空")
                
                # 创建记录
                db_layer = StratigraphicLayer(
                    hole_name=hole_name,
                    depth_top=depth_top,
                    depth_bottom=depth_bottom,
                    layer_type=layer_type
                )
                db.add(db_layer)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"第{i}行: {str(e)}")
        
        db.commit()
        
        return {
            "success": True,
            "message": f"导入完成：成功 {success_count} 条，失败 {error_count} 条",
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[:10] if errors else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/batch-create", response_model=dict)
def batch_create_layers(layers: List[StratigraphicLayerCreate], db: Session = Depends(get_db)):
    """批量创建地层分层数据"""
    try:
        db_layers = [StratigraphicLayer(**layer.model_dump()) for layer in layers]
        db.add_all(db_layers)
        db.commit()
        return {
            "success": True,
            "message": f"成功创建 {len(db_layers)} 条数据",
            "count": len(db_layers)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量创建失败: {str(e)}")


@router.delete("/clear-all", response_model=MessageResponse)
def clear_all(db: Session = Depends(get_db)):
    """清空所有地层分层数据"""
    count = db.query(StratigraphicLayer).delete()
    db.commit()
    return MessageResponse(success=True, message=f"已清空 {count} 条数据")
