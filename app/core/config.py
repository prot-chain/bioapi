from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Config(BaseSettings):

    redis_url: str = ''

    model_config = SettingsConfigDict(env_file='.env')


# get_config retrieves the configuration detail for
@lru_cache
def get_config() -> Config:
    return Config()
