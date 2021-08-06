"""Module containing the main config classes"""
from typing import Optional

from pydantic import BaseModel


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    ssl_ca_certs: Optional[str] = None

    class Config:
        orm_mode = True
