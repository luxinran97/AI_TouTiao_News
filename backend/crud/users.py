import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User, UserToken
from schemas.users import UserRequest, UserUpdateRequest, UserChangePasswordResponse
from utils import security


async def get_user_by_username(db: AsyncSession, username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_data: UserRequest):
    hash_password = security.generate_password_hash(user_data.password)
    user = User(username=user_data.username, password=hash_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_token(db: AsyncSession, user_id: int):
    token = str(uuid.uuid4())
    expire_date = datetime.now() + timedelta(days=7)
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()

    if user_token is not None:
        user_token.token = token
        user_token.expires_at = expire_date # 发现快照变了自动 update
        await db.commit()
    else:
        user_token = UserToken(user_id=user_id, token=token, expires_at=expire_date)
        db.add(user_token)
        await db.commit()

    return token


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return None

    if not security.verify_password(password, user.password):
        return None

    return user

# 根据 token 查询用户
async def get_user_by_token(db: AsyncSession, token: str):
    query = select(UserToken).where(UserToken.token == token)
    result = await db.execute(query)
    db_token =  result.scalar_one_or_none()

    if db_token is None or db_token.expires_at < datetime.now():
        return None

    query = select(User).where(User.id == db_token.user_id)
    result = await db.execute(query)
    db_user = result.scalar_one_or_none()
    if db_user is None:
        return None
    return db_user

async def update_user(db: AsyncSession, user_name:str, user_data: UserUpdateRequest):
    query =  update(User).where(User.username == user_name).values(**user_data.model_dump(exclude_none=True, exclude_unset=True))
    result = await db.execute(query)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await get_user_by_username(db, user_name)
    return updated_user

async def update_password(db: AsyncSession, user: User, password_data: UserChangePasswordResponse):
    if not security.verify_password(password_data.old_password, user.password):
        return False

    hashed_new_pwd = security.get_hash_password(password_data.new_password)
    user.password = hashed_new_pwd

    # 更新：由 SQLAlchemy 真正接管这个 User 对象，确保可以 commit
    # 规避 session 过期或关闭导致的不能提交的问题
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return True
