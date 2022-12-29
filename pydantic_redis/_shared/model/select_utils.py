"""Exposes utilities for selecting records from redis using lua scripts.

"""
from typing import List, Any, Type, Union, Awaitable, Optional

from pydantic_redis._shared.model.prop_utils import (
    NESTED_MODEL_PREFIX,
    NESTED_MODEL_LIST_FIELD_PREFIX,
    NESTED_MODEL_TUPLE_FIELD_PREFIX,
    get_redis_keys_regex,
    get_redis_key_prefix,
    get_model_index_key,
)


from .base import AbstractModel


def get_select_fields(model: Type[AbstractModel], columns: List[str]) -> List[str]:
    """Gets the fields to be used for selecting HMAP fields in Redis.

    It replaces any fields in `columns` that correspond to nested records with their
    `__` prefixed versions.

    Args:
        model: the model for which the fields for selecting are to be derived.
        columns: the fields that are to be transformed into fields for selecting.

    Returns:
        the fields for selecting, with nested fields being given appropriate prefixes.
    """
    fields = []
    nested_model_list_fields = model.get_nested_model_list_fields()
    nested_model_tuple_fields = model.get_nested_model_tuple_fields()
    nested_model_fields = model.get_nested_model_fields()

    for col in columns:

        if col in nested_model_fields:
            col = f"{NESTED_MODEL_PREFIX}{col}"
        elif col in nested_model_list_fields:
            col = f"{NESTED_MODEL_LIST_FIELD_PREFIX}{col}"
        elif col in nested_model_tuple_fields:
            col = f"{NESTED_MODEL_TUPLE_FIELD_PREFIX}{col}"

        fields.append(col)
    return fields


def select_all_fields_all_ids(
    model: Type[AbstractModel],
    skip: int = 0,
    limit: Optional[int] = None,
) -> Union[List[List[Any]], Awaitable[List[List[Any]]]]:
    """Retrieves all records of the given model in the redis database.

    Args:
        model: the Model whose records are to be retrieved.
        skip: the number of records to skip.
        limit: the maximum number of records to return. If None, limit is infinity.

    Returns:
        the list of records from redis, each record being a flattened list of key-values.
        In case we are using async, an Awaitable of that list is returned instead.
    """
    if isinstance(limit, int):
        return _select_all_ids_all_fields_paginated(model=model, limit=limit, skip=skip)
    else:
        table_keys_regex = get_redis_keys_regex(model=model)
        args = [table_keys_regex]
        store = model.get_store()
        return store.select_all_fields_for_all_ids_script(args=args)


def select_all_fields_some_ids(
    model: Type[AbstractModel], ids: List[str]
) -> Union[List[List[Any]], Awaitable[List[List[Any]]]]:
    """Retrieves some records from redis.

    Args:
        model: the Model whose records are to be retrieved.
        ids: the list of primary keys of the records to be retrieved.

    Returns:
        the list of records where each record is a flattened key-value list.
        In case we are using async, an Awaitable of that list is returned instead.
    """
    table_prefix = get_redis_key_prefix(model=model)
    keys = [f"{table_prefix}{key}" for key in ids]
    store = model.get_store()
    return store.select_all_fields_for_some_ids_script(keys=keys)


def select_some_fields_all_ids(
    model: Type[AbstractModel],
    fields: List[str],
    skip: int = 0,
    limit: Optional[int] = None,
) -> Union[List[List[Any]], Awaitable[List[List[Any]]]]:
    """Retrieves records of model from redis, each as with a subset of the fields.

    Args:
        model: the Model whose records are to be retrieved.
        fields: the subset of fields to return for each record.
        skip: the number of records to skip.
        limit: the maximum number of records to return. If None, limit is infinity.

    Returns:
        the list of records from redis, each record being a flattened list of key-values.
        In case we are using async, an Awaitable of that list is returned instead.
    """
    columns = get_select_fields(model=model, columns=fields)

    if isinstance(limit, int):
        return _select_some_fields_all_ids_paginated(
            model=model, columns=columns, limit=limit, skip=skip
        )
    else:
        table_keys_regex = get_redis_keys_regex(model=model)
        args = [table_keys_regex, *columns]
        store = model.get_store()
        return store.select_some_fields_for_all_ids_script(args=args)


def select_some_fields_some_ids(
    model: Type[AbstractModel], fields: List[str], ids: List[str]
) -> Union[List[List[Any]], Awaitable[List[List[Any]]]]:
    """Retrieves some records of current model from redis, each as with a subset of the fields.

    Args:
        model: the Model whose records are to be retrieved.
        fields: the subset of fields to return for each record.
        ids: the list of primary keys of the records to be retrieved.

    Returns:
        the list of records from redis, each record being a flattened list of key-values.
        In case we are using async, an Awaitable of that list is returned instead.
    """
    table_prefix = get_redis_key_prefix(model=model)
    keys = [f"{table_prefix}{key}" for key in ids]
    columns = get_select_fields(model=model, columns=fields)
    store = model.get_store()
    return store.select_some_fields_for_some_ids_script(keys=keys, args=columns)


def parse_select_response(
    model: Type[AbstractModel], response: List[List], as_models: bool
):
    """Casts a list of flattened key-value lists into a list of models or dicts.

    It replaces any foreign keys with the related model instances,
    and converts the list of flattened key-value lists into a list of models or dicts.
    e.g. [["foo", "bar", "head", 9]] => [{"foo": "bar", "head": 9}]

    Returns:
        If `as_models` is true, list of models else list of dicts
    """
    if len(response) == 0:
        return None

    if as_models:
        return [
            model(**model.deserialize_partially(record))
            for record in response
            if record != []
        ]

    return [model.deserialize_partially(record) for record in response if record != []]


def _select_all_ids_all_fields_paginated(
    model: Type[AbstractModel], limit: int, skip: Optional[int]
):
    """Retrieves a slice of all records of the given model in the redis database.

    Args:
        model: the Model whose records are to be retrieved.
        skip: the number of records to skip.
        limit: the maximum number of records to return. If None, limit is infinity.

    Returns:
        the list of records from redis, each record being a flattened list of key-values.
        In case we are using async, an Awaitable of that list is returned instead.
    """
    if skip is None:
        skip = 0
    table_index_key = get_model_index_key(model)
    args = [table_index_key, skip, limit]
    store = model.get_store()
    return store.paginated_select_all_fields_for_all_ids_script(args=args)


def _select_some_fields_all_ids_paginated(
    model: Type[AbstractModel], columns: List[str], limit: int, skip: int
):
    """Retrieves a slice of all records of model from redis, each as with a subset of the fields.

    Args:
        model: the Model whose records are to be retrieved.
        columns: the subset of fields to return for each record.
        skip: the number of records to skip.
        limit: the maximum number of records to return. If None, limit is infinity.

    Returns:
        the list of records from redis, each record being a flattened list of key-values.
        In case we are using async, an Awaitable of that list is returned instead.
    """
    if skip is None:
        skip = 0
    table_index_key = get_model_index_key(model)
    args = [table_index_key, skip, limit, *columns]
    store = model.get_store()
    return store.paginated_select_some_fields_for_all_ids_script(args=args)
