from http.client import HTTPException

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.params import Query
from sqlalchemy import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.testing.schema import table_options

from cache.news_cache import get_cache_news_list, set_cache_news_list
from config.db_conf import get_db
from crud import news
from models.news import News
from schemas.base import NewsItemBase

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

@router.get("/list")
async def get_news(
        category_id: int = Query(..., alias="categoryId"),
        page: int = 1,
        page_size: int = 100,
        db: AsyncSession = Depends(get_db)
):


    page = page // page_size + 1
    news_list = await get_cache_news_list(category_id, page, page_size)  # 缓存数据 json

    offset = (page - 1) * page_size
    total = await news.get_news_count(db, category_id)
    has_more = (offset + len(news_list)) < total

    if news_list:
        # return cached_list  # 要的是 ORM
        return {
        'code': 200,
        'message': 'success',
        'data':{
            "list": [News(**item) for item in news_list],
            "total": total,
            "hasMore": has_more,
        }
    }


    news_list = await news.get_news_list(db, category_id, page, page_size)


    # 写入缓存
    if news_list:
        # 先把 ORM 数据 转换 字典才能写入缓存
        # ORM 转成 Pydantic，再转为 字典
        # by_alias=False 不适用别名，保存 Python 风格，因为 Redis 数据是给后端用的
        news_data = [
            NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False)
            for item in news_list
        ]
        await set_cache_news_list(category_id, page, page_size, news_data)

    return {
        'code': 200,
        'message': 'success',
        'data':{
            "list": jsonable_encoder(news_list),
            "total": total,
            "hasMore": has_more,
        }
    }


@router.get("/detail")
async def get_news_detail(
        news_id: int = Query(..., alias="id"),
        db: AsyncSession = Depends(get_db)
):
    """
    获取新闻详情
    :param news_id:
    :param db:
    :return:
    """
    news_detail = await news.get_news_detail(db, news_id)

    if news_detail is None:
        return Result.error(code=404, detail="该新闻不存在")

    views_res = await news.increase_news_count(db, news_id)
    if not views_res:
        raise HTTPException(status_code=404, detail="新闻不存在")

    related_news = await news.get_related_news(db, news_id, news_detail.category_id)

    return {
        'code': 200,
        'message': 'success',
        "data": {
            **jsonable_encoder(news_detail),
            "relatedNews": related_news
        },
    }
