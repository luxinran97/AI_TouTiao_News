import traceback

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

ASYNC_DATABASE_URI = "mysql+aiomysql://root:123456@localhost:3306/news_app?charset=utf8"

# 创建异步引擎
async_engin = create_async_engine(ASYNC_DATABASE_URI, echo=False, pool_size=5, max_overflow=10)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engin,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 依赖项，用于获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            print(traceback.print_exc())
            await session.rollback()
            raise
        finally:
            await session.close()