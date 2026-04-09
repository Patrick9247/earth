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
    except Exception as e:
        layers = SAMPLE_LAYERS
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'ID', '名称', '类型', '顶部深度(m)', '底部深度(m)',
        '孔隙度', '渗透率(mD)', '热导率(W/m·K)', '颜色'
    ])
    
    for layer in layers:
        if isinstance(layer, dict):
            writer.writerow([
                layer.get('id'), layer.get('name'), layer.get('layer_type'),
                layer.get('depth_top'), layer.get('depth_bottom'),
                layer.get('porosity'), layer.get('permeability'),
                layer.get('thermal_conductivity'), layer.get('color')
            ])
        else:
            writer.writerow([
                layer.id, layer.name, layer.layer_type,
                layer.depth_top, layer.depth_bottom,
                layer.porosity, layer.permeability,
                layer.thermal_conductivity, layer.color
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
        'ID', '钻孔编号', '钻孔名称', 'X坐标', 'Y坐标', '地面高程(m)',
        '总深度(m)', '终孔深度(m)', '孔径(mm)', '施工单位', 
        '开孔日期', '终孔日期', '状态', '备注'
    ])
    
    for dh in drill_holes:
        if isinstance(dh, dict):
            writer.writerow([
                dh.get('id'), dh.get('hole_id'), dh.get('hole_name'),
                dh.get('location_x'), dh.get('location_y'), dh.get('elevation'),
                dh.get('total_depth'), dh.get('final_depth'), dh.get('diameter'),
                dh.get('drill_company'), dh.get('drill_start_date'), dh.get('drill_end_date'),
                dh.get('status'), dh.get('description')
            ])
        else:
            writer.writerow([
                dh.id, dh.hole_id, dh.hole_name,
                dh.location_x, dh.location_y, dh.elevation,
                dh.total_depth, dh.final_depth, dh.diameter,
                dh.drill_company, dh.drill_start_date, dh.drill_end_date,
                dh.status, dh.description
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
    except Exception as e:
        results = SAMPLE_RESULTS
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'ID', '名称', '模型类型', '储层体积(m³)', '平均温度(°C)',
        '最高温度(°C)', '热含量(J)', '可采热量(J)', '发电潜力(MW)',
        '开采年限(年)'
    ])
    
    for r in results:
        if isinstance(r, dict):
            writer.writerow([
                r.get('id'), r.get('name'), r.get('model_type'), r.get('volume'),
                r.get('temperature_avg'), r.get('temperature_max'),
                r.get('heat_content'), r.get('extractable_heat'),
                r.get('power_potential'), r.get('lifetime_years')
            ])
        else:
            writer.writerow([
                r.id, r.name, r.model_type, r.volume,
                r.temperature_avg, r.temperature_max,
                r.heat_content, r.extractable_heat,
                r.power_potential, r.lifetime_years
            ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )


@router.get("/grids/csv")
async def export_grids_csv(result_id: int = None):
    """导出网格数据为 CSV"""
    try:
        from ..database import SessionLocal
        from ..models import GeothermalResource
        import json
        
        db = SessionLocal()
        
        if result_id:
            result = db.query(GeothermalResource).filter(GeothermalResource.id == result_id).first()
            if result and result.original_grids:
                grids = json.loads(result.original_grids)
            else:
                grids = []
        else:
            grids = []
        
        db.close()
    except Exception as e:
        grids = []
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        '编号', 'X坐标(m)', 'Y坐标(m)', 'Z坐标(m)',
        '温度(°C)', '压力(MPa)', '孔隙度', '渗透率(mD)',
        '体积(m³)', '密度(kg/m³)', '相态', '热能(J)'
    ])
    
    for i, g in enumerate(grids, 1):
        writer.writerow([
            i,
            g.get('x', 0), g.get('y', 0), g.get('z', 0),
            g.get('temperature', 0), g.get('pressure', 0),
            g.get('porosity', 0), g.get('permeability', 0),
            g.get('volume', 0), g.get('density', 0),
            g.get('phase', 'liquid'), g.get('heat', 0)
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=grids_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )


@router.get("/all/json")
async def export_all_json(result_id: int = None):
    """导出所有数据为 JSON"""
    try:
        from ..database import SessionLocal
        from ..models import GeologicalLayer, DrillHole, GeothermalResource
        import json
        
        db = SessionLocal()
        layers = db.query(GeologicalLayer).all()
        drill_holes = db.query(DrillHole).all()
        results = db.query(GeothermalResource).all()
        
        # 获取指定结果的网格数据
        grids_data = []
        if result_id:
            result = db.query(GeothermalResource).filter(GeothermalResource.id == result_id).first()
            if result and result.original_grids:
                grids_data = json.loads(result.original_grids)
        
        db.close()
    except Exception as e:
        layers = SAMPLE_LAYERS
        drill_holes = SAMPLE_DRILL_HOLES
        results = SAMPLE_RESULTS
        grids_data = []
    
    # 处理地质层数据
    if layers and hasattr(layers[0], 'id'):
        layers_data = [
            {
                'id': l.id, 'name': l.name, 'type': l.layer_type,
                'depth_top': l.depth_top, 'depth_bottom': l.depth_bottom,
                'porosity': l.porosity, 'permeability': l.permeability,
                'thermal_conductivity': l.thermal_conductivity, 'color': l.color
            } for l in layers
        ]
    else:
        layers_data = layers
    
    # 处理钻孔数据
    if drill_holes and hasattr(drill_holes[0], 'id'):
        drill_holes_data = [
            {
                'id': d.id,
                'hole_id': getattr(d, 'hole_id', None),
                'hole_name': getattr(d, 'hole_name', None),
                'location': {
                    'x': getattr(d, 'location_x', None),
                    'y': getattr(d, 'location_y', None),
                    'elevation': getattr(d, 'elevation', 0)
                },
                'total_depth': getattr(d, 'total_depth', None),
                'final_depth': getattr(d, 'final_depth', None),
                'diameter': getattr(d, 'diameter', None),
                'drill_company': getattr(d, 'drill_company', None),
                'status': getattr(d, 'status', None),
                'description': getattr(d, 'description', None)
            } for d in drill_holes
        ]
    else:
        drill_holes_data = drill_holes
    
    # 处理计算结果
    if results and hasattr(results[0], 'id'):
        results_data = []
        for r in results:
            result_dict = {
                'id': r.id, 'name': r.name, 'model_type': r.model_type,
                'volume': r.volume, 'temperature_avg': r.temperature_avg,
                'temperature_max': r.temperature_max,
                'heat_content': r.heat_content, 'extractable_heat': r.extractable_heat,
                'power_potential': r.power_potential, 'lifetime_years': r.lifetime_years
            }
            # 如果是指定的结果，添加网格数据
            if result_id and r.id == result_id and grids_data:
                result_dict['grids'] = grids_data
            results_data.append(result_dict)
    else:
        results_data = results
    
    data = {
        'export_time': datetime.now().isoformat(),
        'layers': layers_data,
        'drill_holes': drill_holes_data,
        'results': results_data
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
    except Exception as e:
        layers = SAMPLE_LAYERS
        drill_holes = SAMPLE_DRILL_HOLES
        results = SAMPLE_RESULTS
    
    # 计算统计信息
    layer_count = len(layers)
    drill_hole_count = len(drill_holes)
    result_count = len(results)
    
    total_power = 0
    total_heat = 0
    
    for r in results:
        if isinstance(r, dict):
            total_power += r.get('power_potential', 0) or 0
            total_heat += r.get('heat_content', 0) or 0
        else:
            total_power += getattr(r, 'power_potential', 0) or 0
            total_heat += getattr(r, 'heat_content', 0) or 0
    
    total_heat_ej = total_heat / 1e18
    
    max_depth = 0
    total_depth = 0
    
    if drill_hole_count > 0:
        depths = []
        for d in drill_holes:
            if isinstance(d, dict):
                depths.append(d.get('total_depth', 0) or d.get('depth', 0) or 0)
            else:
                depth = getattr(d, 'total_depth', None) or getattr(d, 'final_depth', None) or 0
                depths.append(depth)
        
        if depths:
            max_depth = max(depths)
            total_depth = sum(depths)
    
    report = {
        'title': '地热流体资源建模系统报告',
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_layers': layer_count,
            'total_drill_holes': drill_hole_count,
            'total_calculations': result_count,
            'total_power_potential_mw': round(total_power, 2),
            'total_heat_content_ej': round(total_heat_ej, 2)
        },
        'statistics': {
            'max_depth': max_depth,
            'total_drilled_depth': round(total_depth, 2),
            'avg_drilled_depth': round(total_depth / drill_hole_count, 2) if drill_hole_count > 0 else 0
        }
    }
    
    return report
