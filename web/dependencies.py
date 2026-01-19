import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from core.config import Config, load_config
from data.client import DatabaseClient, DatabaseConfig
from data.repository import EventRepository
from services.auth_service import AuthService
from services.event_service import EventService


logger = logging.getLogger(__name__)

security = HTTPBasic(auto_error=False)

_config: Optional[Config] = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_db_client(config: Config = Depends(get_config)) -> DatabaseClient:
    return DatabaseClient(DatabaseConfig(
        host=config.db_host,
        port=config.db_port,
        database="siem"
    ))


def get_auth_service(config: Config = Depends(get_config)) -> AuthService:
    return AuthService(config)


def get_event_service(db_client: DatabaseClient = Depends(get_db_client)) -> EventService:
    repository = EventRepository(db_client)
    return EventService(repository)


def require_auth(
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> str:
    if credentials is None:
        logger.debug("Authentication required - no credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": 'Basic realm="SIEM Web Interface"'},
        )
    
    if not auth_service.verify_credentials(credentials.username, credentials.password):
        logger.warning(f"Failed authentication attempt for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": 'Basic realm="SIEM Web Interface"'},
        )
    
    logger.debug(f"User {credentials.username} authenticated successfully")
    return credentials.username


def get_current_user(
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[str]:
    if credentials is None:
        return None
    
    if auth_service.verify_credentials(credentials.username, credentials.password):
        return credentials.username
    return None


def check_auth_status(
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> bool:
    if credentials is None:
        return False
    
    return auth_service.verify_credentials(credentials.username, credentials.password)
