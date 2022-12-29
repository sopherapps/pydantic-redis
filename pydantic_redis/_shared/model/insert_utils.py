"""Exposes the utility functions for inserting records into redis.

"""
from datetime import datetime
from typing import Union, Optional, Any, Dict, Tuple, List, Type

from redis.asyncio.client import Pipeline as AioPipeline
from redis.client import Pipeline

from .prop_utils import (
    get_redis_key,
    get_model_index_key,
    NESTED_MODEL_PREFIX,
    NESTED_MODEL_LIST_FIELD_PREFIX,
    NESTED_MODEL_TUPLE_FIELD_PREFIX,
)

from .base import AbstractModel


def insert_on_pipeline(
    model: Type[AbstractModel],
    pipeline: Union[Pipeline, AioPipeline],
    _id: Optional[Any],
    record: Union[AbstractModel, Dict[str, Any]],
    life_span: Optional[Union[float, int]] = None,
) -> Any:
    """Add an insert operation to the redis pipeline.

    Later when the pipeline.execute is called, the actual inserts occur.
    This reduces the number of network requests to the redis server thus
    improving performance.

    Args:
        model: the Model whose records are to be inserted into redis.
        pipeline: the Redis pipeline on which the insert operation
            is to be added.
        _id: the primary key of the record to be inserted in redis.
            It is None when inserting, and some value when updating.
        record: the model instance or dictionary to be inserted into redis.
        life_span: the time-to-live in seconds for the record to be inserted.
            (default: None)

    Returns:
        the primary key of the record that is to be inserted.
    """
    key = _id if _id is not None else getattr(record, model.get_primary_key_field())
    data = _serialize_nested_models(
        model=model, pipeline=pipeline, record=record, life_span=life_span
    )
    name = get_redis_key(model=model, primary_key_value=key)
    mapping = model.serialize_partially(data)
    pipeline.hset(name=name, mapping=mapping)

    if life_span is not None:
        pipeline.expire(name=name, time=life_span)
    # save the primary key in an index: a sorted set, whose score is current timestamp
    table_index_key = get_model_index_key(model)
    timestamp = datetime.utcnow().timestamp()
    pipeline.zadd(table_index_key, {name: timestamp})
    if life_span is not None:
        pipeline.expire(table_index_key, time=life_span)

    return name


def _serialize_nested_models(
    model: Type[AbstractModel],
    pipeline: Union[Pipeline, AioPipeline],
    record: Union[AbstractModel, Dict[str, Any]],
    life_span: Optional[Union[float, int]] = None,
) -> Dict[str, Any]:
    """Converts nested models into their primary keys.

    In order to make the record serializable, all nested models including those in
    lists and tuples of nested models are converted to their primary keys,
    after being their insert operations have been added to the pipeline.

    A few cleanups it does include:
      - Upserting any nested records in `record`
      - Replacing the keys of nested records with their NESTED_MODEL_PREFIX prefixed versions
        e.g. `__author` instead of author
      - Replacing the keys of lists of nested records with their NESTED_MODEL_LIST_FIELD_PREFIX prefixed versions
        e.g. `__%&l_author` instead of author
      - Replacing the keys of tuples of nested records with their NESTED_MODEL_TUPLE_FIELD_PREFIX prefixed versions
        e.g. `__%&l_author` instead of author
      - Replacing the values of nested records with their foreign keys

    Args:
        model: the model the given record belongs to.
        pipeline: the redis pipeline on which the redis operations are to be done.
        record: the model or dictionary whose nested models are to be serialized.
        life_span: the time-to-live in seconds for the given record (default: None).

    Returns:
        the partially serialized dict that has no nested models
    """
    data = record.items() if isinstance(record, dict) else record
    new_data = {}

    nested_model_list_fields = model.get_nested_model_list_fields()
    nested_model_tuple_fields = model.get_nested_model_tuple_fields()
    nested_model_fields = model.get_nested_model_fields()

    for k, v in data:
        key, value = k, v

        if key in nested_model_list_fields:
            key, value = _serialize_list(
                key=key, value=value, pipeline=pipeline, life_span=life_span
            )
        elif key in nested_model_tuple_fields:
            key, value = _serialize_tuple(
                key=key,
                value=value,
                pipeline=pipeline,
                life_span=life_span,
                tuple_fields=nested_model_tuple_fields,
            )
        elif key in nested_model_fields:
            key, value = _serialize_model(
                key=key, value=value, pipeline=pipeline, life_span=life_span
            )

        new_data[key] = value
    return new_data


def _serialize_tuple(
    key: str,
    value: Tuple[AbstractModel],
    pipeline: Union[Pipeline, AioPipeline],
    life_span: Optional[Union[float, int]],
    tuple_fields: Dict[str, Tuple[Any, ...]],
) -> Tuple[str, List[Any]]:
    """Replaces models in a tuple with strings.

    It adds insert operations for the records in the tuple onto the pipeline
    and returns the tuple with the models replaced by their primary keys as value.

    Returns:
        key: the original `key` prefixed with NESTED_MODEL_TUPLE_FIELD_PREFIX
        value: tthe tuple with the models replaced by their primary keys
    """
    try:
        field_types = tuple_fields.get(key, ())
        value = [
            insert_on_pipeline(
                model=field_type,
                _id=None,
                pipeline=pipeline,
                record=item,
                life_span=life_span,
            )
            if issubclass(field_type, AbstractModel)
            else item
            for field_type, item in zip(field_types, value)
        ]
        key = f"{NESTED_MODEL_TUPLE_FIELD_PREFIX}{key}"
    except TypeError:
        # In case the value is None, just ignore
        pass

    return key, value


def _serialize_list(
    key: str,
    value: List[AbstractModel],
    pipeline: Union[Pipeline, AioPipeline],
    life_span: Optional[Union[float, int]],
) -> Tuple[str, List[Any]]:
    """Casts a list of models into a list of strings

    It adds insert operations for the records in the list onto the pipeline
    and returns a list of their primary keys as value.

    Returns:
        key: the original `key` prefixed with NESTED_MODEL_LIST_FIELD_PREFIX
        value: the list of primary keys of the records to be inserted
    """
    try:
        value = [
            insert_on_pipeline(
                model=item.__class__,
                _id=None,
                pipeline=pipeline,
                record=item,
                life_span=life_span,
            )
            for item in value
        ]
        key = f"{NESTED_MODEL_LIST_FIELD_PREFIX}{key}"
    except TypeError:
        # In case the value is None, just ignore
        pass

    return key, value


def _serialize_model(
    key: str,
    value: AbstractModel,
    pipeline: Union[Pipeline, AioPipeline],
    life_span: Optional[Union[float, int]],
) -> Tuple[str, str]:
    """Casts a model into a string

    It adds an insert operation for the given model onto the pipeline
    and returns its primary key as value.

    Returns:
        key: the original `key` prefixed with NESTED_MODEL_PREFIX
        value: the primary key of the model
    """
    try:
        value = insert_on_pipeline(
            model=value.__class__,
            _id=None,
            pipeline=pipeline,
            record=value,
            life_span=life_span,
        )
        key = f"{NESTED_MODEL_PREFIX}{key}"
    except TypeError:
        # In case the value is None, just ignore
        pass

    return key, value
