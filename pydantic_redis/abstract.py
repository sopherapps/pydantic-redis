"""Module containing the main base classes"""
from typing import Optional, Union, Any, Dict, List, Callable, Tuple, Type

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
    _nested_model_tuple_fields: Dict[str, Tuple[Any, ...]] = {}
    _nested_model_list_fields: Dict[str, Type["_AbstractModel"]] = {}
    _nested_model_fields: Dict[str, Type["_AbstractModel"]] = {}
    _field_types: Dict[str, Any] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def serialize_partially(cls, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Converts non primitive data types into str"""
        return {key: _from_any_to_str_or_bytes(value) for key, value in data.items()}

    @classmethod
    def deserialize_partially(
        cls, data: Union[List[Any], Dict[Any, Any]] = ()
    ) -> Dict[str, Any]:
        """
        Converts str or bytes to their expected data types, given a list of properties got from the
        list of lists got after calling EVAL on redis.

        EVAL returns a List of Lists of key, values where the value for a given key is in the position
        just after the key e.g. [["foo", "bar", "head", 9]] => [{"foo": "bar", "head": 9}]

        Note: For backward compatibility, data can also be a dict.
        """
        if isinstance(data, dict):
            # for backward compatibility
            data = _from_dict_to_key_value_list(data)

        parsed_dict = {}

        for i in range(0, len(data), 2):
            key = _from_bytes_to_str(data[i])
            field_type = cls._field_types.get(key)
            value = _from_str_or_bytes_to_any(value=data[i + 1], field_type=field_type)

            if key in cls._nested_model_list_fields and value is not None:
                value = cls.__deserialize_nested_model_list(field=key, value=value)

            elif key in cls._nested_model_tuple_fields and value is not None:
                value = cls.__deserialize_nested_model_tuple(field=key, value=value)

            elif key in cls._nested_model_fields and value is not None:
                value = cls.__deserialize_nested_model(field=key, value=value)

            parsed_dict[key] = value

        return parsed_dict

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

    @classmethod
    def __deserialize_nested_model_list(
        cls, field: str, value: List[Any]
    ) -> List["_AbstractModel"]:
        """Deserializes a list of key values for the given field returning a list of nested models"""
        field_type = cls._nested_model_list_fields.get(field)
        return [field_type(**field_type.deserialize_partially(item)) for item in value]

    @classmethod
    def __deserialize_nested_model_tuple(
        cls, field: str, value: List[Any]
    ) -> Tuple[Any, ...]:
        """Deserializes a list of key values for the given field returning a tuple of nested models among others"""
        field_types = cls._nested_model_tuple_fields.get(field, ())

        items = []
        for field_type, value in zip(field_types, value):
            if issubclass(field_type, _AbstractModel) and value is not None:
                value = field_type(**field_type.deserialize_partially(value))
            items.append(value)

        return tuple(items)

    @classmethod
    def __deserialize_nested_model(
        cls, field: str, value: List[Any]
    ) -> "_AbstractModel":
        """Deserializes a list of key values for the given field returning the nested model"""
        field_type = cls._nested_model_fields.get(field)
        return field_type(**field_type.deserialize_partially(value))


def _from_bytes_to_str(value: Union[str, bytes]) -> str:
    """Converts bytes to str"""
    if isinstance(value, bytes):
        return str(value, "utf-8")
    return value


def _from_str_or_bytes_to_any(value: Any, field_type: Type) -> Any:
    """Converts str or bytes to arbitrary data"""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return orjson.loads(value)
    elif isinstance(value, str) and field_type != str:
        return orjson.loads(value)
    return value


def _from_any_to_str_or_bytes(value: Any) -> Union[str, bytes]:
    """Converts arbitrary data into str or bytes"""
    if isinstance(value, str):
        return value
    return orjson.dumps(value, default=_default_json_dump)


def _default_json_dump(obj):
    """Default JSON dump for orjson"""
    if hasattr(obj, "json") and isinstance(obj.json, Callable):
        return obj.json()
    elif isinstance(obj, set):
        # Set does not exist in JSON.
        # It's fine to use list instead, it becomes a Set when deserializing.
        return list(obj)


def _from_dict_to_key_value_list(data: Dict[str, Any]) -> List[Any]:
    """Converts dict to flattened list of key, values where the value after the key"""
    parsed_list = []

    for k, v in data.items():
        parsed_list.append(k)
        parsed_list.append(v)

    return parsed_list
