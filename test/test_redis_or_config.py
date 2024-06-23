import pytest
import redislite
from redis.client import Redis

from pydantic_redis import Store, RedisConfig


def test_need_config_or_redis():
    with pytest.raises(ValueError):
        _ = Store(name="no-redis-or-config")


def test_cannot_provide_both(unused_tcp_port: int):
    redis = redislite.Redis(host="localhost", port=unused_tcp_port)
    config = RedisConfig(host="localhost", port=unused_tcp_port)

    with pytest.raises(ValueError):
        _ = Store(
            name="redis-or-config",
            redis_config=config,
            redis_store=redis,
        )

def test_config_creates_new():
    store = Store(
        name="redis-or-config",
        redis_config=RedisConfig(
            host="localhost",
            port=6379,
            db=0,
        ),
    )
    assert store.redis_store is not None
    assert isinstance(store.redis_store, Redis)


def test_store_creates_new(unused_tcp_port: int):
    redis = redislite.Redis(host="localhost", port=unused_tcp_port)
    pydantic_redis_store = Store(
        name="redis-or-config",
        redis_store=redis,
    )

    assert pydantic_redis_store.redis_store == redis
