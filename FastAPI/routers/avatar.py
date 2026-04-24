"""
用户头像上传路由
"""
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse
import os
import uuid
from config.db_config import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from crud import users as user_crud
from routers.users import get_current_user_id

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """上传用户头像"""
    # 检查文件类型
    if not file.content_type.startswith('image/'):
        return {"code": 400, "message": "只支持图片文件", "data": None}
    
    # 限制文件大小 2MB
    file_content = await file.read()
    if len(file_content) > 2 * 1024 * 1024:
        return {"code": 400, "message": "图片大小不能超过2MB", "data": None}
    
    # 生成唯一文件名
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"avatar_{user_id}_{uuid.uuid4().hex}.{file_extension}"
    
    # 保存路径
    upload_dir = "uploads/avatars"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    
    # 写入文件
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # 生成访问URL (返回完整URL，确保手机端能访问)
    avatar_url = f"http://192.168.117.44:8000/uploads/avatars/{filename}"
    
    # 更新数据库
    user = await user_crud.get_user_by_id(db, user_id)
    if user:
        user.avatar = avatar_url
        await db.flush()
    
    return {
        "code": 200,
        "message": "上传成功",
        "data": {"avatar": avatar_url}
    }
