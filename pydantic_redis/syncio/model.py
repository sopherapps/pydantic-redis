"""Module containing the model classes"""
from typing import Optional, List, Any, Union, Dict

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
from ..shared.model.delete_utils import delete_on_pipeline


class Model(AbstractModel):
    """
    The section in the store that saves rows of the same kind
    """

    _store: Store

    @classmethod
    def insert(
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
        with store.redis_store.pipeline(transaction=True) as pipeline:
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

            return pipeline.execute()

    @classmethod
    def update(
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
        with store.redis_store.pipeline(transaction=True) as pipeline:
            if isinstance(data, dict):
                insert_on_pipeline(
                    model=cls,
                    _id=_id,
                    pipeline=pipeline,
                    record=data,
                    life_span=life_span,
                )

            return pipeline.execute()

    @classmethod
    def delete(cls, ids: Union[Any, List[Any]]):
        """
        deletes a given row or sets of rows in the table
        """
        store = cls.get_store()
        with store.redis_store.pipeline() as pipeline:
            delete_on_pipeline(model=cls, pipeline=pipeline, ids=ids)
            return pipeline.execute()

    @classmethod
    def select(
        cls,
        columns: Optional[List[str]] = None,
        ids: Optional[List[Any]] = None,
        skip: int = 0,
        limit: Optional[int] = None,
        **kwargs,
    ):
        """
        Selects given rows or sets of rows in the table

        However, if `limit` is set, the number of items
        returned will be less or equal to `limit`.
        `skip` defaults to 0. It is the number of items to skip.
        `skip` is only relevant when limit is specified.

        `skip` and `limit` are irrelevant when `ids` are provided.
        """
        if columns is None and ids is None:
            response = select_all_fields_all_ids(model=cls, skip=skip, limit=limit)

        elif columns is None and isinstance(ids, list):
            response = select_all_fields_some_ids(model=cls, ids=ids)

        elif isinstance(columns, list) and ids is None:
            response = select_some_fields_all_ids(
                model=cls, fields=columns, skip=skip, limit=limit
            )

        elif isinstance(columns, list) and isinstance(ids, list):
            response = select_some_fields_some_ids(model=cls, fields=columns, ids=ids)

        else:
            raise ValueError(
                f"columns {columns}, ids: {ids} should be either None or lists"
            )

        return parse_select_response(
            model=cls, response=response, as_models=(columns is None)
        )
