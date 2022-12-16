"""Module containing utils for getting properties of the Model"""

from typing import Type, Any

from .base import AbstractModel

NESTED_MODEL_PREFIX = "__"
NESTED_MODEL_LIST_FIELD_PREFIX = "___"
NESTED_MODEL_TUPLE_FIELD_PREFIX = "____"


def get_primary_key(model: Type[AbstractModel], primary_key_value: Any):
    """
    Returns the primary key value concatenated to the table name for uniqueness
    """
    return f"{get_table_prefix(model)}{primary_key_value}"


def get_table_prefix(model: Type[AbstractModel]):
    """
    Returns the prefix of the all the redis keys that are associated with this table
    """
    table_name = model.__name__.lower()
    return f"{table_name}_%&_"


def get_table_keys_regex(model: Type[AbstractModel]):
    """
    Returns the table name regex to get all keys that belong to this table
    """
    return f"{get_table_prefix(model)}*"


def get_table_index_key(model: Type[AbstractModel]):
    """Returns the key for the set in which the primary keys of the given table have been saved"""
    table_name = model.__name__.lower()
    return f"{table_name}__index"
