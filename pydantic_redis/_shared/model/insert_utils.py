"""Module containing the mixin for insert functionality in model"""
from datetime import datetime
from typing import Union, Optional, Any, Dict, Tuple, List, Type

from redis.asyncio.client import Pipeline as AioPipeline
from redis.client import Pipeline

from .prop_utils import (
    get_primary_key,
    get_table_index_key,
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
    """
    Creates insert commands for the given record on the given pipeline but does not execute
    thus the data is not yet persisted in redis
    Returns the key of the created item
    """
    key = _id if _id is not None else getattr(record, model.get_primary_key_field())
    data = _get_serializable_dict(
        model=model, pipeline=pipeline, record=record, life_span=life_span
    )
    name = get_primary_key(model=model, primary_key_value=key)
    mapping = model.serialize_partially(data)
    pipeline.hset(name=name, mapping=mapping)

    if life_span is not None:
        pipeline.expire(name=name, time=life_span)
    # save the primary key in an index: a sorted set, whose score is current timestamp
    table_index_key = get_table_index_key(model)
    timestamp = datetime.utcnow().timestamp()
    pipeline.zadd(table_index_key, {name: timestamp})
    if life_span is not None:
        pipeline.expire(table_index_key, time=life_span)

    return name


def _get_serializable_dict(
    model: Type[AbstractModel],
    pipeline: Union[Pipeline, AioPipeline],
    record: Union[AbstractModel, Dict[str, Any]],
    life_span: Optional[Union[float, int]] = None,
) -> Dict[str, Any]:
    """
    Returns a dictionary that can be serialized.
    A few cleanups it does include:
      - Upserting any nested records in `record`
      - Replacing the keys of nested records with their NESTED_MODEL_PREFIX suffixed versions
        e.g. `__author` instead of author
      - Replacing the keys of lists of nested records with their NESTED_MODEL_LIST_FIELD_PREFIX suffixed versions
        e.g. `__%&l_author` instead of author
      - Replacing the keys of tuples of nested records with their NESTED_MODEL_TUPLE_FIELD_PREFIX suffixed versions
        e.g. `__%&l_author` instead of author
      - Replacing the values of nested records with their foreign keys
    """
    data = record.items() if isinstance(record, dict) else record
    new_data = {}

    nested_model_list_fields = model.get_nested_model_list_fields()
    nested_model_tuple_fields = model.get_nested_model_tuple_fields()
    nested_model_fields = model.get_nested_model_fields()

    for k, v in data:
        key, value = k, v

        if key in nested_model_list_fields:
            key, value = _serialize_nested_model_list_field(
                key=key, value=value, pipeline=pipeline, life_span=life_span
            )
        elif key in nested_model_tuple_fields:
            key, value = _serialize_nested_model_tuple_field(
                key=key,
                value=value,
                pipeline=pipeline,
                life_span=life_span,
                tuple_fields=nested_model_tuple_fields,
            )
        elif key in nested_model_fields:
            key, value = _serialize_nested_model_field(
                key=key, value=value, pipeline=pipeline, life_span=life_span
            )

        new_data[key] = value
    return new_data


def _serialize_nested_model_tuple_field(
    key: str,
    value: Tuple[AbstractModel],
    pipeline: Union[Pipeline, AioPipeline],
    life_span: Optional[Union[float, int]],
    tuple_fields: Dict[str, Tuple[Any, ...]],
) -> Tuple[str, List[Any]]:
    """Serializes a key-value pair for a field that has a tuple of nested models"""
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


def _serialize_nested_model_list_field(
    key: str,
    value: List[AbstractModel],
    pipeline: Union[Pipeline, AioPipeline],
    life_span: Optional[Union[float, int]],
) -> Tuple[str, List[Any]]:
    """Serializes a key-value pair for a field that has a list of nested models"""
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


def _serialize_nested_model_field(
    key: str,
    value: AbstractModel,
    pipeline: Union[Pipeline, AioPipeline],
    life_span: Optional[Union[float, int]],
) -> Tuple[str, str]:
    """Serializes a key-value pair for a field that has a nested model"""
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
