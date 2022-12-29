"""Exposes the `Store` for managing a collection of asynchronous Model's.

Stores represent a collection of different kinds of records saved in
a redis database. They only expose records whose `Model`'s have been
registered in them. Thus redis server can have multiple stores each
have a different image of the actual data in redis.

A model must be registered with a store before it can interact with
a redis database.
"""
from typing import Dict, Type, TYPE_CHECKING

from redis import asyncio as redis

from .._shared.store import AbstractStore

if TYPE_CHECKING:
    from .model import Model


class Store(AbstractStore):
    """Manages a collection of Model's, connecting them to a redis database

    A Model can only interact with a redis database when it is registered
    with a `Store` that is connected to that database.

    Attributes:
        models (Dict[str, Type[pydantic_redis.syncio.Model]]): a mapping of registered `Model`'s, with the keys being the
            Model name
        name (str): the name of this Store
        redis_config (pydantic_redis.syncio.RedisConfig): the configuration for connecting to a redis database
        redis_store (Optional[redis.Redis]): an Redis instance associated with this store (default: None)
        life_span_in_seconds (Optional[int]): the default time-to-live for the records inserted in this store
            (default: None)
    """

    models: Dict[str, Type["Model"]] = {}

    def _connect_to_redis(self) -> redis.Redis:
        """Connects the store to redis.

        See the base class.
        """
        return redis.from_url(
            self.redis_config.redis_url,
            encoding=self.redis_config.encoding,
            decode_responses=True,
        )
