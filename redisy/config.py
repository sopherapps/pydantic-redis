"""Module containing the main config classes"""

from pydantic import BaseModel


class RedisConfig(BaseModel):
    host: str = 'localhost'
    port: int = 6379
    db: int = 0

    class Config:
        orm_mode = True
