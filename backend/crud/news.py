from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from cache.news_cache import get_cached_categories, set_cache_categories
from models.news import Category, News


async def get_categories(db:AsyncSession, skip: int = 0, limit: int = 100):
    # 先尝试从缓存中获取
    cached_categories = await get_cached_categories()
    if cached_categories:
        return cached_categories
    stmt =  select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)

    categories = result.scalars().all()
    if categories:
        temp =  jsonable_encoder(categories)
        await set_cache_categories(temp)

    return categories


async def get_news_list(
        db: AsyncSession,
        category_id: int,
        skip: int = 0,
        limit: int = 10
):
    # 查询的是指定分类下的所有新闻
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_news_count(
        db: AsyncSession,
        category_id: int
):
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one()  # 只能有一个结果，否则报错

async def get_news_detail(
        db: AsyncSession,
        news_id:int,
):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one()

async def increase_news_count(
        db: AsyncSession,
        news_id: int
):
    stmt = update(News).where(News.id == news_id).values(views = News.views + 1)
    result =  await db.execute(stmt)
    await db.commit()

    # 更新->检查数据库是否真的命中了数据->命中了返回 True
    return result.rowcount > 0

async def get_related_news(
        db: AsyncSession,
        news_id: int,
        category_id: int,
        limit: int = 5
):
    # 按照浏览量和发布时间排序
    stmt = select(News).where(News.id != news_id, News.category_id == category_id).order_by(News.views.desc(), News.publish_time.desc()).limit(limit)
    result = await db.execute(stmt)
    related_news =  result.scalars().all()
    return [{
        "id": news_detail.id,
        "title": news_detail.title,
        "content": news_detail.content,
        "publish_time": news_detail.publish_time,
        "views": news_detail.views,
        "image": news_detail.image,
        "author": news_detail.author,
        "categoryId": news_detail.category_id,
    } for news_detail in related_news]