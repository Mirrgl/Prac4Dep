import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    db_host: str
    db_port: int
    
    web_host: str
    web_port: int
    
    admin_user: str
    admin_password: str
    
    def __post_init__(self):
        if not self.admin_password:
            raise ValueError("SIEM_ADMIN_PASSWORD environment variable is required")
        
        if self.db_port <= 0 or self.db_port > 65535:
            raise ValueError(f"Invalid database port: {self.db_port}")
        
        if self.web_port <= 0 or self.web_port > 65535:
            raise ValueError(f"Invalid web server port: {self.web_port}")


def load_config() -> Config:
    db_host = os.environ.get("SIEM_DB_HOST", "127.0.0.1")
    
    try:
        db_port = int(os.environ.get("SIEM_DB_PORT", "8080"))
    except ValueError:
        raise ValueError("SIEM_DB_PORT must be a valid integer")
    
    web_host = os.environ.get("SIEM_WEB_HOST", "0.0.0.0")
    
    try:
        web_port = int(os.environ.get("SIEM_WEB_PORT", "8000"))
    except ValueError:
        raise ValueError("SIEM_WEB_PORT must be a valid integer")
    
    admin_user = os.environ.get("SIEM_ADMIN_USER", "admin")
    admin_password = os.environ.get("SIEM_ADMIN_PASSWORD", "")
    
    return Config(
        db_host=db_host,
        db_port=db_port,
        web_host=web_host,
        web_port=web_port,
        admin_user=admin_user,
        admin_password=admin_password
    )