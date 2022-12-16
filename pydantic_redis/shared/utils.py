"""Module containing common utilities"""
import typing
from typing import Any, Tuple, Optional, Union, Dict, Callable, Type, List

import orjson


def strip_leading(word: str, substring: str) -> str:
    """
    Strips the leading substring if it exists.
    This is contrary to rstrip which can looks at removes each character in the substring
    """
    if word.startswith(substring):
        return word[len(substring) :]
    return word


def typing_get_args(v: Any) -> Tuple[Any, ...]:
    """Gets the __args__ of the annotations of a given typing"""
    try:
        return typing.get_args(v)
    except AttributeError:
        return getattr(v, "__args__", ()) if v is not typing.Generic else typing.Generic


def typing_get_origin(v: Any) -> Optional[Any]:
    """Gets the __origin__ of the annotations of a given typing"""
    try:
        return typing.get_origin(v)
    except AttributeError:
        return getattr(v, "__origin__", None)


def from_bytes_to_str(value: Union[str, bytes]) -> str:
    """Converts bytes to str"""
    if isinstance(value, bytes):
        return str(value, "utf-8")
    return value


def from_str_or_bytes_to_any(value: Any, field_type: Type) -> Any:
    """Converts str or bytes to arbitrary data"""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return orjson.loads(value)
    elif isinstance(value, str) and field_type != str:
        return orjson.loads(value)
    return value


def from_any_to_str_or_bytes(value: Any) -> Union[str, bytes]:
    """Converts arbitrary data into str or bytes"""
    if isinstance(value, str):
        return value
    return orjson.dumps(value, default=default_json_dump)


def default_json_dump(obj):
    """Default JSON dump for orjson"""
    if hasattr(obj, "json") and isinstance(obj.json, Callable):
        return obj.json()
    elif isinstance(obj, set):
        # Set does not exist in JSON.
        # It's fine to use list instead, it becomes a Set when deserializing.
        return list(obj)


def from_dict_to_key_value_list(data: Dict[str, Any]) -> List[Any]:
    """Converts dict to flattened list of key, values where the value after the key"""
    parsed_list = []

    for k, v in data.items():
        parsed_list.append(k)
        parsed_list.append(v)

    return parsed_list
