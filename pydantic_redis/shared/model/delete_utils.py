"""Module containing common functionality for deleting records"""
from typing import Type, Union, List

from redis.client import Pipeline
from redis.asyncio.client import Pipeline as AioPipeline

from pydantic_redis.shared.model import AbstractModel
from pydantic_redis.shared.model.prop_utils import get_primary_key, get_table_index_key


def delete_on_pipeline(
    model: Type[AbstractModel], pipeline: Union[Pipeline, AioPipeline], ids: List[str]
):
    """
    Pipelines the deletion of the given ids, so that when pipeline.execute
    is called later, deletion occurs
    """
    primary_keys = []

    if isinstance(ids, list):
        primary_keys = ids
    elif ids is not None:
        primary_keys = [ids]

    names = [
        get_primary_key(model=model, primary_key_value=primary_key_value)
        for primary_key_value in primary_keys
    ]
    pipeline.delete(*names)
    # remove the primary keys from the indexz
    table_index_key = get_table_index_key(model=model)
    pipeline.zrem(table_index_key, *names)
