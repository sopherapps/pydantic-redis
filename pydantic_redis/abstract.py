"""Module containing the main base classes"""
from typing import Optional, Union, Any, Dict, List

import orjson
import redis
from pydantic import BaseModel

from pydantic_redis.config import RedisConfig


class _AbstractStore(BaseModel):
    """
    An abstract class of a store
    """
    name: str
    redis_config: RedisConfig
    redis_store: Optional[redis.Redis] = None
    life_span_in_seconds: Optional[int] = None

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
    def _serialize_models_list(cls, data: List[BaseModel]) -> List[str]:
        """Given a list of models, schedules them for insertion and return the list of corresponding primary keys"""
        primary_keys = []
        for model in data:
            subcls = model.__class__
            subcls.insert(model)
            primary_keys.append(subcls._Model__get_primary_key(getattr(model,subcls._primary_key_field)))
        return orjson.dumps(primary_keys)

    @classmethod
    def _deserialize_models_list(cls, data: List[str], field_name_in_parent) -> List[BaseModel]:
        key = field_name_in_parent
        # Inspect datamodel to decide if the value on this key should be even further deserialized (replace primary key by actual values)
        if key in cls.__fields__ and cls.__fields__[key].annotation.mro()[0] is list and cls.__fields__[key].annotation.mro()[1] is object and cls.__fields__[key].type_ is not str:
            # Given how the Parent model is defined, a child model in a list should be deserialized
            if type(data) is list and len(data) > 0 and all(x for x in data):
                # Indeed, there is data to deserialize (replace primary key by actual values)
                data = cls.__fields__[key].type_.select(ids=[x.split("%&_")[1] for x in data]) # Not great to split but I'm not sure how to select() with a key, instead I select with an id
        return data

    @classmethod
    def serialize_partially(cls, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Converts non primitive data types into str"""
        result = {}
        for key, value in data.items():
            if type(value) is list and len(value) > 0 and all(isinstance(v, BaseModel)  for v in value):
                result[key] = cls._serialize_models_list(value)
            else:
                result[key] = orjson.dumps(value)
        return result

    @classmethod
    def deserialize_partially(cls, data: Optional[Dict[bytes, Any]]) -> Dict[str, Any]:
        """Converts non primitive data types into str"""
        result = {}
        for key, value in data.items():
            key = str(key, "utf-8") if isinstance(key, bytes) else key
            result[key] = orjson.loads(value)
            result[key] = cls._deserialize_models_list(result[key], key)
        return result

    @classmethod
    def get_primary_key_field(cls):
        """Gets the protected _primary_key_field"""
        return cls._primary_key_field

    @classmethod
    def insert(cls, data: Union[List[Any], Any]):
        raise NotImplementedError("insert should be implemented")

    @classmethod
    def update(cls, primary_key_value: Union[Any, Dict[str, Any]], data: Dict[str, Any]):
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
