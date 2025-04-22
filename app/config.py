from functools import lru_cache
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    upload_dir: str = str(Path(__file__).parent.parent / "uploads")

@lru_cache()
def get_settings():
    return Settings()
