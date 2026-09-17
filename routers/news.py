from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import news

router = APIRouter(prefix="/api/news", tags=["news"])

@router.get("/categories")
async def get_categories(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # 获取数据库新闻分类-》先定义模型类=》封装方法
    categories = await news.get_categories(db, skip, limit)
    return {
        'code': 200,
        'message': 'success',
        'data': categories,
    }