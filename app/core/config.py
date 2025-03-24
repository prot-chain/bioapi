from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Config(BaseSettings):

    redis_url: str = ''

    model_config = SettingsConfigDict(env_file='.env')


# get_config retrieves the configuration detail for
@lru_cache
def get_config() -> Config:
    return Config()

# Add these settings to your existing config file
WORKFLOW_BINARY_PATH = os.getenv("WORKFLOW_BINARY_PATH", "/app/bin/protchainworkflow")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")