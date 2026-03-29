"""
CSV导入API - 支持多种数据类型导入
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import csv
import io
import logging
from io import StringIO

from ..database import get_db
from ..models import (
    DrillHole, DrillLayer, DrillTemperatureCurve,
    DrillPressureData, DrillPorosityData, CsvImportRecord
)
from ..schemas import CsvImportResult, CsvPreviewResponse

router = APIRouter(prefix="/api/import", tags=["CSV数据导入"])
logger = logging.getLogger(__name__)


# ==================== CSV模板下载 ====================

@router.get("/template/{import_type}")
async def download_template(import_type: str):
    """
    下载CSV模板文件
    
    import_type: 
    - drill_info: 钻孔空间信息
    - layers: 热储层分层数据
    - temperature: 钻孔测温曲线
    - pressure: 孔口压力数据
    - porosity: 岩石孔隙度数据
    """
    templates = {
        "drill_info": {
            "filename": "钻孔空间信息模板.csv",
            "headers": [
                "钻孔编号", "钻孔名称", "X坐标(m)", "Y坐标(m)", "地面高程(m)",
                "钻孔总深度(m)", "终孔深度(m)", "孔径(mm)", "施工单位",
                "开孔日期", "终孔日期", "钻孔状态", "备注说明"
            ],
            "example_row": [
                "ZK-001", "地热勘探孔1号", "1000.5", "2000.3", "45.2",
                "800", "800", "150", "XX地质勘探公司",
                "2023-01-15", "2023-03-20", "完成", "主探孔"
            ]
        },
        "layers": {
            "filename": "热储层分层数据模板.csv",
            "headers": [
                "钻孔编号", "层序号", "地层名称", "地层类型", "层顶深度(m)", "层底深度(m)",
                "层厚度(m)", "岩性描述", "岩石类型", "岩石颜色", "孔隙度",
                "渗透率(mD)", "岩石密度(g/cm³)", "热导率(W/m·K)",
                "含水层类型", "富水性", "备注说明"
            ],
            "example_row": [
                "ZK-001", "1", "第四系覆盖层", "沉积层", "0", "50",
                "50", "砂质粘土夹砾石", "沉积岩", "黄褐色", "0.25",
                "100", "1.8", "1.8", "潜水含水层", "弱", "表层覆盖"
            ]
        },
        "temperature": {
            "filename": "钻孔测温曲线模板.csv",
            "headers": [
                "钻孔编号", "测点序号", "测量日期", "测量类型", "测量深度(m)",
                "测量温度(°C)", "校正后温度(°C)", "校正方法", "地温梯度(°C/100m)",
                "测量仪器", "测量精度(°C)", "备注"
            ],
            "example_row": [
                "ZK-001", "1", "2023-04-01", "稳态测温", "100",
                "45.5", "45.8", "井温校正", "6.5",
                "XX温度计", "0.1", "正常"
            ]
        },
        "pressure": {
            "filename": "孔口压力数据模板.csv",
            "headers": [
                "钻孔编号", "测点序号", "测量日期", "测量时间", "井口压力(MPa)",
                "储层压力(MPa)", "流动压力(MPa)", "关井压力(MPa)", "压力梯度(MPa/100m)",
                "测量深度(m)", "流量(m³/h)", "动水位(m)", "测量仪器", "备注"
            ],
            "example_row": [
                "ZK-001", "1", "2023-04-01", "10:30:00", "0.35",
                "8.5", "7.2", "8.8", "0.98",
                "800", "120", "25", "XX压力计", "正常生产"
            ]
        },
        "porosity": {
            "filename": "岩石孔隙度数据模板.csv",
            "headers": [
                "钻孔编号", "样品编号", "采样日期", "样品顶深(m)", "样品底深(m)",
                "取样深度(m)", "岩性描述", "岩石类型", "总孔隙度(%)", "有效孔隙度(%)",
                "渗透率(mD)", "水平渗透率(mD)", "垂直渗透率(mD)", "体密度(g/cm³)",
                "颗粒密度(g/cm³)", "含水饱和度(%)", "测试方法", "测试单位", "备注"
            ],
            "example_row": [
                "ZK-001", "S-001", "2023-03-15", "100", "100.5",
                "100.2", "中砂岩", "砂岩", "22.5", "18.3",
                "85", "90", "75", "2.35",
                "2.65", "35", "气体膨胀法", "XX实验室", "储层段"
            ]
        }
    }
    
    if import_type not in templates:
        raise HTTPException(status_code=400, detail=f"不支持的导入类型: {import_type}")
    
    template = templates[import_type]
    
    # 创建CSV内容
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(template["headers"])
    writer.writerow(template["example_row"])
    
    output.seek(0)
    
    # 使用URL编码处理中文文件名
    from urllib.parse import quote
    encoded_filename = quote(template['filename'])
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


# ==================== CSV预览 ====================

@router.post("/preview", response_model=CsvPreviewResponse)
async def preview_csv(file: UploadFile = File(...)):
    """
    预览CSV文件内容
    """
    try:
        content = await file.read()
        
        # 尝试不同编码
        text_content = None
        for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']:
            try:
                text_content = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if text_content is None:
            return CsvPreviewResponse(
                success=False,
                columns=[],
                rows=[],
                total_rows=0,
                message="无法解析文件编码，请使用UTF-8或GBK编码"
            )
        
        reader = csv.DictReader(StringIO(text_content))
        columns = reader.fieldnames or []
        rows = list(reader)
        
        # 限制预览行数
        preview_rows = rows[:20]
        
        return CsvPreviewResponse(
            success=True,
            columns=list(columns),
            rows=preview_rows,
            total_rows=len(rows),
            message=f"成功读取文件，共{len(rows)}行数据"
        )
        
    except Exception as e:
        logger.error(f"预览CSV失败: {e}")
        return CsvPreviewResponse(
            success=False,
            columns=[],
            rows=[],
            total_rows=0,
            message=f"预览失败: {str(e)}"
        )


# ==================== 钻孔空间信息导入 ====================

@router.post("/drill-info", response_model=CsvImportResult)
async def import_drill_info(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    导入钻孔空间信息CSV
    
    必需字段：钻孔编号, X坐标(m), Y坐标(m)
    """
    try:
        content = await file.read()
        text_content = decode_content(content)
        
        if not text_content:
            return CsvImportResult(success=False, message="无法解析文件编码")
        
        reader = csv.DictReader(StringIO(text_content))
        
        total_rows = 0
        success_rows = 0
        errors = []
        drill_holes_to_create = []
        
        for row_num, row in enumerate(reader, start=2):  # 从第2行开始（第1行是表头）
            total_rows += 1
            
            try:
                # 必需字段验证
                hole_id = get_field_value(row, ["钻孔编号", "hole_id", "钻孔编号", "孔号"])
                if not hole_id:
                    errors.append({"row": row_num, "error": "缺少钻孔编号"})
                    continue
                
                location_x = parse_float(get_field_value(row, ["X坐标(m)", "X坐标", "location_x", "x"]))
                location_y = parse_float(get_field_value(row, ["Y坐标(m)", "Y坐标", "location_y", "y"]))
                
                if location_x is None or location_y is None:
                    errors.append({"row": row_num, "error": "缺少坐标信息"})
                    continue
                
                # 检查是否已存在
                existing = db.query(DrillHole).filter(DrillHole.hole_id == hole_id).first()
                if existing:
                    # 更新现有记录
                    existing.hole_name = get_field_value(row, ["钻孔名称", "hole_name", "名称"]) or existing.hole_name
                    existing.location_x = location_x
                    existing.location_y = location_y
                    existing.elevation = parse_float(get_field_value(row, ["地面高程(m)", "高程", "elevation"])) or existing.elevation
                    existing.total_depth = parse_float(get_field_value(row, ["钻孔总深度(m)", "总深度", "total_depth", "深度"])) or existing.total_depth
                    existing.final_depth = parse_float(get_field_value(row, ["终孔深度(m)", "final_depth"])) or existing.final_depth
                    existing.diameter = parse_float(get_field_value(row, ["孔径(mm)", "孔径", "diameter"])) or existing.diameter
                    existing.drill_company = get_field_value(row, ["施工单位", "drill_company"]) or existing.drill_company
                    existing.drill_start_date = get_field_value(row, ["开孔日期", "drill_start_date"]) or existing.drill_start_date
                    existing.drill_end_date = get_field_value(row, ["终孔日期", "drill_end_date"]) or existing.drill_end_date
                    existing.status = get_field_value(row, ["钻孔状态", "status"]) or existing.status
                    existing.description = get_field_value(row, ["备注说明", "备注", "description"]) or existing.description
                    success_rows += 1
                else:
                    # 创建新记录
                    drill_hole = DrillHole(
                        hole_id=hole_id,
                        hole_name=get_field_value(row, ["钻孔名称", "hole_name", "名称"]),
                        location_x=location_x,
                        location_y=location_y,
                        elevation=parse_float(get_field_value(row, ["地面高程(m)", "高程", "elevation"])) or 0,
                        total_depth=parse_float(get_field_value(row, ["钻孔总深度(m)", "总深度", "total_depth", "深度"])),
                        final_depth=parse_float(get_field_value(row, ["终孔深度(m)", "final_depth"])),
                        diameter=parse_float(get_field_value(row, ["孔径(mm)", "孔径", "diameter"])),
                        drill_company=get_field_value(row, ["施工单位", "drill_company"]),
                        drill_start_date=get_field_value(row, ["开孔日期", "drill_start_date"]),
                        drill_end_date=get_field_value(row, ["终孔日期", "drill_end_date"]),
                        status=get_field_value(row, ["钻孔状态", "status"]) or "完成",
                        description=get_field_value(row, ["备注说明", "备注", "description"])
                    )
                    drill_holes_to_create.append(drill_hole)
                    success_rows += 1
                    
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})
        
        # 批量创建新记录
        if drill_holes_to_create:
            db.add_all(drill_holes_to_create)
        
        db.commit()
        
        # 记录导入日志
        record = CsvImportRecord(
            file_name=file.filename,
            import_type="drill_info",
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=total_rows - success_rows,
            error_details=errors[:100] if errors else None,
            status="完成"
        )
        db.add(record)
        db.commit()
        
        return CsvImportResult(
            success=True,
            message=f"导入完成：成功{success_rows}行，失败{total_rows - success_rows}行",
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=total_rows - success_rows,
            errors=errors[:20] if errors else None,
            record_id=record.id
        )
        
    except Exception as e:
        logger.error(f"导入钻孔信息失败: {e}")
        db.rollback()
        return CsvImportResult(success=False, message=f"导入失败: {str(e)}")


# ==================== 热储层分层数据导入 ====================

@router.post("/layers", response_model=CsvImportResult)
async def import_layers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    导入热储层分层数据CSV
    
    必需字段：钻孔编号, 层顶深度(m), 层底深度(m)
    """
    try:
        content = await file.read()
        text_content = decode_content(content)
        
        if not text_content:
            return CsvImportResult(success=False, message="无法解析文件编码")
        
        reader = csv.DictReader(StringIO(text_content))
        
        total_rows = 0
        success_rows = 0
        errors = []
        layers_to_create = []
        
        for row_num, row in enumerate(reader, start=2):
            total_rows += 1
            
            try:
                hole_id = get_field_value(row, ["钻孔编号", "hole_id"])
                if not hole_id:
                    errors.append({"row": row_num, "error": "缺少钻孔编号"})
                    continue
                
                # 查找钻孔
                drill_hole = db.query(DrillHole).filter(DrillHole.hole_id == hole_id).first()
                if not drill_hole:
                    errors.append({"row": row_num, "error": f"钻孔不存在: {hole_id}"})
                    continue
                
                depth_top = parse_float(get_field_value(row, ["层顶深度(m)", "层顶深度", "depth_top"]))
                depth_bottom = parse_float(get_field_value(row, ["层底深度(m)", "层底深度", "depth_bottom"]))
                
                if depth_top is None or depth_bottom is None:
                    errors.append({"row": row_num, "error": "缺少深度信息"})
                    continue
                
                layer = DrillLayer(
                    drill_hole_id=drill_hole.id,
                    layer_no=parse_int(get_field_value(row, ["层序号", "layer_no"])),
                    layer_name=get_field_value(row, ["地层名称", "layer_name"]),
                    layer_type=get_field_value(row, ["地层类型", "layer_type"]),
                    depth_top=depth_top,
                    depth_bottom=depth_bottom,
                    thickness=parse_float(get_field_value(row, ["层厚度(m)", "厚度", "thickness"])),
                    lithology=get_field_value(row, ["岩性描述", "岩性", "lithology"]),
                    rock_type=get_field_value(row, ["岩石类型", "rock_type"]),
                    color=get_field_value(row, ["岩石颜色", "颜色", "color"]),
                    porosity=parse_float(get_field_value(row, ["孔隙度", "porosity"])),
                    permeability=parse_float(get_field_value(row, ["渗透率(mD)", "渗透率", "permeability"])),
                    density=parse_float(get_field_value(row, ["岩石密度(g/cm³)", "密度", "density"])),
                    thermal_conductivity=parse_float(get_field_value(row, ["热导率(W/m·K)", "热导率", "thermal_conductivity"])),
                    aquifer_type=get_field_value(row, ["含水层类型", "aquifer_type"]),
                    water_bearing=get_field_value(row, ["富水性", "water_bearing"]),
                    description=get_field_value(row, ["备注说明", "备注", "description"])
                )
                layers_to_create.append(layer)
                success_rows += 1
                
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})
        
        if layers_to_create:
            db.add_all(layers_to_create)
        
        db.commit()
        
        record = CsvImportRecord(
            file_name=file.filename,
            import_type="layers",
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=total_rows - success_rows,
            error_details=errors[:100] if errors else None,
            status="完成"
        )
        db.add(record)
        db.commit()
        
        return CsvImportResult(
            success=True,
            message=f"导入完成：成功{success_rows}行，失败{total_rows - success_rows}行",
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=total_rows - success_rows,
            errors=errors[:20] if errors else None,
            record_id=record.id
        )
        
    except Exception as e:
        logger.error(f"导入分层数据失败: {e}")
        db.rollback()
        return CsvImportResult(success=False, message=f"导入失败: {str(e)}")


# ==================== 测温曲线导入 ====================

@router.post("/temperature", response_model=CsvImportResult)
async def import_temperature(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    导入钻孔测温曲线数据CSV
    
    必需字段：钻孔编号, 测量深度(m), 测量温度(°C)
    """
    try:
        content = await file.read()
        text_content = decode_content(content)
        
        if not text_content:
            return CsvImportResult(success=False, message="无法解析文件编码")
        
        reader = csv.DictReader(StringIO(text_content))
        
        total_rows = 0
        success_rows = 0
        errors = []
        curves_to_create = []
        
        for row_num, row in enumerate(reader, start=2):
            total_rows += 1
            
            try:
                hole_id = get_field_value(row, ["钻孔编号", "hole_id"])
                if not hole_id:
                    errors.append({"row": row_num, "error": "缺少钻孔编号"})
                    continue
                
                drill_hole = db.query(DrillHole).filter(DrillHole.hole_id == hole_id).first()
                if not drill_hole:
                    errors.append({"row": row_num, "error": f"钻孔不存在: {hole_id}"})
                    continue
                
                depth = parse_float(get_field_value(row, ["测量深度(m)", "深度", "depth"]))
                temperature = parse_float(get_field_value(row, ["测量温度(°C)", "温度", "temperature"]))
                
                if depth is None or temperature is None:
                    errors.append({"row": row_num, "error": "缺少深度或温度数据"})
                    continue
                
                curve = DrillTemperatureCurve(
                    drill_hole_id=drill_hole.id,
                    measure_no=parse_int(get_field_value(row, ["测点序号", "measure_no"])),
                    measure_date=get_field_value(row, ["测量日期", "measure_date"]),
                    measure_type=get_field_value(row, ["测量类型", "measure_type"]) or "稳态测温",
                    depth=depth,
                    temperature=temperature,
                    corrected_temp=parse_float(get_field_value(row, ["校正后温度(°C)", "校正温度", "corrected_temp"])),
                    correction_method=get_field_value(row, ["校正方法", "correction_method"]),
                    gradient=parse_float(get_field_value(row, ["地温梯度(°C/100m)", "地温梯度", "gradient"])),
                    instrument=get_field_value(row, ["测量仪器", "instrument"]),
                    accuracy=parse_float(get_field_value(row, ["测量精度(°C)", "精度", "accuracy"])),
                    description=get_field_value(row, ["备注", "description"])
                )
                curves_to_create.append(curve)
                success_rows += 1
                
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})
        
        if curves_to_create:
            db.add_all(curves_to_create)
        
        db.commit()
        
        record = CsvImportRecord(
            file_name=file.filename,
            import_type="temperature",
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=total_rows - success_rows,
            error_details=errors[:100] if errors else None,
            status="完成"
        )
        db.add(record)
        db.commit()
        
        return CsvImportResult(
            success=True,
            message=f"导入完成：成功{success_rows}行，失败{total_rows - success_rows}行",
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=total_rows - success_rows,
            errors=errors[:20] if errors else None,
            record_id=record.id
        )
        
    except Exception as e:
        logger.error(f"导入测温数据失败: {e}")
        db.rollback()
        return CsvImportResult(success=False, message=f"导入失败: {str(e)}")


# ==================== 压力数据导入 ====================

@router.post("/pressure", response_model=CsvImportResult)
async def import_pressure(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    导入孔口压力数据CSV
    
    必需字段：钻孔编号
    """
    try:
        content = await file.read()
        text_content = decode_content(content)
        
        if not text_content:
            return CsvImportResult(success=False, message="无法解析文件编码")
        
        reader = csv.DictReader(StringIO(text_content))
        
        total_rows = 0
        success_rows = 0
        errors = []
        pressure_to_create = []
        
        for row_num, row in enumerate(reader, start=2):
            total_rows += 1
            
            try:
                hole_id = get_field_value(row, ["钻孔编号", "hole_id"])
                if not hole_id:
                    errors.append({"row": row_num, "error": "缺少钻孔编号"})
                    continue
                
                drill_hole = db.query(DrillHole).filter(DrillHole.hole_id == hole_id).first()
                if not drill_hole:
                    errors.append({"row": row_num, "error": f"钻孔不存在: {hole_id}"})
                    continue
                
                pressure = DrillPressureData(
                    drill_hole_id=drill_hole.id,
                    measure_no=parse_int(get_field_value(row, ["测点序号", "measure_no"])),
                    measure_date=get_field_value(row, ["测量日期", "measure_date"]),
                    measure_time=get_field_value(row, ["测量时间", "measure_time"]),
                    wellhead_pressure=parse_float(get_field_value(row, ["井口压力(MPa)", "井口压力", "wellhead_pressure"])),
                    reservoir_pressure=parse_float(get_field_value(row, ["储层压力(MPa)", "储层压力", "reservoir_pressure"])),
                    flowing_pressure=parse_float(get_field_value(row, ["流动压力(MPa)", "流动压力", "flowing_pressure"])),
                    shut_in_pressure=parse_float(get_field_value(row, ["关井压力(MPa)", "关井压力", "shut_in_pressure"])),
                    pressure_gradient=parse_float(get_field_value(row, ["压力梯度(MPa/100m)", "压力梯度", "pressure_gradient"])),
                    measure_depth=parse_float(get_field_value(row, ["测量深度(m)", "measure_depth"])),
                    flow_rate=parse_float(get_field_value(row, ["流量(m³/h)", "流量", "flow_rate"])),
                    water_level=parse_float(get_field_value(row, ["动水位(m)", "动水位", "water_level"])),
                    instrument=get_field_value(row, ["测量仪器", "instrument"]),
                    description=get_field_value(row, ["备注", "description"])
                )
                pressure_to_create.append(pressure)
                success_rows += 1
                
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})
        
        if pressure_to_create:
            db.add_all(pressure_to_create)
        
        db.commit()
        
        record = CsvImportRecord(
            file_name=file.filename,
            import_type="pressure",
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=total_rows - success_rows,
            error_details=errors[:100] if errors else None,
            status="完成"
        )
        db.add(record)
        db.commit()
        
        return CsvImportResult(
            success=True,
            message=f"导入完成：成功{success_rows}行，失败{total_rows - success_rows}行",
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=total_rows - success_rows,
            errors=errors[:20] if errors else None,
            record_id=record.id
        )
        
    except Exception as e:
        logger.error(f"导入压力数据失败: {e}")
        db.rollback()
        return CsvImportResult(success=False, message=f"导入失败: {str(e)}")


# ==================== 孔隙度数据导入 ====================

@router.post("/porosity", response_model=CsvImportResult)
async def import_porosity(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    导入岩石孔隙度数据CSV
    
    必需字段：钻孔编号
    """
    try:
        content = await file.read()
        text_content = decode_content(content)
        
        if not text_content:
            return CsvImportResult(success=False, message="无法解析文件编码")
        
        reader = csv.DictReader(StringIO(text_content))
        
        total_rows = 0
        success_rows = 0
        errors = []
        porosity_to_create = []
        
        for row_num, row in enumerate(reader, start=2):
            total_rows += 1
            
            try:
                hole_id = get_field_value(row, ["钻孔编号", "hole_id"])
                if not hole_id:
                    errors.append({"row": row_num, "error": "缺少钻孔编号"})
                    continue
                
                drill_hole = db.query(DrillHole).filter(DrillHole.hole_id == hole_id).first()
                if not drill_hole:
                    errors.append({"row": row_num, "error": f"钻孔不存在: {hole_id}"})
                    continue
                
                porosity = DrillPorosityData(
                    drill_hole_id=drill_hole.id,
                    sample_no=get_field_value(row, ["样品编号", "sample_no"]),
                    sample_date=get_field_value(row, ["采样日期", "sample_date"]),
                    depth_top=parse_float(get_field_value(row, ["样品顶深(m)", "depth_top"])),
                    depth_bottom=parse_float(get_field_value(row, ["样品底深(m)", "depth_bottom"])),
                    depth=parse_float(get_field_value(row, ["取样深度(m)", "depth"])),
                    lithology=get_field_value(row, ["岩性描述", "岩性", "lithology"]),
                    rock_type=get_field_value(row, ["岩石类型", "rock_type"]),
                    porosity_total=parse_float(get_field_value(row, ["总孔隙度(%)", "总孔隙度", "porosity_total"])),
                    porosity_effective=parse_float(get_field_value(row, ["有效孔隙度(%)", "有效孔隙度", "porosity_effective"])),
                    permeability=parse_float(get_field_value(row, ["渗透率(mD)", "渗透率", "permeability"])),
                    permeability_horizontal=parse_float(get_field_value(row, ["水平渗透率(mD)", "水平渗透率", "permeability_horizontal"])),
                    permeability_vertical=parse_float(get_field_value(row, ["垂直渗透率(mD)", "垂直渗透率", "permeability_vertical"])),
                    density_bulk=parse_float(get_field_value(row, ["体密度(g/cm³)", "体密度", "density_bulk"])),
                    density_grain=parse_float(get_field_value(row, ["颗粒密度(g/cm³)", "颗粒密度", "density_grain"])),
                    water_saturation=parse_float(get_field_value(row, ["含水饱和度(%)", "含水饱和度", "water_saturation"])),
                    test_method=get_field_value(row, ["测试方法", "test_method"]),
                    laboratory=get_field_value(row, ["测试单位", "laboratory"]),
                    description=get_field_value(row, ["备注", "description"])
                )
                porosity_to_create.append(porosity)
                success_rows += 1
                
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})
        
        if porosity_to_create:
            db.add_all(porosity_to_create)
        
        db.commit()
        
        record = CsvImportRecord(
            file_name=file.filename,
            import_type="porosity",
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=total_rows - success_rows,
            error_details=errors[:100] if errors else None,
            status="完成"
        )
        db.add(record)
        db.commit()
        
        return CsvImportResult(
            success=True,
            message=f"导入完成：成功{success_rows}行，失败{total_rows - success_rows}行",
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=total_rows - success_rows,
            errors=errors[:20] if errors else None,
            record_id=record.id
        )
        
    except Exception as e:
        logger.error(f"导入孔隙度数据失败: {e}")
        db.rollback()
        return CsvImportResult(success=False, message=f"导入失败: {str(e)}")


# ==================== 辅助函数 ====================

def decode_content(content: bytes) -> str:
    """尝试用不同编码解码内容"""
    for encoding in ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return ""


def get_field_value(row: Dict[str, str], field_names: List[str]) -> str:
    """从行中获取字段值（支持多个可能的字段名）"""
    for name in field_names:
        if name in row and row[name] is not None and row[name].strip():
            return row[name].strip()
    return ""


def parse_float(value: str) -> float:
    """解析浮点数"""
    if not value:
        return None
    try:
        return float(value.replace(',', ''))
    except (ValueError, AttributeError):
        return None


def parse_int(value: str) -> int:
    """解析整数"""
    if not value:
        return None
    try:
        return int(float(value.replace(',', '')))
    except (ValueError, AttributeError):
        return None
