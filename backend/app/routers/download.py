"""
文件下载 API
"""
from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(tags=["文件下载"])

@router.get("/download/project")
async def download_project():
    """下载项目源码压缩包"""
    file_path = "/workspace/projects/geothermal-project.tar.gz"
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename="geothermal-project.tar.gz",
            media_type="application/gzip"
        )
    return {"error": "文件不存在"}
