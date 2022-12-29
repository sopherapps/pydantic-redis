"""Exposes common utilities.

"""
import typing
from typing import Any, Tuple, Optional, Union, Dict, Callable, Type, List

import orjson


def strip_leading(word: str, substring: str) -> str:
    """Strips the leading substring if it exists.

    This is contrary to rstrip which removes each character in the substring

    Args:
        word: the string to strip from
        substring: the string to be stripped from the word.

    Returns:
        the stripped word
    """
    if word.startswith(substring):
        return word[len(substring) :]
    return word


def typing_get_args(v: Any) -> Tuple[Any, ...]:
    """Gets the __args__ of the annotations of a given typing.

    Args:
        v: the typing object whose __args__ are required.

    Returns:
        the __args__ of the item passed
    """
    try:
        return typing.get_args(v)
    except AttributeError:
        return getattr(v, "__args__", ()) if v is not typing.Generic else typing.Generic


def typing_get_origin(v: Any) -> Optional[Any]:
    """Gets the __origin__ of the annotations of a given typing.

    Args:
        v: the typing object whose __origin__ are required.

    Returns:
        the __origin__ of the item passed
    """
    try:
        return typing.get_origin(v)
    except AttributeError:
        return getattr(v, "__origin__", None)


def from_bytes_to_str(value: Union[str, bytes]) -> str:
    """Converts bytes to str.

    Args:
        value: the potentially bytes object to transform.

    Returns:
        the string value of the argument passed
    """
    if isinstance(value, bytes):
        return str(value, "utf-8")
    return value


def from_str_or_bytes_to_any(value: Any, field_type: Type) -> Any:
    """Converts str or bytes to arbitrary data.

    Converts the the `value` from a string or bytes to the `field_type`.

    Args:
        value: the string or bytes to be transformed to the `field_type`
        field_type: the type to which value is to be converted

    Returns:
        the `field_type` version of the `value`.
    """
    if isinstance(value, (bytes, bytearray, memoryview)):
        return orjson.loads(value)
    elif isinstance(value, str) and field_type != str:
        return orjson.loads(value)
    return value


def from_any_to_valid_redis_type(value: Any) -> Union[str, bytes, List[Any]]:
    """Converts arbitrary data into valid redis types

    Converts the the `value` from any type to a type that
    are acceptable by redis.
    By default, complex data is transformed to bytes.

    Args:
        value: the value to be transformed to a valid redis data type

    Returns:
        the transformed version of the `value`.
    """
    if isinstance(value, str):
        return value
    elif isinstance(value, set):
        return list(value)
    return orjson.dumps(value, default=default_json_dump)


def default_json_dump(obj: Any):
    """Serializes objects orjson cannot serialize.

    Args:
        obj: the object to serialize

    Returns:
        the bytes or string value of the object
    """
    if hasattr(obj, "json") and isinstance(obj.json, Callable):
        return obj.json()
    return obj


def from_dict_to_key_value_list(data: Dict[str, Any]) -> List[Any]:
    """Converts dict to flattened list of key, values.

    {"foo": "bar", "hen": "rooster"} becomes ["foo", "bar", "hen", "rooster"]
    When redis lua scripts are used, the value returned is a flattened list,
    similar to that shown above.

    Args:
        data: the dictionary to flatten

    Returns:
        the flattened list version of `data`
    """
    parsed_list = []

    for k, v in data.items():
        parsed_list.append(k)
        parsed_list.append(v)

    return parsed_list
