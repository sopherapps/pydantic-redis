"""Exposes utils for getting properties of the Model

Attributes:
    NESTED_MODEL_PREFIX (str): the prefix for fields with single nested models
    NESTED_MODEL_LIST_FIELD_PREFIX (str): the prefix for fields with lists of nested models
    NESTED_MODEL_TUPLE_FIELD_PREFIX (str): the prefix for fields with tuples of nested models
"""

from typing import Type, Any

from .base import AbstractModel

NESTED_MODEL_PREFIX = "__"
NESTED_MODEL_LIST_FIELD_PREFIX = "___"
NESTED_MODEL_TUPLE_FIELD_PREFIX = "____"


def get_redis_key(model: Type[AbstractModel], primary_key_value: Any):
    """Gets the key used internally in redis for the `primary_key_value` of `model`.

    Args:
        model: the model for which the key is to be generated
        primary_key_value: the external facing primary key value

    Returns:
        the primary key internally used for `primary_key_value` of `model`
    """
    return f"{get_redis_key_prefix(model)}{primary_key_value}"


def get_redis_key_prefix(model: Type[AbstractModel]):
    """Gets the prefix for keys used internally in redis for records of `model`.

    Args:
        model: the model for which the redis key prefix is to be generated

    Returns:
        the prefix of the all the redis keys that are associated with this model
    """
    model_name = model.__name__.lower()
    return f"{model_name}_%&_"


def get_redis_keys_regex(model: Type[AbstractModel]):
    """Gets the regex for all keys of records of `model` used internally in redis.

    Args:
        model: the model for which the redis key regex is to be generated

    Returns:
        the regular expression for all keys of records of `model` used internally in redis
    """
    return f"{get_redis_key_prefix(model)}*"


def get_model_index_key(model: Type[AbstractModel]):
    """Gets the key for the index set of `model` used internally in redis.

    The index for each given model stores the primary keys for all records
    that belong to the given model.

    Args:
        model: the model whose index is wanted.

    Returns:
        the the key for the index set of `model` used internally in redis.
    """
    table_name = model.__name__.lower()
    return f"{table_name}__index"
