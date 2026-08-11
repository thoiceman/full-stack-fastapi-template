from pathlib import Path

import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings

# 前端构建产物目录（bun run build 输出到这里）；开发时可用 Vite :5173，此目录可不存在
FRONTEND_DIR = Path(__file__).parent / "frontend"


def custom_generate_unique_id(route: APIRoute) -> str:
    # OpenAPI operationId，便于前端 openapi-ts 生成更稳定的客户端方法名
    return f"{route.tags[0]}-{route.name}"


# 非开发环境且配置了 DSN 时启用 Sentry 错误与性能追踪
if settings.SENTRY_DSN and settings.FASTAPI_ENV != "development":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# 允许前端源（FRONTEND_HOST，开发默认 http://localhost:5173）跨域访问 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_HOST],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 /api/v1 下的业务路由
app.include_router(api_router, prefix=settings.API_V1_STR)
# 用 FastAPI 同域托管前端静态资源；未 build 时访问 / 会报目录不存在
app.frontend("/", directory=FRONTEND_DIR)
