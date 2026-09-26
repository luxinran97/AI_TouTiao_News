from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from crud import users
from crud.users import get_user_by_username, create_user, create_token, authenticate_user, update_user, update_password
from models.users import User
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse, UserUpdateRequest, UserChangePasswordResponse

from config.db_conf import get_db
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/register")
async def register_user(user_data:UserRequest ,db: AsyncSession = Depends(get_db)):
    # 进入请求校验参数-->检查用户是否存在-->创建用户-->升成访问令牌-->响应结果
    ans =  await get_user_by_username(db, user_data.username)
    if ans:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='用户已经存在')

    user = await create_user(db, user_data)
    token = await create_token(db, user.id)
    response_data = UserAuthResponse(token=token, userInfo=UserInfoResponse.model_validate(user))
    return success_response(data=response_data)

@router.post("/login")
async def login(user_data:UserRequest ,db: AsyncSession = Depends(get_db)):
    # 验证用户是否存在-->验证密码-->升成 Token-->响应结果
    user = await authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    token = await create_token(db, user.id)
    response_data = UserAuthResponse(
        token=token,
        user_info=UserInfoResponse.model_validate(user)
    )

    return success_response(message='登录成功' ,data=response_data)

@router.get("/info")
async def get_user_info(user: User = Depends(get_current_user)):
    return success_response(message='success', data=UserInfoResponse.model_validate(user))

# 修改用户信息：验证 token->更新（输入用户信息 put 提交->请求体参数->定义 Pydantic 模型类）->响应结果
@router.put("/update")
async def update_user_info(user_data:UserUpdateRequest ,user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await update_user(db,user.username, user_data)
    return success_response(message='success', data=UserInfoResponse.model_validate(user))

@router.put("/password")
async def change_password(password_data:UserChangePasswordResponse ,user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res_change_pwd = await users.update_password(
        db,
        user,
        password_data
    )

    if not res_change_pwd:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败，请检查旧密码"
        )

    return success_response(message="修改密码成功")