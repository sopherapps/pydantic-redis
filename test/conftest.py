import pytest
import redislite

from pydantic_redis.config import RedisConfig
from pydantic_redis.model import Model
from pydantic_redis.store import Store


@pytest.fixture()
def redis_server(unused_tcp_port):
    """Sets up a fake redis server we can use for tests"""
    instance = redislite.Redis(serverconfig={"port": unused_tcp_port})
    yield unused_tcp_port
    instance.close()
