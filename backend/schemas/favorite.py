from pydantic import BaseModel, Field, ConfigDict

from schemas.base import NewsItemBase


# 检查收藏状态
class FavoriteCheckResponse(BaseModel):
    is_favorite: bool = Field(..., alias="isFavorite")

# 添加收藏
class FavoriteAddRequest(BaseModel):
    news_id: int = Field(..., alias="newsId")


# 收藏列表接口响应模型类
class FavoriteListResponse(BaseModel):
    list: list[NewsItemBase]
    total: int
    has_more: bool = Field(alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )