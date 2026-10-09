from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
from pydantic import computed_field, SecretStr
from urllib.parse import quote_plus
import hmac
import hashlib
from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    
    secret_key: SecretStr
    jwt_lifetime_seconds: int = 3600
    
    openai_api_key: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    db_host: str = "localhost"
    db_port: int = 5432
    
    
    
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")
    
    
    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{quote_plus(self.postgres_password)}"
            f"@{self.db_host}:{self.db_port}/{self.postgres_db}"
        )
    @property
    def sqlalchemy_url(self) -> str:
        return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
            
    def _derive(self, label: str) -> str:
        return hmac.new(
            self.secret_key.get_secret_value().encode(),
            label.encode(),
            hashlib.sha256,
        ).hexdigest()

    @cached_property
    def jwt_secret(self) -> str:
        return self._derive("jwt")

    @cached_property
    def reset_password_secret(self) -> str:
        return self._derive("reset-password")

    @cached_property
    def verification_secret(self) -> str:
        return self._derive("verification")
    
settings = Settings()    
