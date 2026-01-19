import logging
from pathlib import Path

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..dependencies import require_auth


logger = logging.getLogger(__name__)

router = APIRouter(tags=["pages"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    username: str = Depends(require_auth)
):
    return templates.TemplateResponse(
        request, "dashboard.html",
        {"username": username}
    )


@router.get("/events", response_class=HTMLResponse)
async def events_page(
    request: Request,
    username: str = Depends(require_auth)
):
    response = templates.TemplateResponse(
        request, "events.html",
        {"username": username}
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
