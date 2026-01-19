import secrets

from core.config import Config


class AuthService:    
    def __init__(self, config: Config):
        self.config = config
    
    def verify_credentials(self, username: str, password: str) -> bool:
        if username is None or password is None:
            return False
        
        correct_username = secrets.compare_digest(
            username.encode("utf-8"),
            self.config.admin_user.encode("utf-8")
        )
        correct_password = secrets.compare_digest(
            password.encode("utf-8"),
            self.config.admin_password.encode("utf-8")
        )
        
        return correct_username and correct_password
    
    def get_admin_username(self) -> str:
        return self.config.admin_user