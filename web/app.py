import logging
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import Response, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from web.dependencies import get_config
from web.routers import auth_router, pages_router, api_router

# Загрузка переменных из .env файла
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

def create_app() -> FastAPI:
    app = FastAPI(
        title="SIEM Web Interface",
        description="Security Information and Event Management monitoring interface",
        version="1.0.0"
    )
    
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
    
    app.include_router(auth_router)
    app.include_router(pages_router)
    app.include_router(api_router)
    
    _add_exception_handlers(app)
    
    _add_lifecycle_events(app)
    
    @app.get("/")
    async def root():
        return RedirectResponse(url="/login")
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "siem-web"}
    
    return app


def _add_exception_handlers(app: FastAPI) -> None:    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return Response(
                content=exc.detail or "Authentication required",
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="text/plain",
                headers={"WWW-Authenticate": 'Basic realm="SIEM Web Interface"'}
            )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(
            f"Unexpected error processing request {request.method} {request.url.path}: {exc}",
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": "An unexpected error occurred. Please try again later."
            }
        )


def _add_lifecycle_events(app: FastAPI) -> None:    
    @app.on_event("startup")
    async def startup_event():
        logger.info("SIEM Web Interface starting up...")
        
        try:
            config = get_config()
            logger.info(f"Configuration loaded successfully. "
                       f"Database: {config.db_host}:{config.db_port}, "
                       f"Web server: {config.web_host}:{config.web_port}")
            logger.info(f"Access the application at: http://{config.web_host}:{config.web_port}")
        except ValueError as e:
            logger.error(f"Configuration error during startup: {e}")
            print(f"Warning: Configuration error: {e}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("SIEM Web Interface shutting down...")
        
        try:
            logger.info("SIEM Web Interface shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

app = create_app()
