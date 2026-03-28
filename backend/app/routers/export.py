"""
数据导出 API
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import io
import csv
import json
from datetime import datetime

router = APIRouter(prefix="/api/export", tags=["数据导出"])

# 模拟数据
SAMPLE_LAYERS = [
    {'id': 1, 'name': '第四系覆盖层', 'layer_type': '沉积层', 'depth_top': 0, 'depth_bottom': 50, 'porosity': 0.25, 'permeability': 100, 'thermal_conductivity': 1.8, 'color': '#90EE90'},
    {'id': 2, 'name': '砂岩储层', 'layer_type': '储层', 'depth_top': 50, 'depth_bottom': 500, 'porosity': 0.18, 'permeability': 50, 'thermal_conductivity': 2.5, 'color': '#FFD700'},
    {'id': 3, 'name': '花岗岩基底', 'layer_type': '基岩', 'depth_top': 500, 'depth_bottom': 2000, 'porosity': 0.05, 'permeability': 1, 'thermal_conductivity': 3.2, 'color': '#CD5C5C'}
]

SAMPLE_DRILL_HOLES = [
    {'id': 1, 'name': 'ZK-001', 'location_x': 100, 'location_y': 200, 'location_z': 50, 'depth': 800, 'temperature': 120, 'gradient': 6.5, 'description': '主探孔'},
    {'id': 2, 'name': 'ZK-002', 'location_x': 300, 'location_y': 400, 'location_z': 45, 'depth': 1200, 'temperature': 160, 'gradient': 7.2, 'description': '深部探孔'},
    {'id': 3, 'name': 'ZK-003', 'location_x': 500, 'location_y': 150, 'location_z': 55, 'depth': 600, 'temperature': 95, 'gradient': 5.8, 'description': '边缘探孔'}
]

SAMPLE_RESULTS = [
    {'id': 1, 'name': '地热田A计算', 'model_type': 'geothermal', 'volume': 1e8, 'temperature_avg': 150, 'temperature_max': 180, 'heat_content': 1.5e18, 'extractable_heat': 3.75e17, 'power_potential': 12.5, 'lifetime_years': 30},
    {'id': 2, 'name': '地热田B计算', 'model_type': 'geothermal', 'volume': 5e7, 'temperature_avg': 180, 'temperature_max': 220, 'heat_content': 2.1e18, 'extractable_heat': 5.2e17, 'power_potential': 18.3, 'lifetime_years': 25}
]


@router.get("/layers/csv")
async def export_layers_csv():
    """导出地质层数据为 CSV"""
    try:
        from ..database import SessionLocal
        from ..models import GeologicalLayer
        db = SessionLocal()
        layers = db.query(GeologicalLayer).all()
        db.close()
    except:
        layers = SAMPLE_LAYERS
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'ID', '名称', '类型', '顶部深度(m)', '底部深度(m)',
        '孔隙度', '渗透率(mD)', '热导率(W/m·K)', '颜色'
    ])
    
    for layer in layers:
        writer.writerow([
            layer.get('id'), layer.get('name'), layer.get('layer_type'),
            layer.get('depth_top'), layer.get('depth_bottom'),
            layer.get('porosity'), layer.get('permeability'),
            layer.get('thermal_conductivity'), layer.get('color')
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=layers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )


@router.get("/drill-holes/csv")
async def export_drill_holes_csv():
    """导出钻孔数据为 CSV"""
    try:
        from ..database import SessionLocal
        from ..models import DrillHole
        db = SessionLocal()
        drill_holes = db.query(DrillHole).all()
        db.close()
    except:
        drill_holes = SAMPLE_DRILL_HOLES
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'ID', '编号', 'X坐标', 'Y坐标', '地面高程(m)',
        '深度(m)', '温度(°C)', '地温梯度(°C/100m)', '描述'
    ])
    
    for dh in drill_holes:
        writer.writerow([
            dh.get('id'), dh.get('name'), dh.get('location_x'), 
            dh.get('location_y'), dh.get('location_z'),
            dh.get('depth'), dh.get('temperature'), dh.get('gradient'), 
            dh.get('description')
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=drill_holes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )


@router.get("/results/csv")
async def export_results_csv():
    """导出计算结果为 CSV"""
    try:
        from ..database import SessionLocal
        from ..models import GeothermalResource
        db = SessionLocal()
        results = db.query(GeothermalResource).all()
        db.close()
    except:
        results = SAMPLE_RESULTS
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'ID', '名称', '模型类型', '储层体积(m³)', '平均温度(°C)',
        '最高温度(°C)', '热含量(J)', '可采热量(J)', '发电潜力(MW)',
        '开采年限(年)'
    ])
    
    for r in results:
        writer.writerow([
            r.get('id'), r.get('name'), r.get('model_type'), r.get('volume'),
            r.get('temperature_avg'), r.get('temperature_max'),
            r.get('heat_content'), r.get('extractable_heat'),
            r.get('power_potential'), r.get('lifetime_years')
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )


@router.get("/all/json")
async def export_all_json():
    """导出所有数据为 JSON"""
    try:
        from ..database import SessionLocal
        from ..models import GeologicalLayer, DrillHole, GeothermalResource
        db = SessionLocal()
        layers = db.query(GeologicalLayer).all()
        drill_holes = db.query(DrillHole).all()
        results = db.query(GeothermalResource).all()
        db.close()
    except:
        layers = SAMPLE_LAYERS
        drill_holes = SAMPLE_DRILL_HOLES
        results = SAMPLE_RESULTS
    
    data = {
        'export_time': datetime.now().isoformat(),
        'layers': layers if isinstance(layers, list) and all(isinstance(l, dict) for l in layers) else [
            {
                'id': l.id, 'name': l.name, 'type': l.layer_type,
                'depth_top': l.depth_top, 'depth_bottom': l.depth_bottom,
                'porosity': l.porosity, 'permeability': l.permeability,
                'thermal_conductivity': l.thermal_conductivity, 'color': l.color
            } for l in layers
        ],
        'drill_holes': drill_holes if isinstance(drill_holes, list) and all(isinstance(d, dict) for d in drill_holes) else [
            {
                'id': d.id, 'name': d.name,
                'location': {'x': d.location_x, 'y': d.location_y, 'z': d.location_z},
                'depth': d.depth, 'temperature': d.temperature,
                'gradient': d.gradient, 'description': d.description
            } for d in drill_holes
        ],
        'results': results if isinstance(results, list) and all(isinstance(r, dict) for r in results) else [
            {
                'id': r.id, 'name': r.name, 'model_type': r.model_type,
                'volume': r.volume, 'temperature_avg': r.temperature_avg,
                'heat_content': r.heat_content, 'extractable_heat': r.extractable_heat,
                'power_potential': r.power_potential, 'lifetime_years': r.lifetime_years
            } for r in results
        ]
    }
    
    return StreamingResponse(
        io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2, default=str).encode('utf-8')),
        media_type='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=geothermal_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        }
    )


@router.get("/report")
async def generate_report():
    """生成汇总报告"""
    try:
        from ..database import SessionLocal
        from ..models import GeologicalLayer, DrillHole, GeothermalResource
        db = SessionLocal()
        layers = db.query(GeologicalLayer).all()
        drill_holes = db.query(DrillHole).all()
        results = db.query(GeothermalResource).all()
        db.close()
    except:
        layers = SAMPLE_LAYERS
        drill_holes = SAMPLE_DRILL_HOLES
        results = SAMPLE_RESULTS
    
    # 计算统计信息
    layer_count = len(layers)
    drill_hole_count = len(drill_holes)
    result_count = len(results)
    
    total_power = sum(r.get('power_potential', 0) if isinstance(r, dict) else (r.power_potential or 0) for r in results)
    total_heat = sum(r.get('heat_content', 0) if isinstance(r, dict) else (r.heat_content or 0) for r in results) / 1e18
    
    avg_temp = 0
    avg_gradient = 0
    max_depth = 0
    total_depth = 0
    
    if drill_hole_count > 0:
        temps = [d.get('temperature', 0) if isinstance(d, dict) else (d.temperature or 0) for d in drill_holes]
        gradients = [d.get('gradient', 0) if isinstance(d, dict) else (d.gradient or 0) for d in drill_holes]
        depths = [d.get('depth', 0) if isinstance(d, dict) else (d.depth or 0) for d in drill_holes]
        
        avg_temp = sum(temps) / len(temps)
        avg_gradient = sum(gradients) / len(gradients)
        max_depth = max(depths)
        total_depth = sum(depths)
    
    report = {
        'title': '地热流体资源建模系统报告',
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_layers': layer_count,
            'total_drill_holes': drill_hole_count,
            'total_calculations': result_count,
            'total_power_potential_mw': total_power,
            'total_heat_content_ej': total_heat
        },
        'statistics': {
            'avg_temperature': round(avg_temp, 2),
            'avg_gradient': round(avg_gradient, 2),
            'max_depth': max_depth,
            'total_drilled_depth': total_depth
        }
    }
    
    return report
