"""Module containing the main base classes"""
from typing import Optional, Union, Any, Dict, List, Callable

import orjson
import redis
from pydantic import BaseModel
from redis.commands.core import Script

from pydantic_redis.config import RedisConfig


class _AbstractStore(BaseModel):
    """
    An abstract class of a store
    """

    name: str
    redis_config: RedisConfig
    redis_store: Optional[redis.Redis] = None
    life_span_in_seconds: Optional[int] = None
    select_all_fields_for_all_ids_script: Optional[Script] = None
    select_all_fields_for_some_ids_script: Optional[Script] = None
    select_some_fields_for_all_ids_script: Optional[Script] = None
    select_some_fields_for_some_ids_script: Optional[Script] = None

    class Config:
        arbitrary_types_allowed = True
        orm_mode = True


class _AbstractModel(BaseModel):
    """
    An abstract class to help with typings for Model class
    """

    _store: _AbstractStore
    _primary_key_field: str

    @classmethod
    def serialize_partially(cls, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Converts non primitive data types into str"""
        return {
            key: value
            if isinstance(value, str)
            else orjson.dumps(value, default=_default_json_dump)
            for key, value in data.items()
        }

    @classmethod
    def deserialize_partially(cls, data: Optional[Dict[bytes, Any]]) -> Dict[str, Any]:
        """Converts non primitive data types into str"""
        return {
            str(key, "utf-8")
            if isinstance(key, bytes)
            else key: value
            if isinstance(value, str)
            else orjson.loads(value)
            for key, value in data.items()
        }

    @classmethod
    def get_primary_key_field(cls):
        """Gets the protected _primary_key_field"""
        return cls._primary_key_field

    @classmethod
    def insert(cls, data: Union[List[Any], Any]):
        raise NotImplementedError("insert should be implemented")

    @classmethod
    def update(
        cls, primary_key_value: Union[Any, Dict[str, Any]], data: Dict[str, Any]
    ):
        raise NotImplementedError("update should be implemented")

    @classmethod
    def delete(cls, primary_key_value: Union[Any, Dict[str, Any]]):
        raise NotImplementedError("delete should be implemented")

    @classmethod
    def select(cls, columns: Optional[List[str]] = None):
        """Should later allow AND, OR"""
        raise NotImplementedError("select should be implemented")

    class Config:
        arbitrary_types_allowed = True


def _default_json_dump(obj):
    """Default JSON dump for orjson"""
    if hasattr(obj, "json") and isinstance(obj.json, Callable):
        return obj.json()
    elif isinstance(obj, set):
        # Set does not exist in JSON. It's fine to use list instead, it becomes a Set when deserializing.
        return list(obj)
