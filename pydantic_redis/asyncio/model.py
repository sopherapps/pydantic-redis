"""Module containing the model classes"""
from typing import Optional, List, Any, Union, Dict, Tuple, Type

import redis.asyncio

from pydantic_redis.shared.model import AbstractModel
from pydantic_redis.shared.model.insert_utils import insert_on_pipeline
from pydantic_redis.shared.model.prop_utils import get_primary_key, get_table_index_key
from pydantic_redis.shared.model.select_utils import (
    select_all_fields_all_ids,
    select_all_fields_some_ids,
    select_some_fields_all_ids,
    select_some_fields_some_ids,
    parse_select_response,
)

from .store import Store


class Model(AbstractModel):
    """
    The section in the store that saves rows of the same kind
    """

    _store: Store

    @classmethod
    async def insert(
        cls,
        data: Union[List[AbstractModel], AbstractModel],
        life_span_seconds: Optional[float] = None,
    ):
        """
        Inserts a given row or sets of rows into the table
        """
        store = cls.get_store()
        life_span = (
            life_span_seconds
            if life_span_seconds is not None
            else store.life_span_in_seconds
        )

        async with store.redis_store.pipeline(transaction=True) as pipeline:
            data_list = []

            if isinstance(data, list):
                data_list = data
            elif isinstance(data, AbstractModel):
                data_list = [data]

            for record in data_list:
                insert_on_pipeline(
                    model=cls,
                    _id=None,
                    pipeline=pipeline,
                    record=record,
                    life_span=life_span,
                )

            return await pipeline.execute()

    @classmethod
    async def update(
        cls, _id: Any, data: Dict[str, Any], life_span_seconds: Optional[float] = None
    ):
        """
        Updates a given row or sets of rows in the table
        """
        store = cls.get_store()
        life_span = (
            life_span_seconds
            if life_span_seconds is not None
            else store.life_span_in_seconds
        )
        async with store.redis_store.pipeline(transaction=True) as pipeline:
            if isinstance(data, dict):
                insert_on_pipeline(
                    model=cls,
                    _id=_id,
                    pipeline=pipeline,
                    record=data,
                    life_span=life_span,
                )

            return await pipeline.execute()

    @classmethod
    async def delete(cls, ids: Union[Any, List[Any]]):
        """
        deletes a given row or sets of rows in the table
        """
        store = cls.get_store()

        async with store.redis_store.pipeline() as pipeline:
            primary_keys = []

            if isinstance(ids, list):
                primary_keys = ids
            elif ids is not None:
                primary_keys = [ids]

            names = [
                get_primary_key(model=cls, primary_key_value=primary_key_value)
                for primary_key_value in primary_keys
            ]
            pipeline.delete(*names)
            # remove the primary keys from the index
            table_index_key = get_table_index_key(model=cls)
            pipeline.srem(table_index_key, *names)
            return await pipeline.execute()

    @classmethod
    async def select(
        cls,
        columns: Optional[List[str]] = None,
        ids: Optional[List[Any]] = None,
        **kwargs,
    ):
        """
        Selects given rows or sets of rows in the table
        """
        if columns is None and ids is None:
            response = await select_all_fields_all_ids(model=cls)

        elif columns is None and isinstance(ids, list):
            response = await select_all_fields_some_ids(model=cls, ids=ids)

        elif isinstance(columns, list) and ids is None:
            response = await select_some_fields_all_ids(model=cls, fields=columns)

        elif isinstance(columns, list) and isinstance(ids, list):
            response = await select_some_fields_some_ids(
                model=cls, fields=columns, ids=ids
            )

        else:
            raise ValueError(
                f"columns {columns}, ids: {ids} should be either None or lists"
            )

        return parse_select_response(
            model=cls, response=response, as_models=(columns is None)
        )
