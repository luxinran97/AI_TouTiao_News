import datetime

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.history import History
from models.news import News
from models.users import User


async def add_history(db:AsyncSession, user:User, news_id:int):
    query = select(History).where(History.user_id == user.id, History.news_id == news_id)
    result = await db.execute(query)
    existing_history = result.scalar()
    if existing_history:
        existing_history.view_time = datetime.datetime.now()
        await db.commit()
        await db.refresh(existing_history)
        return existing_history
    else:
        updated_history = History(user_id=user.id, news_id=news_id)
        db.add(updated_history)
        await db.commit()
        await db.refresh(updated_history)
        return updated_history

async def get_history(db:AsyncSession, user:User, page:int=1, page_size:int=10):
    offset = (page - 1) * page_size
    query = select(func.count(History.id)).where(History.user_id == user.id)
    count_result = await db.execute(query)
    total = count_result.scalar_one()

    query =(select(News, History.view_time.label("view_time"), History.id.label("history_id"))
             .join(History, History.news_id == News.id)
             .where(History.user_id == user.id)
             .order_by(History.view_time.desc())
             .offset(offset)).limit(page_size)
    result = await db.execute(query)
    rows = result.all()
    return rows, total

async def delete_history(db:AsyncSession, user:User, history_id:int):
    query = delete(History).where(History.user_id == user.id, History.news_id == history_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0

async def clear_history(db:AsyncSession, user:User):
    query = delete(History).where(History.user_id == user.id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount>0
