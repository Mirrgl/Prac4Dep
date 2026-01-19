import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from ..dependencies import check_auth_status


logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    error: Optional[str] = None,
    is_authenticated: bool = Depends(check_auth_status)
):
    if is_authenticated:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        request, "login.html",
        {"error": error}
    )


@router.get("/logout")
async def logout():
    return Response(
        content="Logged out",
        status_code=status.HTTP_401_UNAUTHORIZED,
        media_type="text/plain"
    )
