"""Module containing the store classes for sync io"""
from typing import Dict, Type, TYPE_CHECKING

import redis

from ..shared.store import AbstractStore

if TYPE_CHECKING:
    from .model import Model


class Store(AbstractStore):
    """
    A store that allows a declarative way of querying for data in redis
    """

    models: Dict[str, Type["Model"]] = {}

    def _connect_to_redis(self) -> redis.Redis:
        """Connects the store to redis, returning a proper connection"""
        return redis.from_url(
            self.redis_config.redis_url,
            encoding=self.redis_config.encoding,
            decode_responses=True,
        )
