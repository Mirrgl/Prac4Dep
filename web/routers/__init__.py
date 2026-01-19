from web.routers.auth import router as auth_router
from web.routers.pages import router as pages_router
from web.routers.api import router as api_router

__all__ = [
    "auth_router",
    "pages_router",
    "api_router",
]
