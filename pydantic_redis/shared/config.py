"""Module containing the main config classes"""
from typing import Optional

from pydantic import BaseModel


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    encoding: Optional[str] = "utf-8"

    @property
    def redis_url(self) -> str:
        """Returns a redis url to connect to"""
        proto = "rediss" if self.ssl else "redis"
        if self.password is None:
            return f"{proto}://{self.host}:{self.port}/{self.db}"
        return f"{proto}://:{self.password}@{self.host}:{self.port}/{self.db}"

    class Config:
        orm_mode = True
