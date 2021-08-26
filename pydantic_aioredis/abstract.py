"""Module containing the main base classes"""
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import aioredis
from pydantic import BaseModel

from pydantic_aioredis.config import RedisConfig
from pydantic_aioredis.utils import bytes_to_string


class _AbstractStore(BaseModel):
    """
    An abstract class of a store
    """

    name: str
    redis_config: RedisConfig
    redis_store: aioredis.Redis = None
    life_span_in_seconds: int = None

    class Config:
        """Pydantic schema config"""

        arbitrary_types_allowed = True
        orm_mode = True


class _AbstractModel(BaseModel):
    """
    An abstract class to help with typings for Model class
    """

    _store: _AbstractStore
    _primary_key_field: str

    @staticmethod
    def serialize_partially(data: Dict[str, Any]):
        """Converts non primitive data types into str"""
        return {
            key: (
                value
                if isinstance(value, (str, float, int))
                and not isinstance(value, (bool,))
                else str(value)
            )
            for key, value in data.items()
        }

    @staticmethod
    def deserialize_partially(data: Dict[bytes, Any]):
        """Converts non primitive data types into str"""
        return {
            bytes_to_string(key): (
                bytes_to_string(value) if isinstance(value, (bytes,)) else value
            )
            for key, value in data.items()
        }

    @classmethod
    def get_primary_key_field(cls):
        """Gets the protected _primary_key_field"""
        return cls._primary_key_field

    @classmethod
    @classmethod
    async def insert(
        cls,
        data: Union[List["_AbstractModel"], "_AbstractModel"],
        life_span_seconds: Optional[int] = None,
    ):  # pragma: no cover
        """Insert into the redis store"""
        raise NotImplementedError("insert should be implemented")

    @classmethod
    async def update(
        cls, _id: Any, data: Dict[str, Any], life_span_seconds: Optional[int] = None
    ):  # pragma: no cover
        """Update an existing key"""
        raise NotImplementedError("update should be implemented")

    @classmethod
    async def delete(cls, ids: Union[Any, List[Any]]):  # pragma: no cover
        """Delete a key"""
        raise NotImplementedError("delete should be implemented")

    @classmethod
    async def select(
        cls, columns: Optional[List[str]] = None, ids: Optional[List[Any]] = None
    ):  # pragma: no cover
        """Should later allow AND, OR"""
        raise NotImplementedError("select should be implemented")

    class Config:
        """Pydantic schema config"""

        arbitrary_types_allowed = True
