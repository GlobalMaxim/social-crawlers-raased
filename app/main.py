import asyncio
import aioschedule
from fastapi import FastAPI
# from sqladmin import Admin, ModelView
from starlette.middleware.cors import CORSMiddleware

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from fastapi_utils.tasks import repeat_every
from app.api.api_v1.api import api_router
from app.core.config import settings
from app.services.account_logging.cookie_manager import unlock_all_cookies
# from app.models.api_user import ApiUser

engine_local = create_engine(settings.SQLALCHEMY_DATABASE_URI_LOCAL, poolclass=StaticPool, echo=False)

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# async def scheduler():
#     aioschedule.every(1).seconds.do(unlock_all_cookies, 5)

#     while True:
#         await aioschedule.run_pending()
#         await asyncio.sleep(10)

@app.on_event("startup")
@repeat_every(seconds=10)
def startup():
    unlock_all_cookies(settings.CLEAR_COOKIES_AFTER_MINUTES)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

# admin = Admin(app, engine_local)

# class ApiUserAdmin(ModelView, model=ApiUser):
#     column_list = [
#         ApiUser.id,
#         ApiUser.email,
#         ApiUser.full_name,
#         ApiUser.is_superuser,
#         ApiUser.is_active
#     ]

# admin.add_view(ApiUserAdmin)