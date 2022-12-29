"""Exposes the configuration for connecting to a redis database.
"""
from typing import Optional

from pydantic import BaseModel


class RedisConfig(BaseModel):
    """Configuration for connecting to redis database.

    Inorder to connect to a redis database, there are a number of
    configurations that are needed including the server's host address
    and port. `RedisConfig` computes a redis-url similar to
    `redis://:password@host:self.port/db`

    Attributes:
        host (str): the host address where the redis server is found (default: 'localhost').
        port (int): the port on which the redis server is running (default: 6379).
        db (int): the redis database identifier (default: 0).
        password (Optional[int]): the password for connecting to the
            redis server (default: None).
        ssl (bool): whether the connection to the redis server is to be via TLS (default: False)
        encoding: (Optional[str]): the string encoding used with the redis database
            (default: utf-8)
    """

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    encoding: Optional[str] = "utf-8"

    @property
    def redis_url(self) -> str:
        """a redis URL of form `redis://:password@host:port/db`. (`rediss://..` if TLS)."""
        proto = "rediss" if self.ssl else "redis"
        if self.password is None:
            return f"{proto}://{self.host}:{self.port}/{self.db}"
        return f"{proto}://:{self.password}@{self.host}:{self.port}/{self.db}"

    class Config:
        orm_mode = True
