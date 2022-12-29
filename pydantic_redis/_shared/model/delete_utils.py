"""Exposes shared utilities for deleting records from redis"""
from typing import Type, Union, List

from redis.client import Pipeline
from redis.asyncio.client import Pipeline as AioPipeline

from pydantic_redis._shared.model import AbstractModel
from pydantic_redis._shared.model.prop_utils import get_redis_key, get_model_index_key


def delete_on_pipeline(
    model: Type[AbstractModel], pipeline: Union[Pipeline, AioPipeline], ids: List[str]
):
    """Adds delete operations for the given ids to the redis pipeline.

    Args:
        model: the Model from which the given records are to be deleted.
        pipeline: the Redis pipeline on which the delete operations are
            to be added.
        ids: the list of primary keys of the records that are to be removed.

    Later when pipeline.execute is called later, the actual deletion occurs
    """
    primary_keys = []

    if isinstance(ids, list):
        primary_keys = ids
    elif ids is not None:
        primary_keys = [ids]

    names = [
        get_redis_key(model=model, primary_key_value=primary_key_value)
        for primary_key_value in primary_keys
    ]
    pipeline.delete(*names)
    # remove the primary keys from the indexz
    table_index_key = get_model_index_key(model=model)
    pipeline.zrem(table_index_key, *names)
