"""Module containing the mixin functionality for selecting"""
from typing import List, Any, Type, Union, Awaitable, Optional

from pydantic_redis.shared.model.prop_utils import (
    NESTED_MODEL_PREFIX,
    NESTED_MODEL_LIST_FIELD_PREFIX,
    NESTED_MODEL_TUPLE_FIELD_PREFIX,
    get_table_keys_regex,
    get_table_prefix,
    get_table_index_key,
)


from .base import AbstractModel


def get_select_fields(model: Type[AbstractModel], columns: List[str]) -> List[str]:
    """
    Gets the fields to be used for selecting HMAP fields in Redis
    It replaces any fields in `columns` that correspond to nested records with their
    `__` suffixed versions
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
    """
    Selects all items in the database, returning all their fields

    However, if `limit` is set, the number of items
    returned will be less or equal to `limit`.
    `skip` defaults to 0. It is the number of items to skip.
    `skip` is only relevant when limit is specified.
    """
    if isinstance(limit, int):
        return _select_all_ids_all_fields_paginated(model=model, limit=limit, skip=skip)
    else:
        table_keys_regex = get_table_keys_regex(model=model)
        args = [table_keys_regex]
        store = model.get_store()
        return store.select_all_fields_for_all_ids_script(args=args)


def select_all_fields_some_ids(
    model: Type[AbstractModel], ids: List[str]
) -> Union[List[List[Any]], Awaitable[List[List[Any]]]]:
    """Selects some items in the database, returning all their fields"""
    table_prefix = get_table_prefix(model=model)
    keys = [f"{table_prefix}{key}" for key in ids]
    store = model.get_store()
    return store.select_all_fields_for_some_ids_script(keys=keys)


def select_some_fields_all_ids(
    model: Type[AbstractModel],
    fields: List[str],
    skip: int = 0,
    limit: Optional[int] = None,
) -> Union[List[List[Any]], Awaitable[List[List[Any]]]]:
    """
    Selects all items in the database, returning only the specified fields.

    However, if `limit` is set, the number of items
    returned will be less or equal to `limit`.
    `skip` defaults to 0. It is the number of items to skip.
    `skip` is only relevant when limit is specified.
    """
    columns = get_select_fields(model=model, columns=fields)

    if isinstance(limit, int):
        return _select_some_fields_all_ids_paginated(
            model=model, columns=columns, limit=limit, skip=skip
        )
    else:
        table_keys_regex = get_table_keys_regex(model=model)
        args = [table_keys_regex, *columns]
        store = model.get_store()
        return store.select_some_fields_for_all_ids_script(args=args)


def select_some_fields_some_ids(
    model: Type[AbstractModel], fields: List[str], ids: List[str]
) -> Union[List[List[Any]], Awaitable[List[List[Any]]]]:
    """Selects some of items in the database, returning only the specified fields"""
    table_prefix = get_table_prefix(model=model)
    keys = [f"{table_prefix}{key}" for key in ids]
    columns = get_select_fields(model=model, columns=fields)
    store = model.get_store()
    return store.select_some_fields_for_some_ids_script(keys=keys, args=columns)


def parse_select_response(
    model: Type[AbstractModel], response: List[List], as_models: bool
):
    """
    Converts a list of lists of key-values into a list of models if `as_models` is true or leaves them as dicts
    with foreign keys replaced by model instances. The list is got from calling EVAL on Redis .

    EVAL returns a List of Lists of key, values where the value for a given key is in the position
    just after the key e.g. [["foo", "bar", "head", 9]] => [{"foo": "bar", "head": 9}]
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
    """Selects all fields for at most `limit` number of items after skipping `skip` items"""
    if skip is None:
        skip = 0
    table_index_key = get_table_index_key(model)
    args = [table_index_key, skip, limit]
    store = model.get_store()
    return store.paginated_select_all_fields_for_all_ids_script(args=args)


def _select_some_fields_all_ids_paginated(
    model: Type[AbstractModel], columns: List[str], limit: int, skip: int
):
    """Selects some fields for at most `limit` number of items after skipping `skip` items"""
    if skip is None:
        skip = 0
    table_index_key = get_table_index_key(model)
    args = [table_index_key, skip, limit, *columns]
    store = model.get_store()
    return store.paginated_select_some_fields_for_all_ids_script(args=args)
