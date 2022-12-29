"""Exposes the Base `Model` class for creating custom asynchronous models.

This module contains the `Model` class which should be inherited when
creating model's for use in the asynchronous API of pydantic-redis.
"""
from typing import Optional, List, Any, Union, Dict

from .._shared.model import AbstractModel
from .._shared.model.insert_utils import insert_on_pipeline
from .._shared.model.select_utils import (
    select_all_fields_all_ids,
    select_all_fields_some_ids,
    select_some_fields_all_ids,
    select_some_fields_some_ids,
    parse_select_response,
)

from .store import Store
from .._shared.model.delete_utils import delete_on_pipeline


class Model(AbstractModel):
    """The Base class for all Asynchronous models.

    Inherit this class when creating a new model.
    The new model should have `_primary_key_field` defined.
    Any interaction with redis is done through `Model`'s.
    """

    _store: Store

    @classmethod
    async def insert(
        cls,
        data: Union[List[AbstractModel], AbstractModel],
        life_span_seconds: Optional[float] = None,
    ):
        """Inserts a given record or list of records into the redis.

        Can add a single record or multiple records into redis.
        The records must be instances of this class. i.e. a `Book`
        model can only insert `Book` instances.

        Args:
            data: a model instance or list of model instances to put
                into the redis store
            life_span_seconds: the time-to-live in seconds of the records
                to be inserted. If not specified, it defaults to the `Store`'s
                life_span_seconds.
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
        """Updates the record whose primary key is `_id`.

        Updates the record of this Model in redis whose primary key is equal to the `_id` provided.
        The record is partially updated from the `data`.
        If `life_span_seconds` is provided, it will also update the time-to-live of
        the record.

        Args:
            _id: the primary key of record to be updated.
            data: the new changes
            life_span_seconds: the new time-to-live for the record
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
        """Removes a list of this Model's records from redis

        Removes all the records for the current Model whose primary keys
        have been included in the `ids` passed.

        Args:
            ids: list of primary keys of the records to remove
        """
        store = cls.get_store()

        async with store.redis_store.pipeline() as pipeline:
            delete_on_pipeline(model=cls, pipeline=pipeline, ids=ids)
            return await pipeline.execute()

    @classmethod
    async def select(
        cls,
        columns: Optional[List[str]] = None,
        ids: Optional[List[Any]] = None,
        skip: int = 0,
        limit: Optional[int] = None,
        **kwargs,
    ) -> Union["Model", Dict[str, Any]]:
        """etrieves records of this Model from redis.

        Retrieves the records for this Model from redis.

        Args:
            columns: the fields to return for each record
            ids: the primary keys of the records to returns
            skip: the number of records to skip. (default: 0)
            limit: the maximum number of records to return

        Returns:
            By default, it returns all records that belong to current Model.

            If `ids` are specified, it returns only records whose primary keys
            have been listed in `ids`.

            If `skip` and `limit` are specified WITHOUT `ids`, a slice of
            all records are returned.

            If `limit` and `ids` are specified, `limit` is ignored.

            If `columns` are specified, a list of dictionaries containing only
            the fields specified in `columns` is returned. Otherwise, instances
            of the current Model are returned.
        """
        if columns is None and ids is None:
            response = await select_all_fields_all_ids(
                model=cls, skip=skip, limit=limit
            )

        elif columns is None and isinstance(ids, list):
            response = await select_all_fields_some_ids(model=cls, ids=ids)

        elif isinstance(columns, list) and ids is None:
            response = await select_some_fields_all_ids(
                model=cls, fields=columns, skip=skip, limit=limit
            )

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
