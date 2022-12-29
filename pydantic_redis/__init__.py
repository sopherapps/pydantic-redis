"""A simple declarative ORM for redis based on pydantic.

Provides:

1. A subclass-able `Model` class to create Object Relational Mapping to
redis hashes
2. A redis `Store` class to mutate and query `Model`'s registered in it
3. A `RedisConfig` class to pass to the `Store` constructor to connect
to a redis instance
4. A synchronous `syncio` and an asynchronous `asyncio` interface to the
above classes
"""

from pydantic_redis.syncio import Store, Model, RedisConfig
import pydantic_redis.asyncio

__all__ = [Store, RedisConfig, Model, asyncio]

__version__ = "0.4.3"
