from fastapi import APIRouter

from app.api.routes import items, login, notes, private, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(notes.router)


# 仅开发环境挂载：提供无鉴权的测试用接口（如直接创建用户），生产不可用
if settings.FASTAPI_ENV == "development":
    api_router.include_router(private.router)
