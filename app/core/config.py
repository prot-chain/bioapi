from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Config(BaseSettings):
    redis_url: str = ''
    workflow_binary_path: str = os.getenv("WORKFLOW_BINARY_PATH", "/app/bin/protchainworkflow")
    data_dir: str = os.getenv("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"))
    upload_dir: str = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "uploads"))

    model_config = SettingsConfigDict(env_file='.env')


# get_config retrieves the configuration detail for
@lru_cache
def get_config() -> Config:
    return Config()

# Create a global settings instance
settings = get_config()