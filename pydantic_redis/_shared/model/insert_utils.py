"""Exposes the utility functions for inserting records into redis.

"""

from datetime import datetime
from typing import Union, Optional, Any, Dict, Type

from redis.asyncio.client import Pipeline as AioPipeline
from redis.client import Pipeline

from .prop_utils import (
    get_redis_key,
    get_model_index_key,
)

from .base import (
    AbstractModel,
    NestingType,
    AggTypeTree,
    NESTED_MODEL_LIST_FIELD_PREFIX,
)


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
    after their insert operations have been added to the pipeline.

    A few cleanups it does include:
      - Upserting any nested records in `record`
      - Replacing the keys of nested records with their NESTED_MODEL_PREFIX prefixed versions
        e.g. `__author` instead of author
      - Replacing the keys of lists of nested records with their NESTED_MODEL_LIST_FIELD_PREFIX prefixed versions
        e.g. `___author` instead of author
      - Replacing the keys of tuples of nested records with their NESTED_MODEL_TUPLE_FIELD_PREFIX prefixed versions
        e.g. `____author` instead of author
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
    field_type_trees = model.get_field_type_trees()
    field_typed_keys = model.get_field_typed_keys()

    new_data = {}
    for k, v in data:
        type_tree = field_type_trees.get(k)
        key = field_typed_keys.get(k, k)
        new_data[key] = _serialize_by_type_tree(
            value=v, type_tree=type_tree, pipeline=pipeline, life_span=life_span
        )

    return new_data


def _serialize_by_type_tree(
    value: Any,
    type_tree: Optional[AggTypeTree],
    pipeline: Union[Pipeline, AioPipeline],
    life_span: Optional[Union[float, int]],
) -> Any:
    """Transforms a given value into a value basing on the tree of its aggregate type

    Nested models are inserted into the redis database and their positions in the data
    replaced by their primary keys

    Args:
        value: the value to be serialized basing on the type tree
        type_tree: the tree representing the nested hierarchy of types for the aggregate
            type that the value is to be cast into
        pipeline: the redis pipeline on which the redis operations are to be done.
        life_span: the time-to-live in seconds for the given record.

    Returns:
        the serialized value
    """
    if type_tree is None:
        # return the value as is because it cannot be serialized
        return value

    nesting_type, type_args = type_tree

    if nesting_type is NestingType.ON_ROOT:
        return insert_on_pipeline(
            model=value.__class__,
            _id=None,
            pipeline=pipeline,
            record=value,
            life_span=life_span,
        )

    if nesting_type is NestingType.IN_LIST:
        _type = type_args[0]
        return [
            _serialize_by_type_tree(
                value=item, type_tree=_type, pipeline=pipeline, life_span=life_span
            )
            for item in value
        ]

    if nesting_type is NestingType.IN_TUPLE:
        return tuple(
            [
                _serialize_by_type_tree(
                    value=item, type_tree=_type, pipeline=pipeline, life_span=life_span
                )
                for _type, item in zip(type_args, value)
            ]
        )

    if nesting_type is NestingType.IN_DICT:
        _, value_type = type_args
        return {
            k: _serialize_by_type_tree(
                value=v, type_tree=value_type, pipeline=pipeline, life_span=life_span
            )
            for k, v in value.items()
        }

    if nesting_type is NestingType.IN_UNION:
        # the value can be any of the types in type_args
        for _type in type_args:
            try:
                serialized_value = _serialize_by_type_tree(
                    value=value, type_tree=_type, pipeline=pipeline, life_span=life_span
                )
                # return the first successfully serialized value
                # that is not equal to the original value
                if serialized_value != value:
                    return serialized_value
            except Exception:
                pass

    # return the value without any serializing
    return value
