from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    login,
    api_users,
    proxies,
    social_requests,
    social_parsing_posts,
    social_accounts,
    cookies,
    ipinfo,
    profile_requests
    )


api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(api_users.router, prefix="/api_users", tags=["api_users"])
api_router.include_router(social_requests.router, prefix="/social_requests", tags=["social_requests"])
api_router.include_router(social_parsing_posts.router, prefix="/social_parsing_posts", tags=["social_parsing_posts"])
api_router.include_router(proxies.router, prefix="/proxies", tags=["proxies"])
api_router.include_router(social_accounts.router, prefix="/social_accounts", tags=["social_accounts"])
api_router.include_router(cookies.router, prefix="/cookies", tags=["cookies"])
api_router.include_router(ipinfo.router, prefix="/ipinfo", tags=["ipinfo"])
api_router.include_router(profile_requests.router, prefix="/profile_requests", tags=["profile_requests"])
